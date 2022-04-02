import pytest

from fish2eod import QESModel, BoundaryCondition
from fish2eod.geometry.primitives import Rectangle, Circle
from fish2eod.mesh.domain import mark_domains
from fish2eod.mesh.mesh import create_mesh
from fish2eod.mesh.model_geometry import ModelGeometry


@pytest.fixture(scope="session")
def square_in_square_in_square():
    """Make a complex nested square structure.

    Default behaviour is a nested square
    Complex behaviour will nest two other squares inside the center square

    :return: Model geometry of the nested squares
    """
    sq1 = Rectangle.from_center([0, 0], 6)
    sq2 = Rectangle.from_center([0, 0], 4)
    mg = ModelGeometry(allow_overlaps=True)
    mg.add_domain("bg", sq1)
    mg.add_domain("fg", sq2)

    sq3 = Rectangle.from_center([0, 0], 2)
    sq4 = Rectangle.from_center([0, 0], 0.5)  # not labeled

    mg.add_domain("fg2", sq3)
    mg.add_domain("fake", sq4)

    return mg


@pytest.fixture(scope="session")
def square_in_square_in_square_domains(square_in_square_in_square):
    mesh = create_mesh(square_in_square_in_square)
    return mark_domains(mesh, square_in_square_in_square)


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