import numpy as np
import pytest

from fish2eod.geometry.primitives import Circle, Rectangle
from fish2eod.tests.geometry_primitives.computation import (
    check_overlap_equal,
    check_represented_area,
    get_overlap,
)


@pytest.mark.quick
@pytest.mark.parametrize("r", [0.1, 1, 100])
@pytest.mark.parametrize("y", [-100, 100, 0, 0.1, -0.1])
@pytest.mark.parametrize("x", [-100, 100, 0, 0.1, -0.1])
def test_create_circle(x, y, r):
    c = Circle([x, y], r)

    # Check center and radius
    assert np.isclose([x, y], c.center).all()
    assert c.radius == r

    check_represented_area(c, np.pi * r * r)


@pytest.mark.quick
@pytest.mark.parametrize("dy", [100, -0.1])
@pytest.mark.parametrize("dx", [100, -0.1])
@pytest.mark.parametrize("r", [0.1, 100])
@pytest.mark.parametrize("y", [-100, 0.1])
@pytest.mark.parametrize("x", [-100, 0.1])
def test_translate(x, y, r, dx, dy):
    c = Circle([x, y], r)
    re_done = c.translate(dx=dx, dy=dy).translate(dx=-dx, dy=-dy)
    check_overlap_equal(c, re_done)


@pytest.mark.quick
@pytest.mark.parametrize("angle", [123, -1.5])
@pytest.mark.parametrize("center", [(11, -15), (-102, 1)])
@pytest.mark.parametrize("degrees", [True, False])
@pytest.mark.parametrize("r", [0.1, 100])
@pytest.mark.parametrize("y", [-100, 0.1])
@pytest.mark.parametrize("x", [-100, 0.1])
def test_rotate(x, y, r, angle, degrees, center):
    r = Rectangle.from_center([0, 0], 5, 5)
    re_done = r.rotate(angle, degrees, center).rotate(-angle, degrees, center)

    check_overlap_equal(r, re_done)


@pytest.mark.quick
@pytest.mark.parametrize(
    "px, py, inside", [[-100, 0.1, False], [123, -0.5, True], [123, -3.4999, True], [120.0001, -0.5, True]]
)
def test_inside_circle(px, py, inside):
    c = Circle([123, -0.5], 3)
    expr = c.inside(None, None, buffer=0).replace("x[0]", str(px)).replace("x[1]", str(py))

    assert eval(expr) == inside


@pytest.mark.quick
@pytest.mark.parametrize("padding", [0.1, 100])
@pytest.mark.parametrize("r", [0.1, 100])
@pytest.mark.parametrize("y", [-100, 0.1])
@pytest.mark.parametrize("x", [-100, 0.1])
def test_offset_circle(x, y, r, padding):
    c = Circle([x, y], r)
    new_c = c.expand(padding)

    theory_overlap = (np.pi * (r + padding) ** 2 - np.pi * r**2) / (np.pi * (r + padding) ** 2)
    measured_overlap = get_overlap(new_c, c)

    err = abs(theory_overlap - measured_overlap) / theory_overlap
    assert err < 0.005
