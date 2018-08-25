import pygame
from Vectors import *
from Wireframe import *
import Renderer
import math
import PhysEng
import random
from Events import *
from Renderer import *
from gui import *
from Features import *
import pickle
from Constants import *
from Colour import *
from functools import partial

LOOKSPEED = 0.05 # How fast you turn when looking around
MOVESPEED = 1    # How fast you move

# Create window and pygame objects
pygame.display.set_caption('PHY PY')
pygame.display.set_icon(pygame.image.load('Circle.png'))
clock = pygame.time.Clock()
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

class Game:
    @EventAdder
    def __init__(self, box, wireframes, screen, **kwargs):
        fov = 60 # Fov used when created

        self.box = box
        self.state = 0 # 1 = simulating, 0 just displaying

        self.pos_adder = Vector3d(0, 0, 0)
        self.view_adder = Vector2d(0, 0)

        self.holder = False # Placeholder variable for the node the player can hold in state 1
        self.holdermem = 0  # Stores the w attribute of the node, so when the player lets go of the node it reverses
                            # back to its original value (since holding the node sets the attribute to 0)

        self.build = [] # Stores the nodes the player has selected
        self.facecolour = Vector3d(255, 255, 255) # Face colour used when spawned

        # Items that appear depending on the state
        self.stateitems = {0: [
            Button('PLAY', lambda: self.changestate(), gameDisplay, evManager=self.evManager, rect=Rect(620, 20, 160, 40)),
            Button('BUILD', lambda: self.builder(), gameDisplay, evManager=self.evManager, rect=Rect(620, 70, 160, 40)),
            Button('DESELECT', lambda: [SOUND_DESELECT.play(), self.build.clear()], gameDisplay, evManager=self.evManager, rect=Rect(620, 120, 160, 40)),
            Button('CLEAR', lambda: [SOUND_CLEAR.play(), self.wireframes[0].clear(), self.build.clear()], gameDisplay, evManager=self.evManager, rect=Rect(620, 170, 160, 40)),
            Button('SAVE', lambda: self.items.append(InputBox(180, 200, 440, 200, (255, 200, 0), self.save, 'Save file as:', gameDisplay, evManager=self.evManager)), gameDisplay, evManager=self.evManager, rect=Rect(610, 550, 60, 30)),
            Button('LOAD', lambda: self.items.append(InputBox(180, 200, 440, 200, (255, 200, 0), self.load, 'Load file:', gameDisplay, evManager=self.evManager)), gameDisplay, evManager=self.evManager, rect=Rect(680, 550, 70, 30)),
            Button('X', lambda: change_state(0), gameDisplay, evManager=self.evManager, rect=Rect(760, 550, 30, 30)),
            ColouredBox(600, 0, 200, 600, (60, 170, 210), gameDisplay, evManager=self.evManager, layer=-0.7)],
                           1: [
            ColouredBox(600, 0, 200, 600, (60, 170, 210), gameDisplay, evManager=self.evManager),
            Button('CREATE', lambda: self.changestate(), gameDisplay, evManager=self.evManager, rect=Rect(620, 20, 160, 40)),
            TextBoxEvent(650, 80, 100, 40, 'FOV', gameDisplay, evManager=self.evManager),
            Scroller(700, 130, 440, [40, 170], lambda x: setattr(self.camera, 'fov', math.radians(x)), gameDisplay, evManager=self.evManager),
            ColouredBox(640, 70, 120, 510, (130, 205, 235), gameDisplay, evManager=self.evManager, layer=-0.7)
                           ]}

        # Items that apear depending on how many items are selected
        self.builditems = {0:[],
                           1:[TextBoxEvent(620, 220, 160, 40, 'NODE', gameDisplay, evManager=self.evManager)],
                           2:[TextBoxEvent(620, 220, 160, 40, 'EDGE', gameDisplay, evManager=self.evManager)],
                           3:[
                               TextBoxEvent(620, 220, 160, 40, 'FACE', gameDisplay, evManager=self.evManager),
            ColouredBox(630, 280, 140, 50, self.facecolour, gameDisplay, evManager=self.evManager, layer=-0.9),
            ColouredBox(620, 270, 160, 270, (130, 205, 235), gameDisplay, evManager=self.evManager, layer=-0.8),
            Scroller(660, 340, 180, [0, 255], lambda x: setattr(self.facecolour, 'x', x), gameDisplay, evManager=self.evManager),
            Scroller(700, 340, 180, [0, 255], lambda x: setattr(self.facecolour, 'y', x), gameDisplay,evManager=self.evManager),
            Scroller(740, 340, 180, [0, 255], lambda x: setattr(self.facecolour, 'z', x), gameDisplay, evManager=self.evManager)
        ]}

        # Since creating an object automatically registers it to the event manager, we now go through
        # and unregister every object
        for key in self.builditems:
            for item in self.builditems[key]:
                self.evManager.unregisterListener(item)

        for item in self.stateitems[1 - self.state]:
            self.evManager.unregisterListener(item)

        self.items = [] # Stores the active objects
        self.items.extend(self.stateitems[self.state])

        self.wireframes = wireframes

        # keeps a duplicate of self.wireframes since the physics engine modifies wireframes (you dont want to originals to be changed)
        self.originals = wireframes

        # Create the objects the game uses
        self.camera = Camera(fov, Vector3d(box.x / 2, box.y / 2, -80), screen)
        self.screen = Screen(self.camera, screen, self.box)
        self.world = PhysEng.Engine([], 0.99, box, evManager=self.evManager)
        self.screen.additem(*wireframes)

    def run(self):
        # Moves the camera
        self.camera.move(self.pos_adder.x, self.pos_adder.y)
        self.camera.pos.y += self.pos_adder.z

        # Rotates the camera
        self.camera.look = (self.view_adder.x, self.view_adder.y, 0)

        if self.state == 1:
            if self.holder:
                # updates the 3d position the mouse is holding, using the current position as a bearing
                newpoint = self.screen.get3dPoint(Vector2d(*pygame.mouse.get_pos()), self.holder)
            else:
                newpoint = False

            # Simulates the world
            self.world.simulate(self.holder, newpoint)

    def save(self, text):
        # Saves the wireframe
        try:
            pickle.dump(self.wireframes[0], open(text, 'wb'))
        except:
            # Notifies the player that the file name to save was invalid.
            SOUND_ERROR.play()
            globalTimer.registerItem(
                TextBoxEvent.from_text(Vectors.Vector2d(64, 64), 'Name the file something else'.format(text), gameDisplay,
                                       evManager=self.evManager), 60)
        # Finds the input box, and unregisters it
        # Since only input boxes trigger this
        for item in self.items:
            if isinstance(item, InputBox):
                self.evManager.unregisterListener(item)
                self.items.remove(item)

    def load(self, text):
        try:
            # Loads wireframe
            self.wireframes[0] = pickle.load(open(text, 'rb'))
        except:
            # Notfies the player that the file doesnt exist if the game was unable to load the file
            SOUND_ERROR.play()
            globalTimer.registerItem(TextBoxEvent.from_text(Vectors.Vector2d(64, 64), 'The file {} does not exist'.format(text), gameDisplay, evManager=self.evManager), 60)
        else:
            # Deselects everything (self.screen.extras) stores the nodes that have been selected
            self.build = []
            self.screen.extras = []
            self.screen.items = self.wireframes # Sets the new items to the items just loaded

            # Unregisters textbox
            for item in self.items:
                if isinstance(item, InputBox):
                    self.evManager.unregisterListener(item)
                    self.items.remove(item)

            # Notfies player file was loaded
            globalTimer.registerItem(TextBoxEvent.from_text(Vectors.Vector2d(64, 64), '{} file loaded!'.format(text), gameDisplay, evManager=self.evManager) ,60)

    def changestate(self):
        # Unregisters items in the current state
        for item in self.stateitems[self.state]:
            self.evManager.unregisterListener(item)
            self.items.remove(item)

        if self.state == 0:
            # If the state is going to be changed into a simulation
            for key in self.builditems:

                # Removes all items that display depending on how many items are selected
                for item in self.builditems[key]:

                    # Exception handled since the item might not be active
                    try:
                        self.items.remove(item)
                        self.evManager.unregisterListener(item)
                    except:
                        pass

            # Duplicates items so that the originals don't get modified in the simulation
            dup = [wireframe.copy() for wireframe in self.originals]
            self.world.objects = dup
            self.screen.items = dup
            self.camera.items = dup

            self.state = 1

        elif self.state == 1:
            #
            self.screen.items = self.wireframes
            self.camera.items = self.wireframes
            self.state = 0

        # Deselects everything
        self.build = []
        self.screen.extras = []

        # Registers new items associated with the new state
        for item in self.stateitems[self.state]:
            self.items.append(item)
            self.evManager.registerListener(item)

    def builder(self):
        # Builds an item.
        # The type of item depends on how many nodes are selected


        if len(self.build) == 1:
            # Creates a node
            self.evManager.push(BuildEvent('NODE'))
            SOUND_BUILD.play()
            self.wireframes[0].addNodes(*self.build)

            # Notifies player a node has been created
            globalTimer.registerItem(TextBoxEvent.from_text(Vectors.Vector2d(64, 64), 'Node built', gameDisplay,evManager=self.evManager), 60)


        elif len(self.build) == 2:
            # Creates an edge.

            self.evManager.push(BuildEvent('EDGE'))
            SOUND_BUILD.play()

            # Creates the nodes
            self.wireframes[0].addNodes(*self.build)

            # Creates the edge, connecting the nodes. Index is set to False, so that the nodes are chosen if they
            # are in the same position. This is done as you don't want nodes to be in the same spot as others
            # and .addNodes stops this from happening. So if you index the list the node might not be added and you
            # could have unexpected results
            self.wireframes[0].addEdges([self.build[0], self.build[1]], index=False)
            globalTimer.registerItem(TextBoxEvent.from_text(Vectors.Vector2d(64, 64), 'Edge built', gameDisplay, evManager=self.evManager), 60)

        elif len(self.build) == 3:
            # Same process as with edges
            self.evManager.push(BuildEvent('FACE'))
            SOUND_BUILD.play()
            self.wireframes[0].addNodes(*self.build)
            self.wireframes[0].addEdges([self.build[0], self.build[1]], [self.build[1], self.build[2]], [self.build[2], self.build[0]], index = False)
            self.wireframes[0].addFaces([self.build[0], self.build[1], self.build[2]], index=False, colour=self.facecolour)
            globalTimer.registerItem(TextBoxEvent.from_text(Vectors.Vector2d(64, 64), 'Face built', gameDisplay, evManager=self.evManager), 60)

        else:
            # Produces an error if nothing was selected.
            # The game stops you from selecting more than 3 items so this will only be triggered if nothing is selected
            SOUND_ERROR.play()
            globalTimer.registerItem(TextBoxEvent.from_text(Vectors.Vector2d(64, 64), 'Nothing selected', gameDisplay, evManager=self.evManager), 60)

        # Deselects everything
        self.build = []
        self.screen.extras = []

    def register(self):
        # Registers all items associated with current state
        for item in self.stateitems[self.state]:
            self.evManager.registerListener(item)

    def notify(self, event):
        if isinstance(event, KeyEvent):
            if event.action == 'P':

                # Modifies the pos_adder vector based on what keys are pressed.
                # Since the camera moves every frame based on the vector, the values are modified
                # They are set to movespeed on a key press, and 0 on a key release

                if event.type == 'W':
                    self.pos_adder.x = MOVESPEED
                elif event.type == 'A':
                    self.pos_adder.y = -MOVESPEED
                elif event.type == 'S':
                    self.pos_adder.x = -MOVESPEED
                elif event.type == 'D':
                    self.pos_adder.y = MOVESPEED
                elif event.type == 'Q':
                    self.pos_adder.z = -MOVESPEED
                elif event.type == 'E':
                    self.pos_adder.z = MOVESPEED
                elif event.type == 'LEFT':
                    self.view_adder.y = -LOOKSPEED
                elif event.type == 'RIGHT':
                    self.view_adder.y = LOOKSPEED
                elif event.type == 'UP':
                    self.view_adder.x = LOOKSPEED
                elif event.type == 'DOWN':
                    self.view_adder.x = -LOOKSPEED

            elif event.action == 'R':

                # The reasoning behind this is explained above
                if event.type == 'W':
                    self.pos_adder.x = 0
                elif event.type == 'A':
                    self.pos_adder.y = 0
                elif event.type == 'S':
                    self.pos_adder.x = 0
                elif event.type == 'D':
                    self.pos_adder.y = 0
                elif event.type == 'Q':
                    self.pos_adder.z = 0
                elif event.type == 'E':
                    self.pos_adder.z = 0
                elif event.type == 'LEFT':
                    self.view_adder.y = 0
                elif event.type == 'RIGHT':
                    self.view_adder.y = 0
                elif event.type == 'UP':
                    self.view_adder.x = 0
                elif event.type == 'DOWN':
                    self.view_adder.x = 0

        elif isinstance(event, TickEvent):
            self.run()

            # Lets go of a node the player is holding if the x position of the mouse
            # enters into the side bar
            if pygame.mouse.get_pos()[0] >= 600:
                if self.holder:
                    self.holder.w = self.holdermem
                    self.holder = False

        elif isinstance(event, RenderEvent):
            # Renders grid if the state is equal to 0
            # Draws the nodes that the player has selected
            self.screen.render(self.state == 0, self.build)

        elif isinstance(event, MouseClick):
            # Game is in simulation mode
            if self.state == 1:
                if event.type == 'LEFT':
                    # Left click pressed
                    if event.action == 'P':
                        # Sees if there is a node close the position the mouse clicked on
                        self.holder = self.screen.closest(Vector2d(*pygame.mouse.get_pos()))
                        if self.holder:
                            # If there is, stores the w attribute
                            self.holdermem = self.holder.w

                            # Remembers what the w attribute was, so that it can be set to it's original value
                            # when the mouse is released
                            self.holder.w = 0

                    # Left click released
                    elif event.action == 'R':
                        # If the mouse was holding a node
                        if self.holder:
                            # Sets the w attribute of the node to it's original value
                            self.holder.w = self.holdermem

                            self.holder = False
            else:
                if event.type == 'LEFT':

                    # Left release click event
                    if event.action == 'R':

                        # Makes sure you can only select 3 items
                        if len(self.build) < 3:

                            # Unregister build items (since another item is being selected) so
                            # different items should be registered
                            for key in self.builditems:
                                for item in self.builditems[key]:
                                    try:
                                        self.items.remove(item)
                                        self.evManager.unregisterListener(item)
                                    except:
                                        pass

                            mousepos = Vector2d(*pygame.mouse.get_pos())

                            # Checks to see if there is a node close to where the user clicked
                            pos3d = self.screen.closest(mousepos)
                            if not pos3d:
                                # If there was no node close to the mouse, creates a new one
                                # No bearing is specified so that the point is snapped to the grid
                                pos3d = self.screen.get3dPoint(mousepos, False)
                                pos3d = Verlet(pos3d.x, pos3d.y, pos3d.z, 1)

                            # If a node already built was selected
                            if pos3d not in self.build:
                                self.build.append(pos3d)
                                self.screen.extras = self.build

                            # Add all items associated with the object to be built
                            for item in self.builditems[len(self.build)]:
                                self.items.append(item)
                                self.evManager.registerListener(item)

                            SOUND_SELECT.play()

                        # More than 3 items are selected
                        else:
                            SOUND_ERROR.play()

                if event.type == 'RIGHT':
                    # Right release click event
                    if event.action == 'R':
                        # Toggles the w attribute if a node was found near the mouse
                        pos = self.screen.closest(Vector2d(*pygame.mouse.get_pos()))
                        if isinstance(pos, Vector3d):
                            pos.w = 1 - pos.w

