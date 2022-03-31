# coding=UTF-8
"""Functions for creating and finite element meshes from geometry_primitives."""
import os
import tempfile
from pathlib import Path
from subprocess import Popen, PIPE

import dolfin as df
import meshio
import numpy as np
from dolfin.cpp.mesh import MeshFunctionSizet
from meshio import Mesh

from fish2eod.geometry.primitives import Circle, Polygon
from fish2eod.mesh.model_geometry import ModelGeometry

GMSH_PATH = None
if os.environ.get("READTHEDOCS"):
    GMSH_PATH = Path(__file__).parent / "../../docs/source/gmsh"


class Mesher:
    def __init__(self):
        self.point_count = 1
        self.line_count = 1
        self.surface_count = 1
        self.loop_count = 1

        self.instructions = ["//+", 'SetFactory("OpenCASCADE");']

        self.all_surfaces = []

    def add_circle(self, circle: Circle):
        center_x, center_y = circle.center
        r = circle.radius

        lcar = f", {circle.lcar}" if circle.lcar else ""

        new_points = []

        # steal this trick from pygmsh to put 3 pts on the outside and make 3 120d arcs
        edge_points = [
            [center_x + r, center_y],
            [center_x, center_y],
            [center_x + r * np.cos(2 * np.pi / 3), center_y + r * np.sin(2 * np.pi / 3)],
            [center_x + r * np.cos(4 * np.pi / 3), center_y + r * np.sin(4 * np.pi / 3)],
        ]
        # right, center, left, bottom, top
        for x, y in edge_points:
            self.instructions += [f"Point({self.point_count}) = {{ {x}, {y}, {0} {lcar} }};"]
            new_points.append(self.point_count)
            self.point_count += 1

        self.new_lines = []
        self.instructions += [f"Circle({self.line_count}) = {{ {new_points[0]}, {new_points[1]}, {new_points[2]} }};"]
        self.new_lines.append(self.line_count)
        self.line_count += 1

        self.instructions += [f"Circle({self.line_count}) = {{ {new_points[2]}, {new_points[1]}, {new_points[3]} }};"]
        self.new_lines.append(self.line_count)
        self.line_count += 1

        self.instructions += [f"Circle({self.line_count}) = {{ {new_points[3]}, {new_points[1]}, {new_points[0]} }};"]
        self.new_lines.append(self.line_count)
        self.line_count += 1

        new_loop = self.add_line_loop(*self.new_lines)
        self.add_surface(new_loop)

    def add_line(self, p1: int, p2: int):
        self.instructions += [f"Line({self.line_count}) = {{ {p1}, {p2} }};"]
        new_name = self.line_count
        self.line_count += 1
        return new_name

    def add_line_loop(self, *lines: int):
        self.instructions += [f'Line Loop({self.surface_count}) = {{ {", ".join(str(x) for x in lines)}}};']
        new_name = self.surface_count
        return new_name  # dont increment suface just yet

    def add_surface(self, loop: int):
        self.instructions += [f"Plane Surface({self.surface_count}) = {{ {loop} }};"]
        new_name = f"Surface{{{self.surface_count}}}"
        self.all_surfaces.append(new_name)
        self.surface_count += 1

    def add_polygon(self, poly: Polygon):
        new_points = []
        lcar = f", {poly.lcar}" if poly.lcar else ""

        for x, y, z in poly.mesh_representation:
            self.instructions += [f"Point({self.point_count}) = {{ {x}, {y}, {z} {lcar} }};"]
            new_points.append(self.point_count)
            self.point_count += 1

        new_lines = []
        for p1, p2 in zip(new_points[:-1], new_points[1:]):
            new_lines.append(self.add_line(p1, p2))
        new_lines.append(self.add_line(new_points[-1], new_points[0]))  # make close

        new_loop = self.add_line_loop(*new_lines)
        self.add_surface(new_loop)

    def write(self, file_handle):
        if len(self.all_surfaces) > 1:
            objects = "; ".join(self.all_surfaces[1:]) + "; Delete;"
            tool = f"{self.all_surfaces[0]}; Delete;"

            self.instructions += [f"BooleanFragments{{ {objects} }}{{ {tool} }}"]

        file_handle.write("\n".join(self.instructions))
        file_handle.flush()

    def make_mesh(self) -> Mesh:
        with tempfile.NamedTemporaryFile("w", suffix=".geo") as f:
            self.write(f)

            msh_file = f"{f.name[:-4]}.msh"

            pipe = Popen(["gmsh", f.name, "-2", "-format", "msh", "-bin", "-o", msh_file], stdout=PIPE)
            pipe.communicate()
            assert pipe.returncode == 0

            return meshio.read(msh_file)


def create_mesh(model_geometry: ModelGeometry, verbose: bool = True) -> df.Mesh:
    """Create the mesh from the model geometry.

    :param model_geometry: The model geometry to mesh
    :param verbose: Should gmsh output be printed
    :return: The computed mesh
    """
    mesh_geometry = Mesher()
    # add each object to the mesh geometry
    [mesh_add(obj, mesh_geometry) for (_, obj) in model_geometry]

    created_mesh = mesh_geometry.make_mesh()
    created_mesh.remove_lower_dimensional_cells()
    assert created_mesh.cells[-1].type == "triangle", "Something has changed in meshio: please submit a bug report"
    return create_dolfin_mesh(created_mesh.points, created_mesh.cells[-1].data)


def mesh_add(obj: Polygon, mesh_geometry: Mesher):
    """Add an object to the mesh.

    Adds as a circle or polygon depending on the obj type

    :param obj: Circle to add
    :param mesh_geometry: Mesher to add the circle to
    :return: None
    """
    if isinstance(obj, Circle):
        add_circle(obj, mesh_geometry)

    return add_poly(obj, mesh_geometry)


def add_circle(obj: Polygon, mesh_geometry: Mesher):
    """Add circle objects to the mesh_geometry.

    :param obj: Circle to add
    :param mesh_geometry: Mesher Geometry to add the circle to
    :return: None
    """
    mesh_geometry.add_circle(obj)


def add_poly(obj: Polygon, mesh_geometry: Mesher):
    """Add polygonal objects to the mesh_geometry.

    :param obj: Polygon (rectangle or generic) to add
    :param mesh_geometry: Mesher to add the polygon to
    :return: None
    """
    mesh_geometry.add_polygon(obj)


def create_dolfin_mesh(points: np.ndarray, cells: np.ndarray) -> df.Mesh:
    """Convert the mesh to a dolfin representation.

    https://bitbucket.org/fenics-project/dolfin/issues/845/initialize-mesh-from-vertices

    :param points: Mesh vertex coordinates
    :param cells: Mesh topology
    :returns: dolfin mesh
    """
    editor = df.MeshEditor()
    mesh = df.Mesh()
    editor.open(mesh, "triangle", 2, 2)
    editor.init_vertices(points.shape[0])
    editor.init_cells(cells.shape[0])
    for k, point in enumerate(points):
        editor.add_vertex(k, point[:2])  # drop 3rd dim
    for k, cell in enumerate(cells):
        editor.add_cell(k, cell)
    editor.close()
    return mesh


def create_mesh_function(name: str, mesh: df.Mesh, dimension: int) -> MeshFunctionSizet:
    """Create boilerplate mesh function.

    :param name: Meshfunction name
    :param mesh: Model mesh
    :param dimension: dimension of the function
    :return: Empty MeshFunction
    """
    mf = df.MeshFunction("size_t", mesh, dimension, mesh.domains())
    mf.set_all(0)
    mf.rename(name, name)

    return mf
