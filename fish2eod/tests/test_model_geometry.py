import pytest

from fish2eod.geometry.primitives import Circle, Rectangle
from fish2eod.mesh.model_geometry import ModelGeometry

overlaps_c1 = Circle([0, 0], 0.5)
not_on_bg = Circle([15, 15], 1)
c1 = Circle([0, 0], 1)
c2 = Circle([2, 2], 1)


@pytest.fixture
def base_geometry():
    bg = Rectangle.from_center([0, 0], 10)
    mg = ModelGeometry()
    mg.add_domain("bg", bg)
    return mg


@pytest.mark.quick
def test_create_only_bg():
    ModelGeometry()


@pytest.mark.quick
def test_create_seperate_domains(base_geometry):
    mg = ModelGeometry(base_geometry)
    mg.add_domain("c1", c1)
    mg.add_domain("c2", c2)


@pytest.mark.quick
def test_not_on_bg(base_geometry):
    with pytest.raises(ValueError) as _:
        base_geometry.add_domain("off", not_on_bg)


@pytest.mark.quick
def test_multiple_on_domain(base_geometry):
    base_geometry.add_domain("c", c1, c2)


@pytest.mark.quick
def test_reuse_name(base_geometry):
    base_geometry.add_domain("c1", c1)
    with pytest.raises(ValueError):
        base_geometry.add_domain("c1", c2)


@pytest.mark.quick
def test_overlap_different_domain(base_geometry):
    base_geometry.add_domain("c1", c1)
    with pytest.raises(ValueError):
        base_geometry.add_domain("o1", overlaps_c1)


@pytest.mark.quick
def test_overlap_same_domain(base_geometry):
    with pytest.raises(ValueError):
        base_geometry.add_domain("o1", c1, overlaps_c1)
