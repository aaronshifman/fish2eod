import pytest

from fish2eod.sweep import ParameterSet, ParameterSweep


@pytest.mark.quick
@pytest.mark.parametrize(
    "to_check, good",
    [
        [{}, False],
        [{"x": [1, 2], "y": []}, False],
        [{"x": [1, 2], "y": [1]}, False],
        [{"x": [1]}, True],
        [{"x": [1, 2]}, True],
        [{"x": [1, 2], "y": [3, "4"]}, True],
    ],
)
def test_check_length(to_check, good):
    if good:
        ParameterSet("test", **to_check)
    else:
        with pytest.raises(AssertionError):
            ParameterSet("test", **to_check)


@pytest.mark.quick
def test_parameter_set():
    ps = ParameterSet("abc", a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9])
    names = ["a", "b", "c"]
    targets = [[1, 4, 7], [2, 5, 8], [3, 6, 9]]

    check_parameter_set(ps, names, targets)

    ps2 = ParameterSet("123", y=[100, 200, 300], z=[400, 500, 600])
    ps.add_parameter_set(ps2)

    names = ["a", "b", "c", "y", "z"]
    targets = [[1, 4, 7, 100, 400], [2, 5, 8, 200, 500], [3, 6, 9, 300, 600]]

    check_parameter_set(ps, names, targets)


def check_parameter_set(ps, names, targets):
    assert len(ps) == len(ps._parameters[names[0]])
    assert set(ps.parameters) == set(names)

    for t, p in zip(targets, ps):
        assert t == [p[1][x] for x in names]


@pytest.mark.quick
def test_parameter_sweep_ordering():
    ps1 = ParameterSet("ps1", a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9])
    ps2 = ParameterSet("ps2", x=[100, 200], y=[300, 400])
    remeshable = ParameterSet("remesh", q=[1, 2, 3, 4, 5, 6], rebuild_mesh=True)

    parameter_sweep = ParameterSweep(ps1, remeshable, ps2)  # force the mehs in the middle so its sort will be obvious
    remeshes = list(filter(lambda x: x[0], parameter_sweep))

    assert parameter_sweep.ordered_parameter_sets[0] == remeshable  # remeshable is rightmost
    assert parameter_sweep.remesh_index == 0  # the index of the remeshable is 0
    assert len(parameter_sweep) == 3 * 2 * 6  # there are that many sims
    assert len(remeshes) == len(remeshable)  # should be meshed 6 times (len(remeshable))
    assert [x[1]["q"] for x in remeshes] == remeshable._parameters["q"]
