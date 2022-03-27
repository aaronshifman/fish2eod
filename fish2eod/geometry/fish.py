# coding=UTF-8
"""Functions and classes for defining special fish geometries.

Fish is the generic fish class
Apteronotus is a fish of species Apteronotus with appropriate body and parameters
Eigenmannia is a fish of species Eigenmannia with appropriate body and parameters
"""
from typing import Dict, List, NamedTuple, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as shp
from scipy.interpolate import CubicSpline
from shapely import ops

from fish2eod.data.species_registry import SPECIES_REGISTRY
from fish2eod.geometry.operations import (
    cut_line_between_fractions,
    extend_line,
    parallel_curves,
    uniform_spline_interpolation,
)
from fish2eod.geometry.primitives import Polygon
from fish2eod.helpers.type_helpers import FISH_COORDINATES
from fish2eod.math import BoundaryCondition
from fish2eod.properties import SplineExpression


def make_eod_fcn(phase, data):
    data_phase = data.phase
    eod = data.eod

    # Find where the data is "very close" to the target
    eod_ix = np.where(np.isclose(data_phase, phase, rtol=0.001))[0]
    # Convert the eod to a cubic spline parameterized on [0, 1] -> eod(start, end)

    eod_vals = eod.values[eod_ix] / (100 * 100)  # A/m^2 -> A/cm^2
    t = np.linspace(0, 1, len(eod_vals))
    return CubicSpline(t, eod_vals)


class SideStruct(NamedTuple):
    """Convenience struct to hold a left and right side array."""

    left: np.ndarray
    right: np.ndarray


class FishContainer:
    def __init__(self):
        self.fishes: List[Fish] = []

    def __getattr__(self, item: str):
        """Catchall to iterate and pass attribute calls to the fish class

        :param item: Name of the attribute
        :return:
        """
        for f in self.fishes:
            yield f.__getattribute__(item)

    def init_fish(self, fish_x_list: FISH_COORDINATES, fish_y_list: FISH_COORDINATES, species: str) -> None:
        """Initialize all fish.

        Multiple fish are specified with multidimensional lists.

        The x list [0,20] would specify a single fish spanning [0,20]cm.
        The x list [[0,20]] would specify a single fish spanning [0,20]cm.
        The x list [[0,20], [40, 60]] would specify two fish one spanning [0,20]cm and the other [40,60]cm

        Any number of fish can be specified in this manner as long as there are an equal number of fish specified in
        the x and y coordinates.

        :param fish_x_list: List of fish x-coordinates
        :param fish_y_list: List of fish y-coordinates
        :param species: Name of the species
        :param body: Optional custom body geometry
        :param eod: Optional custom eod waveform
        :return: None
        """

        try:
            len(fish_x_list[0])  # check if multidim
        except TypeError:
            fish_x_list = [fish_x_list]
            fish_y_list = [fish_y_list]

        self.fishes = [Fish(x, y, species) for x, y in zip(fish_x_list, fish_y_list)]

    def __len__(self):
        return len(self.fishes)


