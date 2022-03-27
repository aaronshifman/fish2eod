import dolfin as df
import numpy as np
import pytest
import shapely.geometry as shp

from fish2eod.properties import Property, SpatialFunction, SplineExpression


@pytest.mark.quick
def test_property(square_in_square_in_square_domains):
    domains = square_in_square_in_square_domains
    domain_function = SpatialFunction()
    domain_function[0] = 0
    domain_function[1] = 100
    domain_function[2] = 200
    domain_function[3] = 300

    p = Property(domains, domain_function)

    class Test(object):  # todo mock this in
        index = 0

    a = Test()
    v = [0, 15]
    for c in df.cells(domains.mesh()):
        a.index = c.index()
        p.eval_cell(v, tuple(c.midpoint())[:-1], a)

        assert v[0] == 100 * domains[c]
        assert v[1] == 15


@pytest.mark.quick
def test_functional_expression(square_in_square_in_square_domains):
    domains = square_in_square_in_square_domains
    domain_function = SpatialFunction()
    domain_function[0] = lambda x, y: x * y
    domain_function[1] = lambda x, y: x * y
    domain_function[2] = lambda x, y: x * y
    domain_function[3] = lambda x, y: x * y
    p = Property(domains, domain_function)

    class Test(object):  # todo mock this in
        index = 0

    a = Test()
    v = [0, 15]
    for c in df.cells(domains.mesh()):
        a.index = c.index()
        p.eval_cell(v, tuple(c.midpoint())[:-1], a)

        assert v[0] == c.midpoint()[0] * c.midpoint()[1]
        assert v[1] == 15


@pytest.mark.quick
def test_spline_property(square_in_square_in_square_domains):
    domains = square_in_square_in_square_domains
    line = shp.LineString([shp.Point(-3, 0), shp.Point(3, 0)])
    p = SplineExpression(line, lambda x: x)

    v = [0, 15]
    for c in df.cells(domains.mesh()):
        p.eval(v, tuple(c.midpoint())[:-1])
        assert np.isclose(v[0], (c.midpoint()[0] + 3) / 6)
        assert v[1] == 15
