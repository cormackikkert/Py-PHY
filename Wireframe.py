import Vectors
import copy
import math
import random

# Gets the rough distance between a wireframe and a position
def wireDist(item, position):
    assert isinstance(item, Wireframe), 'Must be Wireframe type'
    centre = item.findCentre()
    return math.sqrt((centre.x - position.x) ** 2 +
                     (centre.y - position.y) ** 2 +
                     (centre.z - position.z) ** 2)


# The face class, one of the building blocks of a wireframe
# It is a triangle that connects 3 nodes
class Face:
    def __init__(self, first, second, third, colour=False):
        # Defines the nodes that make up the face
        self.first  = first
        self.second = second
        self.third  = third

        # Uses a default colour if no colour is provided
        self.colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) if not colour else colour.tuple()

    # Returns the distance between a face and a node
    # since this will only be used as a comparison, it doesnt sqrt the distance to save computing power
    def distance(self, point):
        return (sum(node.x for node in self) / 3 - point.x) ** 2 + \
               (sum(node.y for node in self) / 3 - point.y) ** 2 + \
               (sum(node.z for node in self) / 3 - point.z) ** 2

    def __iter__(self):
        yield self.first
        yield self.second
        yield self.third

    def __str__(self):
        return self.first.__str__() + ' ' + self.second.__str__() + ' ' + self.third.__str__()

# One of the other 3 building blocks of a wireframe
# Connects two nodes together
class Edge:
    def __init__(self, first, second, colour=False):
        self.first = first
        self.second = second
        self.colour = (0, 190, 255) if not colour else colour

    def distance(self, point):
        return (sum(node.x for node in self) / 2 - point.x) ** 2 + \
               (sum(node.y for node in self) / 2 - point.y) ** 2 + \
               (sum(node.z for node in self) / 2 - point.z) ** 2

    def __iter__(self):
        yield self.first
        yield self.second

    def __str__(self):
        return str(self.first) + ' ' + str(self.second)

# The stick class is used by the physics engine.
# It has a length attribute that is used by the engine to figure out how much distance should be between nodes
class Stick(Edge):
    def __init__(self, first, second, colour=False, length=False):
        super(Stick, self).__init__(first, second, colour)
        if length:
            self.length = length
        else:
            self.length = math.sqrt((first.x - second.x) ** 2 + (first.y - second.y) ** 2 + (first.z - second.z) ** 2)

# The wireframe object is an object that stores a collection of nodes, edges and faces
class Wireframe:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.faces = []

    def addNodes(self, *nodes):
        # Goes through each node passed to the function
        for node in nodes:
            assert isinstance(node, Vectors.Vector3d), "must be Vector"\

            # Makes sure that there is not a node already in the position of the new node.
            if not any((node.x, node.y, node.z) == (point.x, point.y, point.z) for point in self.nodes):
                self.nodes.append(node)

    def addEdges(self, *edgelist, **kwargs):
        # Checks to see if an index argument was passed.
        # If index == True the edge's start and end nodes are retrieved by indexing the wireframe node list.
        # If index == False the edge's start and end nodes are retrieved by looking through the wireframe node list, and finding a node at a certain position
        if 'index' in kwargs and kwargs['index'] == False:
            for edge in edgelist:
                finals = []
                for ideal in edge:
                    # Searches for a node in the same position as one of the nodes in the edge (the variable)
                    for node in self.nodes:
                        if (ideal.x, ideal.y, ideal.z) == (node.x, node.y, node.z):
                            finals.append(node)
                            break

                # Tries to see if it's possible to build the edge
                try:
                    stick = Stick(*finals)
                except:
                    return

                # If it's possible to build the edge, it only adds it to the wireframe object if an edge like it does not already exist
                if not any((stick.first.x, stick.first.y, stick.first.z, stick.second.x, stick.second.y, stick.second.z) ==
                        (otherstick.first.x, otherstick.first.y, otherstick.first.z, otherstick.second.x, otherstick.second.y, otherstick.second.z)
                           for otherstick in self.edges):
                    self.edges.append(stick)
        else:
            # Creates an Edge using indicies from the edge (variable)
            for edge in edgelist:
                stick = Stick(self.nodes[edge[0]], self.nodes[edge[1]])
                # Makes sure the edge doesn't already exist
                if not any((stick.first.x, stick.first.y, stick.first.z, stick.second.x, stick.second.y,
                            stick.second.z) ==
                                   (otherstick.first.x, otherstick.first.y, otherstick.first.z, otherstick.second.x,
                                    otherstick.second.y, otherstick.second.z)
                           for otherstick in self.edges):
                    self.edges.append(stick)

    # Creates a face, using the same process as the edge, except with the face taking 3 variables
    def addFaces(self, *facelist, **kwargs):
        if 'index' in kwargs and kwargs['index'] == False:
            for face in facelist:
                finals = []
                for ideal in face:
                    for node in self.nodes:
                        if (ideal.x, ideal.y, ideal.z) == (node.x, node.y, node.z):
                            finals.append(node)
                            break
                try:
                    if 'colour' in kwargs:
                        face = Face(*finals, colour=kwargs['colour'].copy())
                    else:
                        face = Face(*finals)
                except:
                    pass

                if not any(face.__str__() == builtface.__str__() for builtface in self.faces):
                    self.faces.append(face)
        else:
            for face in facelist:
                if 'colour' in kwargs:
                    self.faces.append(Face(self.nodes[face[0]], self.nodes[face[1]], self.nodes[face[2]], colour=kwargs['colour'].copy()))
                else:
                    self.faces.append(Face(self.nodes[face[0]], self.nodes[face[1]], self.nodes[face[2]]))

    # Returns a rough approximation of the centre of the wireframe
    def findCentre(self):
        meanX = sum([node.x for node in self.nodes]) / len(self.nodes)
        meanY = sum([node.y for node in self.nodes]) / len(self.nodes)
        meanZ = sum([node.z for node in self.nodes]) / len(self.nodes)
        return Vectors.Vector3d(meanX, meanY, meanZ)

    # Returns a new copy of the wireframe
    # Deepcopies so it does not return a reference to its self
    def copy(self):
        return copy.deepcopy(self)

    # Deletes all data in the wireframe
    def clear(self):
        del self.nodes[:]
        del self.edges[:]
        del self.faces[:]

    def __iter__(self):
        for node in self.nodes:
            yield node

    def __str__(self):
        return '\n'.join(self)