from Wireframe import *
import pygame
from Vectors import *
import math
from Events import *
import Constants
from math import sin, cos
from statistics import median

# Defines some colours used by the renderer
BLUE = (0, 55, 220)
RED = (220, 55, 0)
AQUA = (0, 190, 255)
ORANGE = (255, 180, 0)

def getall(classes, *vars):
    # Returns a list of every value of a attribute on a list of classes
    # Also allows for multiple attributes to be passed in
    total = []
    for clas in classes:
        for var in vars:
            total.extend(getattr(clas, var))
    return total

# The screen class. Keeps a list of wireframes, then returns information about those wireframes
# Like closest node to a point, closest 3d point to a point, etc
# Can render its wireframes as well

class Screen:
    def __init__(self, camera, display, box):
        self.camera = camera
        self.display = display
        self.box = box

        # The box that shows the boundaries of the simulation.
        # Cannot be interacted with. Just renders
        self.renderbox = Wireframe()
        self.renderbox.addNodes(*[Verlet(x, y, z, 0) for x in [0, box.x] for y in [0, box.y] for z in [0, box.z]])

        self.extras = [] # Extra things that can be added to render (Used in the game to show what items are being selected)

        # The grid that shows where nodes can be created
        self.grid = Wireframe()
        self.grid.addNodes(*[Verlet(x, y, z, 0) for x in range(0, box.x + 1, Constants.REND_PREC) for y in range(0, box.y + 1, Constants.REND_PREC) for z in range(0, box.z + 1, Constants.REND_PREC)])

        self.items = []

    def additem(self, *items):
        for item in items:
            self.items.append(item)

    def closest(self, point):
        # Returns the closest node to the point.
        # If no node is found within 10 pixel, False is returned
        highest = [10, False]
        for item in self.items:
            for node in item:

                # Gets the 2d representation of the node
                proj = self.camera.renderP(node)
                if not proj:
                    continue

                # Gets the distance from the 2d representation of the node and the point passed to the method
                # Then checks to see if its closest node found to the point
                dist = Vector2d.distance(proj, point)
                if dist < highest[0]:
                    highest = [dist, node]

        return highest[1]


    def get3dPoint(self, point, bearing):
        # Returns a 3d point, given a 2d point.
        # Does this by finding the closest 3d point when projected to a 2d point
        # It is way too computationally expensive to check every node possible

        # If a bearing is present, 3d points are chosen around the bearing.
        if bearing:
            # Works in the same way as the above method
            highest = [False, False]
            for node in [Vector3d(x, y, z) for x in range(int(bearing.x - 1), int(bearing.x + 2)) for y in range(int(bearing.y - 1), int(bearing.y + 2)) for z in range(int(bearing.z - 1), int(bearing.z + 2))]:
                proj = self.camera.renderP(node)
                dist = Vector2d.distance(proj, point)
                if not highest[0] or dist < highest[0]:
                    highest = [dist, node]

            if highest[1] == False:
                return False
            else:
                return highest[1]

        # Without a bearing the 3d points are chosen by going through the grid
        else:
            # Works in the same way as the above method
            highest = [False, False]
            for node in self.grid:
                proj = self.camera.renderP(node)
                if not proj:
                    continue
                dist = Vector2d.distance(proj, point)
                if not highest[0] or dist < highest[0]:
                    highest = [dist, node]

            if highest[1] == False:
                return False
            else:
                return highest[1]

    def render(self, grid, others):
        # Renders all the items to the screen

        # Creates a list of all items that need to be rendered
        allitems = getall([self.renderbox], 'nodes', 'edges', 'faces')
        allitems .extend(getall(self.items, 'nodes', 'edges', 'faces'))
        allitems.extend(self.extras)
        allitems.extend(others)

        dup = list(allitems) # duplicates items, to seperate the items from the grid that is going to be added to the orginal list
        if grid:
            gridnodes = getall([self.grid], 'nodes')
            allitems.extend(gridnodes)

        for item in sorted(allitems, key=lambda x:x.distance(self.camera.pos), reverse = True):

            # If the item is a node
            if isinstance(item, Vectors.Vector3d):
                point = self.camera.renderP(item)
                try:
                    # Checks to see if the node is part of the grid
                    if any(id(item) == id(node) for node in self.grid):

                        # If the node is part of the grid, it only draws the node if
                        # there is no other node in that position
                        for node in dup:
                            if isinstance(node, Vectors.Vector3d):
                                if (item.x, item.y, item.z) == (node.x, node.y, node.z):
                                    break
                        else:
                            pygame.draw.circle(self.display, AQUA, (int(point.x), int(point.y)), 3)
                    else:
                        # Makes the node orange if its part of the extras list
                        if item in self.extras:
                            pygame.draw.circle(self.display, ORANGE, (int(point.x), int(point.y)), 4)

                        # Makes the node red if its pinned
                        elif item.w == 0:
                            pygame.draw.circle(self.display, RED, (int(point.x), int(point.y)), 4)

                        # Otherwise draws the node in a aqua colour
                        else:
                            pygame.draw.circle(self.display, BLUE, (int(point.x), int(point.y)), 4)
                except:
                    pass

            # If the item is an edge
            elif isinstance(item, Edge):
                # projects each node from the edge, then draws a line connecting them
                values = [self.camera.renderP(node) for node in item]
                try:
                    pygame.draw.line(self.display, item.colour, *[(int(point.x), int(point.y)) for point in values])
                except:
                    pass

            # If the item is a face
            elif isinstance(item, Face):
                # same process as with the edges
                values = [self.camera.renderP(node) for node in item]
                try:
                    pygame.draw.polygon(self.display, item.colour, [(int(point.x), int(point.y)) for point in values])
                except:
                    pass

