"""Helper module for running tests.

Defines default classes and convenience functions.
"""
from os.path import abspath, join, split

import numpy as np
import pandas as pd
from scipy.interpolate import griddata


def compare_comsol(u, filename: str) -> float:
    """Interpolate and compare Comsol and fish2eod solutions.

    :param u: fish2eod solution object
    :param filename: Name of the comsol file
    :return: NRMSE between two solutions
    """
    true_data = pd.read_csv(
        join(split(abspath(__file__))[0], "data", filename + ".txt"),
        delim_whitespace=True,
        skiprows=9,
        names=["x", "y", "v"],
    )

    x = np.linspace(true_data.x.values.min(), true_data.x.values.max(), 100)
    y = np.linspace(true_data.y.values.min(), true_data.y.values.max(), 100)

    comsol = griddata(
        (true_data.x.values, true_data.y.values),
        true_data.v,
        (x[None, :], y[:, None]),
        method="cubic",
    )

    if "fish" in filename:
        fenics_data = [u(a, b) for a, b in zip(true_data.x.values * 100, true_data.y.values * 100)]
    else:
        fenics_data = [u(a, b) for a, b in zip(true_data.x.values, true_data.y.values)]

    fenics = griddata(
        (true_data.x.values, true_data.y.values),
        fenics_data,
        (x[None, :], y[:, None]),
        method="cubic",
    )

    err = comsol - fenics

    return np.sqrt(np.mean(err**2)) / (np.max(comsol) - np.min(comsol))
