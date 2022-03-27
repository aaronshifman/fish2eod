from unittest import mock

import numpy as np
import pandas as pd
import pytest

from fish2eod.data.load_data import get_body_data, get_eod_data
from fish2eod.data.settings import FishSettings
from fish2eod.data.species_registry import SPECIES_REGISTRY, register_species
from fish2eod.geometry.fish import Fish, make_eod_fcn


@pytest.fixture
def bogus_fish():
    bogus_settings = FishSettings(
        name="mock",
        normal_length=10,
        head_distance=1,
        tail_distance=9,
        head_conductance=1,
        tail_conductance=2,
        organ_start=2,
        organ_length=6,
        organ_width=0.01,
    )
    register_species("bogus", mock_rectangle_body(), None, bogus_settings)

    yield

    del SPECIES_REGISTRY["bogus"]


def mock_load_body():
    x = [0, 1, 2]
    y = [0, 0, 0]

    return pd.DataFrame({"x": x, "y": y})


def mock_load_eod():
    phase = [0, 0, 0, 1, 1, 1]
    x = [0, 1, 2, 0, 1, 2]
    eod = [5, 6, 7, 10, 11, 12]

    return pd.DataFrame({"phase": phase, "x": x, "eod": eod})


def mock_rectangle_body():
    return pd.DataFrame({"x": [0, 2, 4, 6, 8, 10], "y": [0.1, 0.11, 0.12, 0.13, 0.12, 0.1]})


@pytest.mark.quick
@mock.patch("fish2eod.data.load_data.pd.read_csv", return_value=mock_load_body())
def test_get_body(_):
    body = get_body_data("SomeSpecies")
    assert np.all(body.x == [0, 100, 200])
    assert np.all(body.y == [0, 0, 0])


@pytest.mark.quick
@pytest.mark.parametrize(("phase", "expected"), [(0, [5, 6, 7]), (1, [10, 11, 12])])
@mock.patch("fish2eod.data.load_data.pd.read_csv", return_value=mock_load_eod())
def test_get_eod(_, phase, expected):
    eod = make_eod_fcn(phase, get_eod_data("SomeSpecies"))

    for ix, x in enumerate([0, 0.5, 1]):
        assert np.isclose(expected[ix], eod(x) * 100 * 100)


@pytest.mark.quick
def test_fish_creation(bogus_fish):
    fish = Fish(
        [0, 10],
        [0, 0],
        "bogus",  # todo get these numbers?
    )

    assert np.isclose(
        fish.organ._shapely_representation.area,
        fish.settings.organ_length * 2 * fish.settings.organ_width,
    )
    assert fish.body._shapely_representation.area < fish.outer_body._shapely_representation.area

    assert fish.skin_conductance(0.1, 0.1) == fish.settings.head_conductance
    assert fish.skin_conductance(9.9, 0.1) == fish.settings.tail_conductance
    assert fish.skin_conductance(5, 0.1) == 0.5 * fish.settings.head_conductance + 0.5 * fish.settings.tail_conductance


@pytest.mark.parametrize("species", ["Apteronotus", "Eigenmannia", "bogus"])
@pytest.mark.parametrize("thickness", [0.01, 0.05, 0.1])
@pytest.mark.parametrize(
    ("x", "y", "var", "sign"),
    [
        ([0, 10], [0, 0], 1, 1),
        ([10, 0], [0, 0], 1, -1),
        ([0, 0], [0, 10], 0, -1),
        ([0, 0], [10, 0], 0, 1),
    ],
)
def test_fish_sides(x, y, var, sign, thickness, species, bogus_fish):  # todo fix this up
    fish = Fish(x, y, species, skin_thickness=thickness)  # todo get these numbers?,

    for part in ["body", "outer_body", "organ"]:
        data_l = sign * fish.sides[part].left[:, var]
        data_r = sign * fish.sides[part].right[:, var]
        assert np.mean(data_l) < 0
        assert np.mean(data_r) > 0
