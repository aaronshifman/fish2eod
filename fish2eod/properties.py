# coding=UTF-8
"""Helpers for defining complex properties on a fenics domain.

Properties are UserExpressions for performing specific tasks

SplineExpression defines a function on a boundary mapped [start,stop] -> [0, 1]
Property defines a scalar on a set of domains by domain_id (e.g. conductivity)
"""
from typing import Callable, Dict, List, Tuple, Union

import shapely.geometry as geom
from dolfin import UserExpression
from dolfin.cpp.mesh import MeshFunctionSizet


class SpatialFunction:
    def __init__(self):
        self.domain_set: Dict[int, Union[float, Callable]] = {}

    def __call__(self, domain_id: int, x: float, y: float) -> float:
        f = self.domain_set[domain_id]
        if callable(f):
            return f(x, y)
        return f

    def __setitem__(self, key: int, value: Union[float, Callable]):
        self.domain_set[key] = value

    def __getitem__(self, item):
        return self.domain_set[item]


class SplineExpression(UserExpression):
    """Assign a spline across a boundary.

    :param boundary: Linestring representing the boundary
    :param f: A 1D spline function
    """

    def __init__(self, boundary: geom.LineString, f: Callable[[float], float], **kwargs):
        """Instantiate SplineExpression."""
        super().__init__(**kwargs)

        self.boundary = boundary
        self.boundary_function = f

    def eval(self, values: List[float], x: Tuple[float, float]) -> None:
        """Evaluate expression at a coordinate.

        This function doesn't return but mutates the array argument as per dolfin requirements

        :param values: Implicit return: set values[0]=some_number to return
        :param x: x, y coordinates
        """
        p = geom.Point(x[0], x[1])
        # f(a) needs a fraction along the boundary
        frac = self.boundary.project(p, normalized=True)
        values[0] = self.boundary_function(frac)

    @staticmethod
    def value_shape():
        """Inform dolfin this expression is a scalar."""
        return ()

    def __floordiv__(self, other):
        """Not used but UFL wants this."""


class Property(UserExpression):
    """Class to handle assigning a property across domains.

    :param domains: Labeled domains
    :param f: Dictionary with keys being a domain and value being either a value or a function taking x,y
    """

    def __floordiv__(self, other):
        """Not used but UFL wants this."""

    def __init__(self, domains: MeshFunctionSizet, f: SpatialFunction, **kwargs):
        """Instantiate Property."""
        super().__init__(**kwargs)

        self.domains = domains
        self.f = f

    def eval_cell(self, values: List[float], x: Tuple[float, float], cell):
        """Evaluate the property at a coordinate.

        :param values: Implicit return: set values[0]=some_number to return
        :param x: x, y coordinates of the cell
        :param cell: Geometry cell (element) the function is being accessed on
        """
        domain = self.domains[cell.index]
        values[0] = self.f(domain, x[0], x[1])

    @staticmethod
    def value_shape() -> Tuple:
        """Inform dolfin this expression is a scalar."""
        return ()
