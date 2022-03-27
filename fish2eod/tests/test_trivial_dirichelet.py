import numpy as np
import pytest

from fish2eod.geometry.primitives import Rectangle
from fish2eod.math import BoundaryCondition
from fish2eod.models import QESModel


@pytest.fixture(scope="session")
def basic_model():
    class BasicModel(QESModel):
        def create_geometry(self, **kwargs) -> None:
            background = Rectangle([-0.5, -0.5], 1, 1)
            self.model_geometry.add_domain("bkg", background, sigma=1)

    return BasicModel


@pytest.fixture(scope="session")
def square_in_square_model():
    class SquareInSquareModel(QESModel):
        def create_geometry(self, **kwargs) -> None:
            background = Rectangle([-0.5, -0.5], 1, 1)
            square = Rectangle([-0.25, -0.25], 0.5, 0.5)
            self.model_geometry.add_domain("bkg", background, sigma=1)
            self.model_geometry.add_domain("sq", square, sigma=1)

    return SquareInSquareModel


def test_empty_model(basic_model):
    model = basic_model()
    model.compile()
    model.solve()

    assert np.isclose(model._fem_solution(-0.5, -0.5), 0)
    assert np.isclose(model._fem_solution(-0.5, 0.5), 0)
    assert np.isclose(model._fem_solution(0.5, -0.5), 0)
    assert np.isclose(model._fem_solution(0.5, 0.5), 0)


def test_grounded_extremity(basic_model):
    class Model(basic_model):
        def get_dirichlet_conditions(self):
            return [BoundaryCondition(0, self._EXTERNAL_BOUNDARY)]

    model = Model()
    model.compile()
    model.solve()

    assert np.isclose(model._fem_solution(-0.5, -0.5), 0)
    assert np.isclose(model._fem_solution(-0.5, 0.5), 0)
    assert np.isclose(model._fem_solution(0.5, -0.5), 0)
    assert np.isclose(model._fem_solution(0.5, 0.5), 0)


def test_constant_extremity(basic_model):
    class Model(basic_model):
        def get_dirichlet_conditions(self, **kwargs):
            return [BoundaryCondition(1, self._EXTERNAL_BOUNDARY)]

    model = Model()
    model.compile()
    model.solve()

    assert np.isclose(model._fem_solution(-0.5, -0.5), 1)
    assert np.isclose(model._fem_solution(-0.5, 0.5), 1)
    assert np.isclose(model._fem_solution(0.5, -0.5), 1)
    assert np.isclose(model._fem_solution(0.5, 0.5), 1)


def test_interior_boundary(square_in_square_model):
    class Model(square_in_square_model):
        def get_dirichlet_conditions(self, **kwargs):
            return [BoundaryCondition(1, self._EXTERNAL_BOUNDARY)]

    model = Model()
    model.compile()
    model.solve()

    assert np.isclose(model._fem_solution(-0.25, -0.25), 1)
    assert np.isclose(model._fem_solution(-0.25, 0.25), 1)
    assert np.isclose(model._fem_solution(0.25, -0.25), 1)
    assert np.isclose(model._fem_solution(0.25, 0.25), 1)


def test_logical_dirichelet(square_in_square_model):
    class Model(square_in_square_model):
        def get_dirichlet_conditions(self, **kwargs):
            return [BoundaryCondition("1*x[0]<0", self.model_geometry["sq"])]  # todo optional not list

    model = Model()
    model.compile()
    model.solve()

    assert np.isclose(model._fem_solution(-0.25, -0.25), 1)
    assert np.isclose(model._fem_solution(-0.25, 0.25), 1)
    assert np.isclose(model._fem_solution(0.25, -0.25), 0, atol=1e-6)
    assert np.isclose(model._fem_solution(0.25, 0.25), 0, atol=1e-6)
