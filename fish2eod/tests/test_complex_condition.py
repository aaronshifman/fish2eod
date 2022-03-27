import pytest

from fish2eod import BoundaryCondition, Circle, Rectangle
from fish2eod.models import QESModel
from fish2eod.tests.testing_helpers import compare_comsol


@pytest.fixture(scope="session")
def central_source_model():
    class CentralCircularSource(QESModel):
        def __init__(self, bkg_cond, source_cond, source):
            super().__init__()
            self.bkg_cond = bkg_cond
            self.source_cond = source_cond
            self.source = source

        def create_geometry(self, **kwargs) -> None:
            background = Rectangle([-0.5, -0.5], 1, 1, lcar=0.01)
            source = Circle([0, 0], 0.2, lcar=0.01)  # particularly sensitive to mesh size

            self.model_geometry.add_domain("bkg", background, sigma=self.bkg_cond)
            self.model_geometry.add_domain("source", source, sigma=self.source_cond)

        def get_neumann_conditions(self, **kwargs):
            return [BoundaryCondition(self.source, self.model_geometry["source"])]

        def get_dirichlet_conditions(self, **kwargs):
            return [BoundaryCondition(0, self._EXTERNAL_BOUNDARY)]

    return CentralCircularSource


@pytest.fixture(scope="session")
def complex_geometry_model():
    class ComplexGeometryModel(QESModel):
        def create_geometry(self, **kwargs) -> None:
            background = Rectangle([-0.5, -0.5], 1, 1)
            ground = Circle([-0.4, 0.2], 0.02)
            bottom_source = Circle([0, -0.2], 0.1)
            top_source = Circle([0.2, 0.3], 0.05)

            self.model_geometry.add_domain("bkg", background, sigma=1)
            self.model_geometry.add_domain("ground", ground, sigma=2)
            self.model_geometry.add_domain("bottom_source", bottom_source, sigma=3)
            self.model_geometry.add_domain("top_source", top_source, sigma=4)

        def get_neumann_conditions(self, **kwargs):
            return [
                BoundaryCondition(1, self.model_geometry["bottom_source"]),
                BoundaryCondition(-2, self.model_geometry["top_source"]),
            ]

        def get_dirichlet_conditions(self, **kwargs):
            return [BoundaryCondition(0, self.model_geometry["ground"])]

    return ComplexGeometryModel


@pytest.mark.integration
@pytest.mark.parametrize(
    "bkg_cond, source_cond, source, name",
    [[1, 4, "atan2(x[0], x[1])", "complex_bc"], [lambda x, y: 1 + x, lambda x, y: 1 + y, "1", "complex_cond"]],
)
def test_complex_bc(bkg_cond, source_cond, source, name: str, central_source_model):
    model = central_source_model(bkg_cond=bkg_cond, source_cond=source_cond, source=source)
    model.compile()
    model.solve()

    assert compare_comsol(model._fem_solution, name) <= 0.02


@pytest.mark.integration
def test_complex_geometry(complex_geometry_model):
    model = complex_geometry_model()
    model.compile()
    model.solve()

    assert compare_comsol(model._fem_solution, "multi_geometry") <= 0.02