class Fish:  # todo should this subclass geometry?
    """Body of a fish defined by a skeleton.

    :param skeleton_x: x coordinates of the skeleton
    :param skeleton_y: y coordinates of the skeleton
    :param species: Either a provided name or FishSettings
    :param body: Optional dataframe specifying the body geometry
    :param eod: Optional dataframe specifying the EOD
    """

    def __init__(self, skeleton_x: Sequence[float], skeleton_y: Sequence[float], species: str, skin_thickness=0.01):
        self.species_data = SPECIES_REGISTRY[species]
        self.skin_thickness = skin_thickness
        self.x, self.y = uniform_spline_interpolation(skeleton_x, skeleton_y, n=100, m=500)

        # todo find a way to initialize null polygon
        self.skeleton = shp.LineString(list(zip(self.x, self.y)))
        self.sides: Dict[str, SideStruct] = dict()

        # Setup organ
        organ_bounds = [
            self.settings.organ_start / self.settings.normal_length,
            (self.settings.organ_length + self.settings.organ_start) / self.settings.normal_length,
        ]
        scale_factor = self.skeleton.length / self.settings.normal_length
        self.organ = self.offset_skeleton(
            scale_factor * self.settings.organ_width,
            scale_factor * self.settings.organ_width / 2,
            bounds=organ_bounds,
            lcar=0.05,
        )

        # setup body
        _, body_y = self.get_body_coordinates()
        self.body = self.offset_skeleton(body_y, self.skin_thickness / 4)

        # the outer body (skin) is just the body offset by 0.01cm (100um)
        self.outer_body = self.body.expand(self.skin_thickness)
        self.outer_body.simplify(self.skin_thickness / 4)  # remove number of elements to increase mesh efficiency

        self.setup_sides()  # identify left and right sides

    @property
    def settings(self):
        return self.species_data.settings

    def eod(self, phase):
        data = self.species_data.eod
        return make_eod_fcn(phase, data)

    def setup_sides(self):
        """Tag and create a contour for the left and right sides of each body part."""
        part_name_list = ("body", "outer_body", "organ")
        part_object_list = (self.body, self.outer_body, self.organ)

        for part_name, part_geometry in zip(part_name_list, part_object_list):
            parts = split_body(self.skeleton, part_geometry)
            right, left = assign_left_right(parts, self.skeleton)

            self.sides[part_name] = SideStruct(right=right, left=left)

    def eod_boundary_condition(self, eod, domain_label: int):
        expression = SplineExpression(shp.LineString(self.sides["organ"].left), eod, degree=2)
        label = domain_label
        return BoundaryCondition(value=expression, label=label)

    def get_body_coordinates(self, n: int = 100, m: int = 500):
        """Get the body coordinates uniformly interpolated interpolated.

        :param n: Number of points to interpolate
        :param m: Resolution for computing curve length
        :return: Body x and y coordinates uniformly interpolated
        """
        data = self.species_data.body
        scale_factor = self.skeleton.length / self.settings.normal_length

        # addition of [0] forces a nose point at (0,0)
        body_y = np.concatenate(([0], data.y.values)) * scale_factor
        body_x = np.concatenate(([0], data.x.values)) * scale_factor

        return uniform_spline_interpolation(body_x, body_y, n=n, m=m)

    def offset_skeleton(
        self,
        d: Union[float, Sequence[float]],
        threshold: float,
        bounds: Sequence[float] = None,
        lcar=0.5,
    ) -> Polygon:
        """Create a body part by offsetting the skeleton.

        :param d: Distance from curve to offset
        :param bounds: Optional bounds to offset from. This is used for the organ which is not the whole skeleton
        :param threshold: Width to simplify
        :param lcar: Characteristic length
        :return: The offset polygon
        """
        if bounds:
            # If there are bounds cut out the relevant part and offset it - used for the organ
            cut_line = cut_line_between_fractions(self.skeleton, *bounds)
            curve = parallel_curves(*np.array(cut_line.coords).T, d=d)
        else:
            # Offset the full organ - used for the body
            curve = parallel_curves(self.x, self.y, d=d)

        # extract the inner/outer (left/right) curves and make it into a polygon
        upper_x, upper_y, lower_x, lower_y = (
            curve["x_inner"],
            curve["y_inner"],
            curve["x_outer"],
            curve["y_outer"],
        )

        pol = Polygon(
            np.concatenate((upper_x, lower_x[::-1])),
            np.concatenate((upper_y, lower_y[::-1])),
            lcar=lcar,
        )
        pol.simplify(threshold)

        return pol

    def skin_conductance(self, x: float, y: float) -> float:
        """Compute the skin conductance at a point (x,y) on the skin.

        :param x: x coordinate on skin
        :param y: y coordinate on skin
        :return: Returns the skin conductance
        """
        # Convert skin distance into a fraction of body length
        head_fraction = self.settings.head_distance / self.settings.normal_length
        tail_fraction = self.settings.tail_distance / self.settings.normal_length

        effective_fraction = self.skeleton.project(shp.Point(x, y), normalized=True)

        # return appropriate conductance depending on location
        if effective_fraction < head_fraction:
            return self.settings.head_conductance

        if effective_fraction > tail_fraction:
            return self.settings.tail_conductance

        return self.settings.middle_conductance(head_fraction, tail_fraction, effective_fraction)

    def draw(self, draw_sides=True) -> None:
        """Draw the fish.

        :param draw_sides: Color the sides differently (left red, right green) for debug purposes
        :returns: None
        """
        self.organ.draw()
        self.body.draw()
        self.outer_body.draw()

        if draw_sides:
            plt.plot(*self.sides["body"].right.T, "r")
            plt.plot(*self.sides["body"].left.T, "g")

            plt.plot(*self.sides["outer_body"].right.T, "r")
            plt.plot(*self.sides["outer_body"].left.T, "g")


