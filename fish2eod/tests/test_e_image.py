from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fish2eod import BaseFishModel, Circle, ElectricImageParameters, compute_transdermal_potential


def dataset_1(x):
    data = pd.read_csv(
        Path(__file__).parent / "data" / "Comsol_EI_sphere_5mm_diam_x02_04_06_08_phase6.csv",
        skiprows=8,
        names=["x", "ei"],
    )

    splits = [0] + list(np.where(data["x"].diff() < -0.2)[0]) + [1000000]  # some number at the end
    data_partitions = [data.iloc[i : j - 1, [0, 1]].reset_index(drop=True) for i, j in zip(splits[:-1], splits[1:])]

    return {"x": x, "cond": 5.998e5 / 100, "data": data_partitions[x // 2 - 1], "eod_phase": 0.24, "r": 0.25}


def dataset_2(cond):
    data = pd.read_csv(
        Path(__file__).parent / "data" / "Comsol_EI_sphere_rad1mm_x06_phase6_condsweep.csv",
        skiprows=8,
        names=["x", "ei"],
    )

    splits = [0] + list(np.where(data["x"].diff() < -0.2)[0]) + [1000000]  # some number at the end
    data_partitions = [data.iloc[i : j - 1, [0, 1]].reset_index(drop=True) for i, j in zip(splits[:-1], splits[1:])]

    parts = {2.3e-5 / 100: 0, 0.0115 / 100: 1, 0.23 / 100: 2}
    return {"x": 6, "cond": cond, "data": data_partitions[parts[cond]], "eod_phase": 0.24, "r": 0.1}


@pytest.fixture(
    params=[
        *[(dataset_1, x) for x in [2, 4, 6, 8]],
        *[(dataset_2, c) for c in [2.3e-5 / 100, 0.0115 / 100, 0.23 / 100]],
    ]
)
def data(request):  # trick to concatenate fixtures
    dataset, *p = request.param
    return dataset(*p)


@pytest.fixture(scope="session")
def model_class():
    class Model(BaseFishModel):
        def add_geometry(self, x, r, c, **kwargs):
            prey = Circle((x, 2), r)

            self.model_geometry.add_domain("prey", prey, sigma=c)  # copper sphere S/cm

    return Model


def test_e_image(data, model_class):
    x, cond, true_ei, phase, r = data["x"], data["cond"], data["data"], data["eod_phase"], data["r"]

    model = model_class()
    EIP = ElectricImageParameters(domains=("prey",), value=model.WATER_CONDUCTIVITY)
    parameters = {"fish_x": [0, 21], "fish_y": [0, 0], "image": EIP, "x": x, "eod_phase": phase, "r": r, "c": cond}
    model.compile(**parameters)
    model.solve(**parameters)

    skin, e_image = list(compute_transdermal_potential(model))[0]

    test_x, test_y = skin.right_outer[:, 0], e_image.right_tdp
    true_x, true_y = true_ei["x"] * 100, true_ei["ei"]

    test_y = np.interp(true_x, test_x, test_y)

    nrmse = np.sqrt(np.mean((test_y - true_y) ** 2)) / (true_y.max() - true_y.min())
    assert nrmse < 0.04  # < 4%
