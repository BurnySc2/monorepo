from shapely.geometry import LinearRing, LineString, MultiLineString, MultiPoint, Point, Polygon


def test_geometry_shapely():
    # Points
    point1 = Point(0.0, 0.0)
    point2 = Point(3.0, 4.0)
    assert point1.area == 0
    assert point1.length == 0
    assert point1.distance(point2) == 5

    # Lines
    line = LineString([(0, 0), (2, 2)])
    assert list(line.coords) == line.coords[:] == [(0, 0), (2, 2)], line.coords[:]
    assert line.hausdorff_distance(point1) == point1.hausdorff_distance(line) == 2**1.5
    assert line.length == 2**1.5
    assert line.area == 0
    assert line.bounds == (0, 0, 2, 2), line.bounds
    line2 = LineString([(0, 2), (2, 0)])
    assert line.intersection(line2) == Point(1, 1)
    assert not line.contains(point1)
    assert not line.contains(point2)

    # Rings
    ring = LinearRing([(0, 0), (1, 1), (1, 0)])
    assert abs(ring.length - 3.414213) < 0.000001
    assert ring.bounds == (0, 0, 1, 1)

    # Polygon
    polygon = Polygon([(0, 0), (1, 1), (1, 0)])
    assert polygon.area == 0.5
    assert abs(polygon.length - 3.414213) < 0.000001
    assert polygon.bounds == (0, 0, 1, 1)
    assert not polygon.contains(point1)
    assert not polygon.contains(point2)

    # Points with radius
    a: Point = Point(1, 1).buffer(1.5)
    b: Point = Point(2, 1).buffer(1.5)
    difference = a.difference(b)
    assert isinstance(difference, Polygon)

    union = a.boundary.union(b.boundary)
    assert isinstance(union, MultiLineString)

    # MultiPoint is a collection of points
    # Calculate the minimum box or polygon that contains these points
    multi = MultiPoint([(0, 0), (1, 1), (2, 0.5)]).minimum_rotated_rectangle
    assert isinstance(multi, Polygon)


if __name__ == '__main__':
    test_geometry_shapely()