# Creates box wireframe
box = Vector3d(100, 100, 100)
boxframe = Wireframe()
boxframe.addNodes(Vector3d(0, 0, 0), Vector3d(0, 0, box.z), Vector3d(0, box.y, 0),
                  Vector3d(0, box.y, box.z), Vector3d(box.x, 0, 0), Vector3d(box.x, 0, box.z),
                  Vector3d(box.x, box.y, 0), Vector3d(box.x, box.y, box.z))
boxframe.addEdges([0, 1], [0, 2], [0, 4], [3, 1], [3, 2], [3, 7], [7, 5], [7, 6], [2, 6], [5, 1], [5, 4], [6, 4])

# Global states
'''
    0 = MENU
    1 = GAME
    2 = ACHIEVEMENTS
'''

# Creates the colour udpater
updater = ColourUpdater(evManager=Controller)

# Defines the different items for each state
STATE_ITEMS = {0: [TextBoxEvent(60, 100, 400, 100, 'PHY PY: a physics simulator', gameDisplay, evManager=Controller),
                   Button('EXIT GAME', lambda: globalAchievements.save() or exit(), gameDisplay, evManager=Controller, rect=Rect(60, 430, 270, 100)),
                   Scroller(400, 250, 280, [0, 1], lambda x: [sound.set_volume(x) for sound in Constants.ALL_SOUNDS], gameDisplay, evManager=Controller),
                   TextBoxEvent(340, 210, 120, 30, 'SOUND', gameDisplay, evManager=Controller, layer=-0.9),
                   KeyboardController(evManager=Controller),
                   Maker(gameDisplay, evManager=Controller)],
               1: [Game(box, [Wireframe()], gameDisplay, evManager=Controller),
                   KeyboardController(evManager=Controller)],
               2: [TextBoxEvent(60, 100, 310, 100, 'Achievements', gameDisplay, evManager=Controller),
                   KeyboardController(evManager=Controller)]}

