"""Common analysis tools for working with dolfin objects with inconsistent methods."""
from typing import NamedTuple

import dolfin as df
import numpy as np


def get_data(f) -> np.ndarray:
    """Get data from a dolfin MeshFunction/function.

    :param f: dolfin object to extract the data from
    :return: Data in a matrix - must be combined with topology for plotting
    """
    try:  # fenics is inconsistent but it seems like one of these will exist
        data = f.compute_vertex_values().reshape((-1, 1))
    except AttributeError:
        data = f.array().reshape((-1, 1))

    return convert_fenics_data(data)


def get_dimension(f) -> int:
    """Get dimension from a dolfin MeshFunction/function.

    :param f: dolfin object to extract the dimension from
    :return: Dimension
    """
    try:  # again inconsistent but one of these will get the dimension
        return f.geometric_dimension()
    except AttributeError:
        return f.dim()


def convert_fenics_data(data: np.ndarray):
    """Convert fenics data into a manipulatable format after loading.

    Fenics data can be saved as unsigned integers for integer meshfunctions which can cause problems. Additionally
    data will be saved as [[x0], [x1], [x2], ... [xn]] so flatten the array.

    :param data: Fenics data in numpy after loading from h5 file
    :return: Data in a usable format
    """

    if len(data.shape) > 1 and data.shape[1] == 1:
        data = data.ravel()

    if np.issubdtype(data.dtype, np.unsignedinteger):
        data = data.astype(np.uint64)

    return data


class Equation(NamedTuple):
    """Helper named tuple for the compiled equation.

    a is the bilinear form
    u is the trial function
    b is the right hand side of the equation
    """

    A: df.Form
    u: df.TrialFunction
    b: df.Form
