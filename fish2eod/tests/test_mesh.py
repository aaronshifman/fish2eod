import numpy as np
import pytest

from fish2eod.geometry.primitives import Rectangle
from fish2eod.mesh.mesh import create_mesh
from fish2eod.mesh.model_geometry import ModelGeometry


@pytest.mark.parametrize("corner_x, corner_y, width, height", [[0, 0, 1, 1], [-1, 5, 11, 0.1]])
def test_square_mesh(corner_x, corner_y, width, height):
    bg = Rectangle.from_center([0, 0], 100, 100)
    r = Rectangle([corner_x, corner_y], width, height)

    mg = ModelGeometry(allow_overlaps=True)
    mg.add_domain("bg", bg)
    mg.add_domain("r", r)

    points = [
        (-50, -50),
        (50, -50),
        (50, 50),
        (-50, 50),
        (corner_x, corner_y),
        (corner_x + width, corner_y),
        (corner_x + width, corner_y + height),
        (corner_x, corner_y + height),
    ]

    mesh = create_mesh(mg)
    coordinates = mesh.coordinates()
    for p in points:
        err = coordinates - p
        assert np.isclose(err, 0, atol=1e-6).any()
