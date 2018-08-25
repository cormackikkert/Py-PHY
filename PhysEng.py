import Wireframe
import Vectors
import statistics
import pygame
from Events import *
from Constants import *

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# The engine for the game
# Uses Verlet integration
# A points last position and current position is stored
# Velocity for a point is retrieved by getting the vector from the last position to the current position

# This class was designed to be versatile
# Therefore all it does is apply physics to the objects it has, and nothing else (doesnt render the objects or anything)
# It is designed to know nothing about the rest of the game
class Engine:
    # Event handler is only used, as this pushes events that the achievement objects takes care off.
    @EventAdder
    def __init__(self, objects, friction, box, **kwargs):
        self.grav = Constants.PHY_GRAV_3D
        self.friction = friction
        self.box = box
        self.objects = objects

    def additem(self, *objects):
        for object in objects:
            assert isinstance(object, Wireframe.Wireframe), 'Unexpected type'
            self.objects.append(object)

    def simulate(self, point, holder):
        # Moves a point to the holder position if point and holder arn't False
        # This is used by the game when the player clicks on a node
        if point and holder:
            point.x = holder.x
            point.y = holder.y
            point.z = holder.z

        # Performs calculations on all the points the engine has stored
        self.movepoints()

        # Continually updates the stick and does collisions.
        # Higher precision = more realistic physics.
        # Lower precision = less realistic and more jelly like.

        # It is more realistic as every time you change the pos of the two edges nodes it can stuff up other edges that
        # those nodes might be connected to making it less realistic.
        #  (If you want to see this change the precision to 1 and load file fabric and play with it. Then compare with the precision at 10)
        # Since the movesticks method moves the nodes it puts the points back inside the box if the movesticks pushed them out
        for i in range(Constants.PHY_PRECISION):
            self.movesticks()
            self.constrainPoints()

    def constrainPoints(self):
        # Checks to see if any points are outside of the box, and if so, moves them back in
        for object in self.objects:
            for point in object:

                # This vector is only used if the node is outside the box
                # If the node is outside the box then it is used to set the
                # old position in such a way where the next frame will get
                # the nodes velocity to be bouncing off the wall
                velocity = (point - point.old) * PHY_BOUNCE
                collide = False

                # Checks to see if the the nodes x coordinate is outside the box
                if not 0 <= point.x <= self.box.x:
                    # Sets the x coordinate to the edge of the box, that the node passed
                    point.x = statistics.median([0, point.x, self.box.x])
                    # Sets the old x to the edge of the box, plus the veloctity, so the next frame it goes away from the wall
                    # (Since the velocity is calculated by getting the vector from the old pos to the new pos)
                    point.old.x = point.x + velocity.x
                    collide = True

                if not 0 <= point.y <= self.box.y:
                    point.y = statistics.median([0, point.y, self.box.y])
                    point.old.y = point.y + velocity.y
                    collide = True

                if not 0 <= point.z <= self.box.z:
                    point.z = statistics.median([0, point.z, self.box.z])
                    point.old.z = point.z + velocity.z
                    collide = True

                # If a collision did occur
                if collide:

                    # Sends a collision event to the event Manager, with the speed of the collision
                    self.evManager.push(CollideEvent(velocity.length()))

                    if velocity.length() > 1:
                        # Plays a thump sound, with the volume proportionate to the collision speed
                        volume = velocity.length() / 10
                        pygame.mixer.music.load(SOUND_FILE_THUMP)
                        pygame.mixer.music.set_volume(volume)
                        pygame.mixer.music.play(0)


    # Loops through every point and moves it
    def movepoints(self):
        for object in self.objects:
            for point in object:
                # Gets the vector from the old pos to the new pos
                # Multiplies it by the friction value to act as air resistance and friction
                velocity = (point - point.old) * self.friction
                self.evManager.push(MoveEvent(velocity.length()))
                # Sets the new old position the current new position
                point.old = Vectors.Vector3d(*point.list())

                # Gets the new position. Adds the gravity vector and mulplies by the nodes w value
                # A W value of 1 means that the point is normal and acts normally
                # A W value of 0 means that the point is 'pinned' and can't move
                newposition = point + (velocity + self.grav) * point.w

                # Sets the new node position
                point.x = newposition.x
                point.y = newposition.y
                point.z = newposition.z

    # Loops through every edge and moves the edges nodes around so they arn't too close or too far away
    def movesticks(self):
        for object in self.objects:
            for edge in object.edges:
                # Gets the difference from the ideal distance between nodes and the actual distance between nodes
                rel = edge.first - edge.second
                distance = rel.length()

                # Negative means the points are too far awy, Positive means they are too close
                difference = edge.length - distance

                # Gets the percent of the distance each node has to move for them to be edge.length away
                try:
                    percent = difference / distance / 2
                except:
                    percent = 0.5

                # Gets the distance each node has to move
                offset = rel * percent

                # Moves each node into place. Multiplies by the w value so that "pinned" points don't move
                # While this means that a node will only move half the distance required if the other node is pinned,
                # this calculation happens Constants.PHY_PRECISION times, so its gets closer every calculation
                edge.first.add(offset * edge.first.w)
                edge.second.sub(offset * edge.second.w)

    def notify(self, event):
        pass

