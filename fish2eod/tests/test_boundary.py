"""Test components related to boundaries and labeling them."""
import dolfin as df
import numpy as np
import pytest

from fish2eod.math import BoundaryCondition
from fish2eod.mesh.boundary import (
    boundary_iterator,
    mark_boundaries,
    mark_edge_by_rules,
)
from fish2eod.mesh.domain import mark_domains
from fish2eod.mesh.mesh import create_mesh


@pytest.fixture(scope="session")
def simple_domain(size=15):
    """Construct a simple meshfunction representing domains.

    Simple is defined as 0 defined on the left half (x < 0.5) and 1 on the right side (x > 0.5)

    :param size: Resolution of the mesh
    :return: Domain function
    """
    mesh = df.UnitSquareMesh(size, size)
    domain = df.MeshFunction("size_t", mesh, 2)

    # make MeshFunction with right = 1 and left = 0
    for c in df.cells(mesh):
        if c.midpoint()[0] > 0.5:
            domain[c] = 1
    return domain


@pytest.fixture(scope="session")
def complex_domain(size=15):
    """Construct a complex meshfunction representing domains.

    If on the right half the function is 1 if y < 0.5 and 2 if y > 0.5

    :param size: Resolution of the mesh
    :return: Domain function
    """
    mesh = df.UnitSquareMesh(size, size)
    domain = df.MeshFunction("size_t", mesh, 2)

    # make MeshFunction with left = 0 and right = 1 if lower and 2 if upper
    for c in df.cells(mesh):
        if c.midpoint()[0] > 0.5:
            if c.midpoint()[1] > 0.5:
                domain[c] = 2
            else:
                domain[c] = 1
    return domain


@pytest.mark.quick
def test_boundary_iterator(simple_domain):
    """Test iterating over a domain meshfunction.

    The simple meshfunction has a single boundary at x = 0.5. The bordering domains are values 0, 1
    """
    for edge, neighbouring_domains in boundary_iterator(simple_domain):
        assert pytest.approx(0.5) == edge.midpoint()[0]
        assert neighbouring_domains == (0, 1)


@pytest.mark.quick
def test_complicated_boundary_iterator(complex_domain):
    r"""Test iterating over a domain meshfunction.

    The complex meshfunction has 2 boundaries

    There is a boundary at x=0.5
    There is a boundary at y=0.5 for x\in [0.5, 1]

    The first boundary has mating domains of 0,1 or 0,2 depending on where it is
    The second has the domains 1, 2
    """
    for edge, neighbouring_domains in boundary_iterator(complex_domain):
        if np.isclose(edge.midpoint()[0], 0.5):
            assert neighbouring_domains == (0, 1) or neighbouring_domains == (0, 2)
        else:
            assert pytest.approx(0.5) == edge.midpoint()[1]
            assert neighbouring_domains == (1, 2)


@pytest.mark.quick
def test_mark_edge_by_rules(complex_domain):
    """Test marking boundaries with a rule.

    The rule used is only when the mating domains are 1 and 2.
    """
    marker = lambda b1, b2: (b1 == 1 and b2 == 2, 100)

    for edge, neighbouring_domains in boundary_iterator(complex_domain):
        label = mark_edge_by_rules(neighbouring_domains, marker)
        if neighbouring_domains == (1, 2):
            assert label == 100
        else:  # Boundary was not labeled so None
            assert label is None


@pytest.mark.quick
def test_mark_boundaries(square_in_square_in_square):
    """Test the marking of boundaries.

    Mark the boundaries on the complex 4-nested square
    """
    mg = square_in_square_in_square
    mesh = create_mesh(mg)
    domains = mark_domains(mesh, mg)
    bm = lambda b1, b2: (
        b1 == mg.domain_names["fg"] and b2 == mg.domain_names["fg2"],
        200,
    )  # mark boundary between fg and fg2 as 200
    boundaries, _ = mark_boundaries(domains, mg, bm, external_boundary=9999)

    # manually check edges (facets)
    for f in df.facets(boundaries.mesh()):
        mp = f.midpoint()

        if np.isclose(abs(mp[0]), 3) or np.isclose(abs(mp[1]), 3):
            expected = 9999
        elif np.isclose(abs(mp[0]), 2) and abs(mp[1]) <= 2 or np.isclose(abs(mp[1]), 2) and abs(mp[0]) <= 2:
            expected = 1
        elif np.isclose(abs(mp[0]), 1) and abs(mp[1]) <= 1 or np.isclose(abs(mp[1]), 1) and abs(mp[0]) <= 1:
            expected = 200
        elif np.isclose(abs(mp[0]), 0.25) and abs(mp[1]) <= 0.25 or np.isclose(abs(mp[1]), 0.25) and abs(mp[0]) <= 0.25:
            expected = 0
        else:
            expected = 0

        assert boundaries[f] == expected


@pytest.mark.parametrize("val", [-100, 0, 100, 1e6])
def test_boundary_condition_representation(val):
    """Test implementation of boundary conditions and the various methods are equivalent.

    :param val: Value to set bc
    """
    b1 = BoundaryCondition(str(val), 1).to_fenics_representation()  # string def
    b2 = BoundaryCondition(val, 1).to_fenics_representation()  # numeric def
    b3 = BoundaryCondition(df.Expression(str(val), degree=2), 1).to_fenics_representation()

    mesh = df.UnitSquareMesh(15, 15)

    b1 = b1.compute_vertex_values(mesh)
    b2 = b2.compute_vertex_values(mesh)
    b3 = b3.compute_vertex_values(mesh)

    assert np.all(b1 == b2)
    assert np.all(b1 == b3)

    assert np.allclose(b1, val)
