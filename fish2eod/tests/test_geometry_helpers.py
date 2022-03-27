import numpy as np
import pytest
import shapely.geometry as shp

from fish2eod.geometry.operations import (
    cut_line_between_fractions,
    extend_line,
    filter_line_length,
    measure_and_interpolate,
    parallel_curves,
    uniform_spline_interpolation,
)


@pytest.mark.quick
@pytest.mark.parametrize(
    "x, y, m, d_true",
    [
        [[0, 1, 2], [0, 1, 2], 10, np.sqrt(8)],
        [[0, 1, 2], [0, 1, 2], 3, np.sqrt(8)],
        [[0, 1, 2], [0, 0, 0], 10, 2],
        [[0, 1, 2, 5], [0, 1, 0, 0], 10, 3 + 2 * np.sqrt(2)],
    ],
)
def test_measure_and_interpolate(x, y, m, d_true):
    d, xi, yi = measure_and_interpolate(x, y, m)

    assert len(xi) >= m
    assert len(yi) >= m
    assert pytest.approx(d_true) == np.sum(d)


@pytest.mark.quick
@pytest.mark.parametrize(
    "x, y, n, expected_segment_length",
    [
        [[0, 1, 2], [0, 0, 0], 5, 0.5],
        [[0, 1, 2], [0, 0, 0], 101, 2 / 100],
        [[0, 1, 2, 5], [0, 1, 0, 0], 100, (3 + 2 * np.sqrt(2)) / 99],  # need large numer of pts because of sharp bends
    ],
)
def test_uniform_spline_interpolation(x, y, n, expected_segment_length):
    xi, yi = uniform_spline_interpolation(x, y, n)

    assert len(xi) == n == len(yi)
    segment_lengths = np.sqrt(np.diff(xi) ** 2 + np.diff(yi) ** 2)
    assert segment_lengths == pytest.approx(expected_segment_length, abs=1e-2)


@pytest.mark.quick
def test_uniform_spline_sine():
    x = np.linspace(0, 10, 20)
    y = np.exp(x)

    n = 40
    xi, yi = uniform_spline_interpolation(x, y, n)

    target_distance, *_ = measure_and_interpolate(x, y, 100)
    target_distance = sum(target_distance) / (n - 1)

    measured_distance = np.sqrt(np.diff(xi) ** 2 + np.diff(yi) ** 2)

    assert np.std(measured_distance) / np.mean(measured_distance) <= 0.01  # < 1% cv
    assert abs(np.mean(measured_distance) - target_distance) / target_distance <= 0.01  # <1% error


@pytest.mark.quick
def test_cut_line_between_fractions():
    line = shp.LineString(zip([0, 1], [0, 0]))

    cut_line = cut_line_between_fractions(line, 1 / 3, 2 / 3)

    x_t, y_t = np.array(cut_line.coords).T

    d = np.sqrt((max(x_t) - min(x_t)) ** 2 - (max(y_t) - min(y_t)) ** 2)

    assert pytest.approx(1 / 3) == d
    assert pytest.approx(2 / 3) == max(x_t)
    assert pytest.approx(1 / 3) == min(x_t)


@pytest.mark.quick
@pytest.mark.parametrize(
    ("f1", "f2", "good_bad"),
    [
        (0.6, 0.7, True),
        (0.6, 0.75, False),
        (0.6, 0.707, False),
        (0.605, 0.7, False),
        (0.4, 0.6, False),
        (1.4, 1.5, False),
    ],
)
def test_filter_line_length(f1, f2, good_bad):
    original = shp.LineString(zip([0, 1], [0, 0]))
    sub_line = shp.LineString(zip([f1, f2], [0, 0]))
    assert filter_line_length(original, 0.6, 0.7, sub_line) == good_bad


@pytest.mark.quick
def test_offset_curve_straight_line():
    x = [0, 1]
    y = [0, 0]

    offset_dict = parallel_curves(x, y, 1)

    x_inner = offset_dict["x_inner"]
    x_outer = offset_dict["x_outer"]

    y_inner = offset_dict["y_inner"]
    y_outer = offset_dict["y_outer"]

    assert pytest.approx(x) == x_inner
    assert pytest.approx(x) == x_outer
    assert pytest.approx(1) == y_inner
    assert pytest.approx(-1) == y_outer


@pytest.mark.quick
@pytest.mark.parametrize("x, y, f, expected_length", [[[0, 1, 2], [0, 0, 0], 0.01, 2.04]])
def test_extend_curve(x, y, f, expected_length):
    e_x, e_y = extend_line(x, y, f)

    length = np.sum(np.sqrt(np.diff(e_x) ** 2 + np.diff(e_y) ** 2))
    assert pytest.approx(expected_length, 1e-2) == length
