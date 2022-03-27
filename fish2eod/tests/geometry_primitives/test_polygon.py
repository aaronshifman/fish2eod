import numpy as np
import pytest

from fish2eod import Polygon
from fish2eod.tests.geometry_primitives.computation import check_represented_area


@pytest.mark.quick
@pytest.mark.parametrize(
    "x, y, area",
    [[[0, 1, 1], [0, 0, 1], 0.5], [[0, 1, 1, 0], [0, 0, 1, 1], 1]],  # triangle  # square
)
def test_polygon(x, y, area):
    p = Polygon(x, y)
    check_represented_area(p, 1 / 2 * 1 * 1)
    x_in, y_in = zip(*p._shapely_representation.exterior.coords)

    assert np.all(np.array(x) == x_in[:-1])
    assert np.all(np.array(y) == y_in[:-1])


@pytest.mark.quick
def test_invalid_polygon():
    with pytest.raises(ValueError):
        Polygon([0, 1, 0, 1], [0, 1, 1, 0])  # crosses
