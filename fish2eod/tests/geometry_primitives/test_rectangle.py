import numpy as np
import pytest

from fish2eod.geometry.primitives import Rectangle
from fish2eod.tests.geometry_primitives.computation import check_represented_area


@pytest.mark.quick
@pytest.mark.parametrize(
    "corner_x, corner_y, width, height, expected_center, expected_h",
    [[0, 0, 5, None, (2.5, 2.5), 5], [-100, 100, 10, 15, (-95, 107.5), 15], [-11, 0, 1000, 11.2, (489, 5.6), 11.2]],
)
def test_create_rectangle(
    corner_x: float, corner_y: float, width: float, height: float, expected_center, expected_h: float
):
    r = Rectangle([corner_x, corner_y], width, height)
    assert np.isclose(r.center, expected_center).all()
    assert r.height == expected_h
    check_represented_area(r, width * expected_h)


@pytest.mark.quick
@pytest.mark.parametrize(
    "center_x, center_y, width, height, expected_h",
    [[0, 0, 5, None, 5], [-100, 100, 10, 15, 15], [-11, 0, 1000, 11.2, 11.2]],
)
def test_create_rectangle_center(center_x: float, center_y, width: float, height: float, expected_h: float):
    r = Rectangle.from_center([center_x, center_y], width, height)
    assert np.isclose(r.center, (center_x, center_y)).all()
    assert r.height == expected_h
    check_represented_area(r, width * expected_h)


@pytest.mark.quick
@pytest.mark.parametrize(
    "px, py, inside",
    [
        [123, -456, True],
        [130.9999, -456, True],
        [131.00001, -456, False],
        [126, -461.999, True],
        [126, -462.001, False],
        [115.001, -462.001, False],
        [115.001, -461.999, True],
    ],
)
def test_inside_square(px, py, inside):
    r = Rectangle.from_center([123, -456], 16, 12)
    expr = r.inside(None, None, buffer=0).replace("x[0]", str(px)).replace("x[1]", str(py)).replace("&&", "and")

    assert eval(expr) == inside
