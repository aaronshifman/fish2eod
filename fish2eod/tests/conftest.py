import pytest

from fish2eod.geometry.primitives import Rectangle
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
