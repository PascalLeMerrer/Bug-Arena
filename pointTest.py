import unittest
import math
from point import Point


class PointTest (unittest.TestCase):

    def test_slide_xy(self):
        point = Point(2, 1)
        point.slide_xy(4, 3)
        self.assertEqual(point.x, 6)
        self.assertEqual(point.y, 4)

    def test_slide_xy_negative(self):
        point = Point(2, 1)
        point.slide_xy(-4, -5)
        self.assertEqual(point.x, -2)
        self.assertEqual(point.y, -4)



    def test_rotate(self):
        point = Point(2, 1)
        rotatedPoint = point.rotate(math.pi)
        self.assertTrue(are_nearly_equal(rotatedPoint.x , -2))
        self.assertTrue(are_nearly_equal(rotatedPoint.y , -1))

    def test_rotate_about(self):
        point = Point(2, 1)
        rotation_center = Point(3, 2)
        rotatedPoint = point.rotate_about(rotation_center, math.pi)
        self.assertTrue(are_nearly_equal(rotatedPoint.x , 4))
        self.assertTrue(are_nearly_equal(rotatedPoint.y , 3))

    def test_rotate_about2(self):
        point = Point(2, 1)
        rotation_center = Point(1, 1)
        rotatedPoint = point.rotate_about(rotation_center, math.pi / 2)
        self.assertTrue(are_nearly_equal(rotatedPoint.x , 1))
        self.assertTrue(are_nearly_equal(rotatedPoint.y , 2))    


    def test_rotate_negative(self):
        point = Point(-1, -1)
        rotatedPoint = point.rotate(math.pi)
        self.assertTrue(are_nearly_equal(rotatedPoint.x , 1))
        self.assertTrue(are_nearly_equal(rotatedPoint.y , 1))

def are_nearly_equal(value1, value2, precision=0.01):
    """
        returns true when the first value is nearly equals to the second
    """
    delta = math.fabs(value1 - value2)
    return delta <= precision


if __name__ == '__main__':
    unittest.main()