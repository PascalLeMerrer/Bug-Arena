import unittest
import math
from cshape import OrientableRectShape
from cocos import euclid
from point import Point

class CshapeTest (unittest.TestCase):

    def test_create_unrotated_rectangle(self):

        rectangle, center = self._create_rectangle()

        self.assertEqual(rectangle.A.x, 0)
        self.assertEqual(rectangle.A.y, 3)


        self.assertEqual(rectangle.B.x, 2)
        self.assertEqual(rectangle.B.y, 3)


        self.assertEqual(rectangle.C.x, 2)
        self.assertEqual(rectangle.C.y, 1)

        self.assertEqual(rectangle.D.x, 0)
        self.assertEqual(rectangle.D.y, 1)

    def test_create_rotated_rectangle(self):

        rectangle, center = self._create_rectangle(1, 2, 90)

        self.assertTrue(are_nearly_equal(rectangle.A.x, 0))
        self.assertTrue(are_nearly_equal(rectangle.A.y, 1))
        self.assertTrue(are_nearly_equal(rectangle.B.x, 0))
        self.assertTrue(are_nearly_equal(rectangle.B.y, 3))
        self.assertTrue(are_nearly_equal(rectangle.C.x, 2))
        self.assertTrue(are_nearly_equal(rectangle.C.y, 3))
        self.assertTrue(are_nearly_equal(rectangle.D.x, 2))
        self.assertTrue(are_nearly_equal(rectangle.D.y, 1))

    def test_get_triangle1_area(self):

        rectangle, center = self._create_rectangle()

        area_center_A_B = rectangle._get_triangle_area(center, rectangle.A, rectangle.B)
        self.assertTrue(are_nearly_equal(area_center_A_B, 2))

    def test_get_triangle2_area(self):

        rectangle, center = self._create_rectangle()

        area_center_D_A  = rectangle._get_triangle_area(center, rectangle.D, rectangle.A)
        self.assertTrue(are_nearly_equal(area_center_D_A, 2))

    def test_get_triangle3_area(self):

        rectangle, center = self._create_rectangle()

        area_center_B_C = rectangle._get_triangle_area(center, rectangle.B, rectangle.C)
        self.assertTrue(are_nearly_equal(area_center_B_C, 2))

    def test_get_triangle4_area(self):

        rectangle, center = self._create_rectangle()

        area_center_C_D = rectangle._get_triangle_area(center, rectangle.C, rectangle.D)
        self.assertTrue(are_nearly_equal(area_center_C_D, 2))

    def test_get_triangle5_area(self):

        rectangle, center = self._create_rectangle()

        area_A_B_C = rectangle._get_triangle_area(rectangle.A, rectangle.B, rectangle.C)
        self.assertTrue(are_nearly_equal(area_A_B_C, 4))

    def test_touches_point(self):
        rectangle, center = self._create_rectangle()

        self.assertTrue(rectangle.touches(center))
        self.assertTrue(rectangle.touches(Point(0.5, 1.5)))
        self.assertTrue(rectangle.touches(Point(1.5, 2.5)))
        self.assertTrue(rectangle.touches(Point(0.75, 1.1)))

        self.assertFalse(rectangle.touches(Point(0, 1)))
        self.assertFalse(rectangle.touches(Point(3, 2)))
        self.assertFalse(rectangle.touches(Point(1, 3.5)))
        self.assertFalse(rectangle.touches(Point(-0.5, 2)))

    def test_overlaps_AA_rectangle(self):
        rect1, center1 = self._create_rectangle()
        rect2 = rect1.copy()
        self.assertTrue(rect1.overlaps(rect2))

        rect3, center3 = self._create_rectangle(2, 3)
        self.assertTrue(rect1.overlaps(rect3))

    def test_overlaps_rotated_rectangle(self):
        rect1, center1 = self._create_rectangle()
        rect2, center2 = self._create_rectangle(1, 2, 45)
        self.assertTrue(rect1.overlaps(rect2))
        self.assertTrue(rect2.overlaps(rect1))

        rect3, center3 = self._create_rectangle(2, 3, 45)
        self.assertTrue(rect3.overlaps(rect1))
        self.assertTrue(rect1.overlaps(rect3))

        self.assertTrue(rect3.overlaps(rect2))
        self.assertTrue(rect2.overlaps(rect3))

        rect4, center4 = self._create_rectangle(0, 3, 60)
        self.assertTrue(rect1.overlaps(rect4))
        self.assertTrue(rect4.overlaps(rect1))

        rect5, center5 = self._create_rectangle(4, 2)
        self.assertFalse(rect1.overlaps(rect5))
        self.assertFalse(rect5.overlaps(rect1))

        rect6, center6 = self._create_rectangle(4, 2, 60)
        self.assertFalse(rect1.overlaps(rect6))
        self.assertFalse(rect6.overlaps(rect1))

    def test_get_square_distance(self):
        rect1, center1 = self._create_rectangle()
        p1 = Point(1, 2)
        p2 = Point(4, 2)
        self.assertEqual(rect1._get_square_distance(p1, p2), 9)

    def test_distance(self):
        rect1, center1 = self._create_rectangle()
        rect2, center2 = self._create_rectangle(4, 2)
        self.assertEqual(rect1.distance(rect2), 1) 

        rect3, center3 = self._create_rectangle(1, -2)
        self.assertEqual(rect1.distance(rect3), 2)

        # overlapping shapes
        rect4, center4 = self._create_rectangle(1, 1)
        self.assertEqual(rect1.distance(rect4), 1)

    def test_minmax(self):
        rect1, center1 = self._create_rectangle()
        self.assertEqual(rect1.minmax(), (0, 2, 1, 3))

    def test_fits_in_box(self):
        rect1, center1 = self._create_rectangle()
        self.assertTrue(rect1.fits_in_box((-0.5, 2.5, 0.5, 3.5)))
        self.assertTrue(rect1.fits_in_box((0, 2, 1, 3)))

        rect2, center2 = self._create_rectangle(0, 0, 45)
        self.assertTrue(rect2.fits_in_box((-1.5, 1.5, -1.5, 1.5)))

    def _create_rectangle(self, center_x=1, center_y=2, angle = 0):
        """
        returns a test rectangle (a 2x2 square indeed, centered on point (1,2))
        """
        center = euclid.Vector2(center_x, center_y)
        half_width = 1
        half_height = 1
        
        return (OrientableRectShape(center, half_width, half_height, angle), center)
        

def are_nearly_equal(value1, value2, precision=0.01):
    """
        returns true when the first value is nearly equals to the second
    """
    delta = math.fabs(value1 - value2)
    return delta <= precision


if __name__ == '__main__':
    unittest.main()