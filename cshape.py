import math
from cocos.euclid import Vector2
from point import Point

class OrientableRectShape(object):
    """
    Implements the Cshape interface that uses rectangles with a possible rotation.
    
    Distance is not the euclidean distance but the rectangular or max-min
    distance, max( min(x0 - x1), min(y0 - y1) : (xi, yi) in recti )
    
    Good if actors rotate.

    Look at Cshape for other class and methods documentation.
    """
    
    def __init__(self, center, half_width, half_height, angle):
        """
        :Parameters:
            `center` : euclid.Vector2
                rectangle center
            `half_width` : float
                half width of rectangle
            `half_height` : float
                half height of rectangle
            'angle' : float
                orientation of the rectangle, in degrees
        """
        self.half_width = half_width
        self.half_height = half_height
        self.center = center
        self.update_position()
        self.rotate(angle)

    def update_position(self):
        self.unrotated_A = Point(self.center.x - self.half_width, self.center.y + self.half_height)
        self.unrotated_B = Point(self.center.x + self.half_width, self.center.y + self.half_height)
        self.unrotated_C = Point(self.center.x + self.half_width, self.center.y - self.half_height)
        self.unrotated_D = Point(self.center.x - self.half_width, self.center.y - self.half_height)

    def move_by(self, dx, dy):
        ''' moves the shape
            dx distance in pixels along horizontal axis
            dy distance in pixels along vertical axis 
        '''
        self.unrotated_A.x += dx
        self.unrotated_B.x += dx
        self.unrotated_C.x += dx
        self.unrotated_D.x += dx

        self.unrotated_A.y += dy
        self.unrotated_B.y += dy
        self.unrotated_C.y += dy
        self.unrotated_D.y += dy

        self.center.x += dx
        self.center.y += dy

        self.A.x += dx
        self.B.x += dx
        self.C.x += dx
        self.D.x += dx

        self.A.y += dy
        self.B.y += dy
        self.C.y += dy
        self.D.y += dy

    def rotate(self, angle):
        """
        :Parameters:
            'angle': float
                the new rotation of the shape, in degrees
        """        
        self.angle = angle
        rad = math.radians(angle)
        self.A = self.unrotated_A.rotate_about(self.center, rad)
        self.B = self.unrotated_B.rotate_about(self.center, rad)
        self.C = self.unrotated_C.rotate_about(self.center, rad)
        self.D = self.unrotated_D.rotate_about(self.center, rad)

    def _get_triangle_area(self, A,B,C):
        """
            :Parameters:
                'A' : Point
                'B' : Point
                'C' : Point
                A, B, C must be in clockwise order
            :rtype: float 
                the double of the area of the ABC triangle
        """    
        return (C.x*B.y-B.x*C.y)-(C.x*A.y-A.x*C.y)+(B.x*A.y-A.x*B.y)
    
    def _get_square_distance(self, p1, p2):
        """
            :Parameters:
                'p1' : Point - first point
                'p2' : Point - second point
            :rtype: float
                the square of the distance  between p1 and p2
        """
        return (p1.x - p2.x)**2 + (p1.y - p2.y)**2

    def overlaps(self, other):
        if self == other:
            return False
        
        return (self.touches(other.center)
             or self.touches(other.A)
             or self.touches(other.B)
             or self.touches(other.C)
             or self.touches(other.D)
             or other.touches(self.center)
             or other.touches(self.A)
             or other.touches(self.B)
             or other.touches(self.C)
             or other.touches(self.D))

    def distance(self, other):
        """
            TODO: find some optimization
        """
        square_distance = min(self._get_square_distance(self.A, other.A),
                              self._get_square_distance(self.A, other.B),
                              self._get_square_distance(self.A, other.C),
                              self._get_square_distance(self.A, other.D),
                              self._get_square_distance(self.B, other.A),
                              self._get_square_distance(self.B, other.B),
                              self._get_square_distance(self.B, other.C),
                              self._get_square_distance(self.B, other.D),
                              self._get_square_distance(self.C, other.A),
                              self._get_square_distance(self.C, other.B),
                              self._get_square_distance(self.C, other.C),
                              self._get_square_distance(self.C, other.D),
                              self._get_square_distance(self.D, other.A),
                              self._get_square_distance(self.D, other.B),
                              self._get_square_distance(self.D, other.C),
                              self._get_square_distance(self.D, other.D))
        if square_distance < 0.0:
            result = 0.0
        else:
            result = math.sqrt(square_distance)
        return result
    
    def near_than(self, other, near_distance):
        return self.distance(other) <= near_distance

    def touches_point(self, x, y):        
        P = Point(x, y)
        return self.touches(P)

    def touches(self, P):
        return (self._get_triangle_area(self.A, self.B, P) > 0 
            and self._get_triangle_area(self.B, self.C, P) > 0 
            and self._get_triangle_area(self.C, self.D, P) > 0 
            and self._get_triangle_area(self.D, self.A, P) > 0)

    def fits_in_box(self, packed_box):
        minmax = self.minmax()
        return (packed_box[0] <= minmax[0]
            and packed_box[1] >= minmax[1] 
            and packed_box[2] <= minmax[2]
            and packed_box[3] >= minmax[3])

    def minmax(self):
        return (min(self.A.x, self.B.x, self.C.x, self.D.x),
                max(self.A.x, self.B.x, self.C.x, self.D.x),
                min(self.A.y, self.B.y, self.C.y, self.D.y),
                max(self.A.y, self.B.y, self.C.y, self.D.y))

    def copy(self):
        return OrientableRectShape(Vector2(self.center.x, self.center.y), 
                                              self.half_width, 
                                              self.half_height, 
                                              self.angle) 
    def __repr__(self):
        return self.A.__repr__() + " " + self.B.__repr__() + " " + self.C.__repr__() + " " + self.D.__repr__()