# The camera class.
# This class was also designed to be versatile. Given a point, it performs a perspective projection on that point
# then returns the new point

# It also can be moved around and turned around. It is designed to know nothing about the rest of the game
class Camera(object):
    def __init__(self, fov, pos, display):

        self.focal = 1

        self.pos = pos                  # The position of the camera
        self.theta = Vector3d(0, 0, 0)  # The angle the camera is looking

        self.display = display
        self.ez = 1 / math.tan(math.radians(fov) / 2)   # distance from the display surface (the surface that points get
                                                        # rendered too) and the viewer. Given this value the fov in degrees
                                                        # Can be worked out.

        self.woffset = self.display.get_width() / 2
        self.hoffset = self.display.get_height() / 2

    @property
    def fov(self):
        return 2 * math.atan(1 / self.ez)

    @property
    def look(self):
        raise ValueError('Look is only used as a setter')

    @fov.setter
    def fov(self, fov):
        self.ez = 1 / math.tan(fov / 2)

    @look.setter
    def look(self, values):
        # changes the direction the camera is facing
        self.theta.x += values[0]
        self.theta.y += values[1]
        self.theta.z += values[2]

        # Stops the camera from looking up too far to loop around, and looking down to far to also loop around
        self.theta.x = median([- math.pi / 2, self.theta.x, math.pi])

        # Allows the camera to turn all the way around, by making the theta.y value loop over when it goes too far
        if self.theta.y < -math.pi:
            self.theta.y = math.pi
        if self.theta.y > math.pi:
            self.theta.y = -math.pi

    def renderP(self, point):
        # Takes a 3d vector, then projects it onto a 2d surface and returns the vector
        try:
            # follows the algorithm shown here https://en.wikipedia.org/wiki/3D_projection
            relative = point - self.pos
            rotated = Vector3d(0, 0, 0)

            # Gets the relative z position of the node
            rotated.z = cos(self.theta.x) * (cos(self.theta.y) * relative.z + sin(self.theta.y) * (sin(self.theta.z) * relative.y + cos(self.theta.z) * relative.x)) - sin(self.theta.x) * (cos(self.theta.z) * relative.y - sin(self.theta.z) * relative.x)

            # if the relative z position is less than zero, forces a return false
            # (since the node is behind the camera and cannot be viewed)
            if rotated.z <= 0:
                raise ValueError

            # Gets the relative x and y position
            rotated.x = cos(self.theta.y) * (sin(self.theta.z) * relative.y + cos(self.theta.z) * relative.x) - sin(self.theta.y) * relative.z
            rotated.y = sin(self.theta.x) * (cos(self.theta.y) * relative.z + sin(self.theta.y) * (sin(self.theta.z) * relative.y + cos(self.theta.z) * relative.x)) + cos(self.theta.x) * (cos(self.theta.z) * relative.y - sin(self.theta.z) * relative.x)

            # Projects the new point onto a 2d surface
            newx = (self.ez / rotated.z) * rotated.x * self.woffset + self.woffset
            newy = (self.ez / rotated.z) * rotated.y * self.hoffset + self.hoffset

            point = Vector2d(newx, newy)
            return point
        except:
            return False

    def move(self, move, strafe):
        # Moves the camera. move is how fast the camera should move forward (negative values move backwards)
        # strafe is how fast you camera should move to the right (negative values move the camera to the left)

        # Gets the direction the camera is facing, ignoring the y value.
        target = Vector3d(0, 0, 0)

        # Turns the direction into a x, z vector
        target.x = sin(self.theta.y) * cos(self.theta.x)
        target.z = cos(self.theta.y) * cos(self.theta.z)
        target.normalise()

        # Moves in the direction of the camera
        self.pos.add(target * move)

        # Moves side to side from the direction of the camera

        # Gets the crossproduct of the direction the camera is facing and a vector pointing up
        target.crossProduct(Vector3d(0, -1, 0))

        self.pos.add(target * strafe)