def change_state(newstate):
    global GAME_STATE
    global STATE_ITEMS

    # Stores items to delete
    temp = []

    # Removes items. Keeps items of certain types in certain states
    for item in Controller.listeners:

        # Keeps the Timer, Achievement and Colour Updater objects
        if not isinstance(item, Timer) and not isinstance(item, Achievements) and not isinstance(item, ColourUpdater):

            # Keeps circle toy items if the state is changing to the menu screen or achievement screen
            if not ((isinstance(item, CircleToy) or (isinstance(item, Maker))) and newstate in [0, 2]):
                temp.append(item)

    # Removes items
    for item in temp:
        Controller.unregisterListener(item)

    # Adds new items
    for item in STATE_ITEMS[newstate]:
        Controller.registerListener(item)

    # Registers the achievement boxes if the state is changed to the achievement screen
    if newstate == 2:
        globalAchievements.registerBoxes()

    GAME_STATE = newstate

# Has to add stuff to STATE_ITEMS here since these use the change_state function (which uses the STATE_ITEMS list
STATE_ITEMS[0].append(Button('PLAY GAME', partial(change_state, 1), gameDisplay, evManager=Controller, rect=Rect(60, 210, 270, 100)))
STATE_ITEMS[0].append(Button('ACHIEVEMENTS', partial(change_state, 2), gameDisplay, evManager=Controller, rect=Rect(60, 320, 270, 100)))
STATE_ITEMS[2].append(Button('BACK', partial(change_state, 0), gameDisplay, evManager=Controller, rect=Rect(380, 100, 150, 100)))

# Sets the state
change_state(0)

# Game loop
while True:
    # Pushes events so that objects registered react
    Controller.push(TickEvent())
    Controller.push(RenderEvent())

    pygame.display.update()
    clock.tick(60)
    gameDisplay.fill((0, 0, 0))