def split_body(skeleton: shp.LineString, polygon: Polygon) -> List[shp.LineString]:
    """Split a polygon with a skeleton.

    :param skeleton: Body skeleton
    :param polygon: The body part to split
    :return: The two halves of the body part
    """
    # Extend the skeleton past the body to be able to cut the skin
    splitter_x, splitter_y = extend_line(*np.array(skeleton.coords).T)
    splitter = shp.LineString(zip(splitter_x, splitter_y))

    # Extract the contour and split them
    contour = shp.LineString(polygon.shapely_representation.exterior.coords)
    body_halves = ops.split(polygon.shapely_representation, splitter)

    # Fix the body halves to be one-sided and not include the skeleton
    return [clean_linestring(body_half, contour) for body_half in body_halves.geoms]


def clean_linestring(body_half: shp.Polygon, contour: shp.LineString) -> shp.LineString:
    """Fix the cut body contour.

    When the polygon gets cut - the outline of the cutter is embedded into it. This extracts the pure skin contour

    :param body_half: The half body to get the skin from
    :param contour: Contour of the whole fish
    :return: Appropriate sided contour
    """
    # Find where the body_half only intersects with the contour
    side_contour = body_half.buffer(1e-6).intersection(contour)

    # Sometimes the overlap isn't perfect this will merge the fragments
    if isinstance(side_contour, shp.MultiLineString):
        side_contour = ops.linemerge(side_contour)

    return side_contour


def align_contour_head_tail(side: np.ndarray, head: np.ndarray) -> np.ndarray:
    """Reorder a side if necessary so that it runs from head -> tail.

    :param side: Coordinates of the side
    :param head: Coordinate of the head
    :return: Coordinates of the side in correct order
    """
    if np.sqrt(np.sum((side[0] - head) ** 2)) > np.sqrt(np.sum((side[-1] - head) ** 2)):
        return side[::-1]
    return side


def fish_rotation_matrix(head: np.ndarray, tail: np.ndarray) -> np.ndarray:
    """Compute the 2D rotation matrix for the fish with rotation relative to y-axis.

    :param head: Coordinates of the head
    :param tail: Coordinates of the tail
    :return: Rotation matrix
    """
    body_vector = np.array([head[0] - tail[0], head[1] - tail[1]])
    theta = np.arctan2(body_vector[1], body_vector[0]) - np.arctan2(1, 0)
    return np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])


def assign_left_right(parts: List[shp.LineString], skeleton: shp.LineString) -> Tuple[np.ndarray, np.ndarray]:
    """Map the 2 sides onto a "left" and "right" relative to the fish axis.

    :param parts: Tuple of sides to assign
    :param skeleton: The body skeleton
    :return: Tuple of coordinates for right and left (in that order)
    """
    # Extract basic properties
    side1, side2 = np.array(parts[0].coords), np.array(parts[1].coords)
    skeleton = np.array(skeleton.coords)
    head = skeleton[0, :].copy()
    tail = skeleton[-1, :].copy()

    # Order the 2 sides in order of head -> tail
    side1 = align_contour_head_tail(side1, head)
    side2 = align_contour_head_tail(side2, head)

    if determine_right(side1, head, tail, skeleton):
        return side1, side2  # side1 on right
    return side2, side1  # side2 on right


def determine_right(side: np.ndarray, head: np.ndarray, tail: np.ndarray, skeleton: np.ndarray):
    """Determine if the given side is the right side.

    :param side: One of the sides
    :param head: Head coordinates
    :param tail: Tail coordinates
    :param skeleton: Skeleton Coordinates
    :return: If the side is the right side of not
    """
    # Create a clone to rotate
    test_curve = np.copy(side)

    # de-Rotate the skeleton and the curve
    rotation_matrix = fish_rotation_matrix(head, tail)
    rotated_skeleton = np.dot(skeleton - tail, rotation_matrix)
    rotated_curve = np.dot(test_curve - tail, rotation_matrix)

    # If most x-points are more positive than that of the skeleton it's the right
    # This works since the fish is de-rotated to be "parallel-ish" to the y-axis
    shapely_curve = shp.LineString(zip(*rotated_curve.T))
    shapely_midline = shp.LineString(zip(*rotated_skeleton.T))

    side = 0
    for p in zip(*shapely_curve.xy):
        closest_point = shapely_midline.interpolate(shapely_midline.project(shp.Point(p)))

        sign = 1 if p[0] > closest_point.xy[0][0] else -1
        side += sign * abs(p[0])  # weight contribution by distance to the midline
    return side > 0
