import math
from copy import deepcopy

# Defines the vector classes
class Vector3d:
    def __init__(self, *x):
        assert len(x)==3, "Unexpected arguments"
        self.x = x[0]
        self.y = x[1]
        self.z = x[2]

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalise(self):
        # Normalising the vector means changing the variables
        # So the direction is preserved but the length is equal to 1
        length = self.length()
        if length > 0:
            self.x /= length
            self.y /= length
            self.z /= length

    def distance(self, point):
        # See Wireframe.face.distance
        return (self.x - point.x) ** 2 + \
               (self.y - point.y) ** 2 + \
               (self.z - point.z) ** 2

    def list(self):
        return [self.x, self.y, self.z]

    def __add__(self, vect):
        return Vector3d(self.x + vect.x, self.y + vect.y, self.z + vect.z)

    def add(self, vect):
        # Same thing as above, but works inplace
        self.x += vect.x
        self.y += vect.y
        self.z += vect.z

    def __sub__(self, vect):
        return Vector3d(self.x - vect.x, self.y - vect.y, self.z - vect.z)

    def sub(self, vect):
        self.x -= vect.x
        self.y -= vect.y
        self.z -= vect.z

    def __mul__(self, scalar):
        if isinstance(scalar, Vector3d):
            return Vector3d(self.x * scalar.x, self.y * scalar.y, self.z * scalar.z)
        else:
            return Vector3d(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar):
        return Vector3d(self.x / scalar, self.y / scalar, self.x / scalar)

    def mul(self, scalar):
        if isinstance(scalar, Vector3d):
            self.x *= scalar.x
            self.y *= scalar.y
            self.z *= scalar.z
        else:
            self.x *= scalar
            self.y *= scalar
            self.z *= scalar

    def crossProduct(self, vect1):
        # sets itself to a vector perpendicular to itself and vect1 (itself and vect1 need to be normalised)
        temp = Vector3d(0, 0, 0)
        temp.x = self.y * vect1.z - self.z * vect1.y
        temp.y = self.z * vect1.x - self.x * vect1.z
        temp.z = self.x * vect1.y - self.y * vect1.x
        self.x = temp.x
        self.y = temp.y
        self.z = temp.z

    @staticmethod
    def dotProduct(vect1, vect2):
        # A test of similarity between 2 normalised vectors.
        # 1 means they are equal
        # 0 means they are at right angles to each other
        # -1 means that they are facing in opposite directions
        return (vect1.x * vect2.x) + (vect1.y * vect2.y) + (vect1.z * vect2.z)

    @staticmethod
    def returnCrossProduct(vect1, vect2):
        # Exactly like the cross product method but returns one, instead of acting in place
        temp = Vector3d(0, 0, 0)
        temp.x = vect2.y * vect1.z - vect2.z * vect1.y
        temp.y = vect2.z * vect1.x - vect2.x * vect1.z
        temp.z = vect2.x * vect1.y - vect2.y * vect1.x
        return temp

    def copy(self):
        return deepcopy(self)

    def tuple(self):
        return eval(self.__str__())

    def __str__(self):
        return '(%.2f, %.2f, %.2f)' % (self.x, self.y, self.z)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __eq__(self, other):
        if isinstance(other, Vector3d):
            return self.x == other.x and self.y == other.y and self.z == other.z
        else:
            return bool(other)

    def __ne__(self, vect):
        return not self.__eq__(vect)

class Vector2d:
    def __init__(self, *x):
        assert len(x)==2, "Unexpected arguments"
        self.x = x[0]
        self.y = x[1]

    def length(self):
        return math.hypot(self.x, self.y)

    def normalise(self):
        length = self.length()
        self.x /= length
        self.y /= length

    def copy(self):
        return deepcopy(self)

    def __add__(self, vect):
        return Vector2d(self.x + vect.x, self.y + vect.y)

    def __sub__(self, vect):
        return Vector2d(self.x - vect.x, self.y - vect.y)

    def __mul__(self, scalar):
        return Vector2d(self.x * scalar, self.y * scalar)

    def __str__(self):
        return '(%.2f, %.2f)' % (self.x, self.y)

    def __iter__(self):
        yield self.x
        yield self.y

    @staticmethod
    def distance(vect1, vect2):
        # The actual distance is used when checking to see if a mouse is close enough to a node so the distance is square rooted
        # This won't affect the comparison anyway since the distance methods that do return the distance without square rooting it
        # Are only compared with other distance methods that work in 3d. This is only 2d.
        return math.hypot(vect1.x - vect2.x, vect1.y - vect2.y)


# Creates the Verlet Class, used in the physics engine
# Recommended to read that first (PhysEng.py)
class Verlet(Vector3d):
    def __init__(self, *values):
        assert (len(values) in [4, 5] and values[3] in [1, 0]), "Unexpected arguments"
        super(Verlet, self).__init__(*values[:3])

        # w = 1 Means that the object will move normally
        # w = 0 Means that the object will be 'pinned' and only move if the user moves it.
        self.w = values[3]

        # Allows the old pos to be set manually, allowing for the node to have a defined starting velocity
        try:
            self.old = Vector3d(*values[4])

        # Default. No starting velocity
        except:
            self.old = Vector3d(*values[:3])

    def __str__(self):
        return '(%.2f, %.2f, %.2f)' % (self.x, self.y, self.z)


