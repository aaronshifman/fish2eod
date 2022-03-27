def check_overlap_equal(shape1, shape2):
    err = get_overlap(shape1, shape2)
    assert err < 1e-9


def check_represented_area(s, true_area):
    shapely_area = s._shapely_representation.area

    err = (true_area - shapely_area) / shapely_area
    assert err < 0.01  # tests shapely representation < 1% err


def get_overlap(shape1, shape2):
    true_area = shape1._shapely_representation.area

    overlapping_area = shape1._shapely_representation.intersection(shape2._shapely_representation).area
    return (true_area - overlapping_area) / true_area
