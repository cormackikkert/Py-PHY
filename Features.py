from Events import *
from math import hypot, sin, cos
from Vectors import *
from random import randint, random
from statistics import median
from gui import *
import pickle
import Constants
pygame.init()

# This class, destroys objects after x amount of frames
# This is used for the notifications that display on the game
class Timer:
    @EventAdder
    def __init__(self, **kwargs):
        self.items = {}
        self.layer = -10

    def registerItem(self, item, timer):
        # Stores the item, and how many frames it should be active
        self.items[item] = timer
        self.evManager.registerListener(item)

    def notify(self, event):
        # Loops through every item every tick event, and checks if it should still be active.
        # If so it removes it from the event manager and from the timers dictionary of items
        if isinstance(event, TickEvent):
            toremove = []

            # Loops through every item
            for item in self.items:
                self.items[item] -= 1 # Reduces timer

                # Checks to see if it should be removed
                if self.items[item] < 0:
                    self.evManager.unregisterListener(item)
                    toremove.append(item)

            # Removes items that should be removed
            for item in toremove:
                 del self.items[item]

# A circle super class
class Circle:
    def __init__(self, pos, radius):
        self.pos = pos
        self.radius = radius

    def collidepoint(self, vect):
        # Checks to see if the vect is within the circle
        return hypot(self.pos.x - vect.x, self.pos.y - vect.y) < self.radius

# A circle, that when clicked on, explodes
class CircleToy(Circle):
    @EventAdder
    def __init__(self, pos, radius, display, maker, **kwargs):
        super().__init__(pos, radius)
        self.layer = -0.7 + random() # Makes the layer random so that bubbles and fireworks can be on different layers to
                                     # each other, making it look more realistic. Also stuffs up the event manager if they are
                                     # all on the same layer, as objects on top of others might not be the first to recieve events
                                     # depending on what item was registered first
        self.display = display
        self.colour = (randint(0, 255), randint(0, 255), randint(0, 255))
        self.maker = maker # Uses this to add its firework particles to the list.

    def notify(self, event):
        if isinstance(event, TickEvent):
            # Makes the CircleToy fall over time
            self.pos = self.pos + (Constants.PHY_GRAV_2D * 3)

            # Deactivates the entity if it goes off screen
            if self.pos.y - self.radius > Constants.SCREEN_SIZE[1]:
                self.evManager.unregisterListener(self)

        elif isinstance(event, MouseClick):
            if self.collidepoint(Vector2d(*pygame.mouse.get_pos())):
                # Makes sure it only reacts to left clicks, but still blocks clicks (so you can't click on something behind it)
                if not event.type == 'LEFT':
                    return True
                if not event.action == 'R':
                    return True


                self.evManager.push(PopEvent())
                self.evManager.unregisterListener(self)
                Constants.SOUND_FIREWORK.play()

                # Creates firework particles
                for i in range(Constants.FIREWORK_PARTS):
                    # Appends the new firework particle to the self's list, as without that, python decides to delete the object since nothing references it
                    self.maker.items.append(Firework(Vector2d(self.pos.x, self.pos.y), 10, Vector2d(cos(i), sin(i)) * randint(2, 5), self.colour, self.display, evManager=self.evManager, layer=self.layer))
                return True

        if isinstance(event, RenderEvent):
            pygame.draw.circle(self.display, self.colour, (int(self.pos.x), int(self.pos.y)), self.radius)

# A firework particle
class Firework(CircleToy):
    @EventAdder
    def __init__(self, pos, radius, velocity, colour, display, **kwargs):
        self.pos = pos
        self.radius = radius
        self.velocity = velocity
        self.display = display
        self.layer = -0.8
        self.maxlife = 120 # How many frames the firework wil live for
        self.lifetime = self.maxlife

        # Makes the colour slightly different from the colour that was passed in
        # Since alot of firework particles will be made it once it allows for
        # Each one to be slightly different
        self.colour = (median([0, colour[0] + randint(-50, 50), 255]), median([0, colour[1] + randint(-50, 50), 255]), median([0, colour[2] + randint(-50, 50), 255]))

    def notify(self, event):
        if isinstance(event, TickEvent):
            # Updates the velocity
            self.velocity = self.velocity + Constants.PHY_GRAV_2D

            # Updates the position
            self.pos = self.pos + self.velocity

            # Checks to see if the particle should still be active
            self.lifetime -= 1
            if self.lifetime < 0:
                self.evManager.unregisterListener(self)

        if isinstance(event, RenderEvent):
            # Draws the particle. Makes the size relative to the lifetime, so the particle gets smaller over time
            pygame.draw.circle(self.display, self.colour, (int(self.pos.x), int(self.pos.y)), int(self.radius*self.lifetime/self.maxlife))

# A class that constantly makes Circle Toys
class Maker:
    @EventAdder
    def __init__(self, display, **kwargs):
        self.display = display
        self.items = [] # A list of items created by the maker (including firework particles)
                        # Stops python from removing the item since there are no references to it

    def notify(self, event):
        if isinstance(event, TickEvent):
            # Has a random chance of making the Circle Toy, with approximately 2 every frame
            if randint(0, 30) == 0:
                radius = randint(30, 50) # Makes the radius random

                # Creates the CircleToy. Places it right above the screen so it doesn't look like it pops into existence
                self.items.append(CircleToy(Vector2d(randint(0, 800), -radius), radius, self.display, self, evManager = self.evManager))

# An achievement box. Stores data about the achievement
# And display information about the achievement when the mouse hovers over it
class AchievementBox(Rect):
    @EventAdder
    def __init__(self, x, y, w, h, text, unlock, values, surface, **kwargs):
        super().__init__(x, y, w, h)
        self.layer = -1
        self.text = text
        self.unlocked = unlock # Wether or not the achievement is unlocked
        self.values = values   # A list of values to store about the achievement, in the following format
                               # [current score, score to unlock the achievement, discription of how to unlock achievment]
        self.surface = surface
        self.textbox = False   # Variable used to store the text box, if it is created

    def notify(self, event):
        if isinstance(event, TickEvent):
            # If the mouse is above the box
            if self.collidepoint(Vector2d(*pygame.mouse.get_pos())):
                if not self.textbox:
                    # Creates a textbox if there isn't one.
                    # Shows details about achievement, from the values attribute
                    self.textbox = TextBoxEvent.from_text(Vector2d(pygame.mouse.get_pos()[0], self.y - 40), '{0:.2f} / {1} {2}'.format(*self.values), self.surface, evManager=self.evManager)
                else:
                    # Updates the position of the achievement if one is already created
                    self.textbox.x = pygame.mouse.get_pos()[0]

            # If the mouse is not hovering over the box
            else:
                # Deactivates the text box if there is one
                if self.textbox:
                    self.evManager.unregisterListener(self.textbox)
                    self.textbox = False

        if isinstance(event, MouseClick):
            # Stops a click from going through the object.
            # Checks the textbox, as there is only a textbox if the mouse is over the box
            if self.textbox:
                return True
        if isinstance(event, RenderEvent):
            # Chooses a different colour if the achievement is unlocked
            if self.unlocked:
                pygame.draw.rect(self.surface, (190, 0, 75), self.tuple())
            else:
                pygame.draw.rect(self.surface, (65, 100, 45), self.tuple())
            drawtext(self.surface, self.text, self)

# Class that keeps track of the achievements the player unlocks
# Updates the achievement boxes
class Achievements:
    @EventAdder
    def __init__(self, boxes, display, **kwargs):
        self.boxes = boxes
        self.display = display
        self.tracker = {}
        self.achievements = {}
        self.ideals = Constants.ACH_IDEALS  # Score the player needs to get to, to unlock the achievement
        for name in Constants.ACH_NAMES:
            self.tracker[name] = 0          # Score the player is currently on
            self.achievements[name] = False # Whether or not the player has unlocked the achievement

    def registerBoxes(self):
        for box in self.boxes:
            self.evManager.registerListener(box)

    def update(self):
        # Updates achievement boxes, given an achievements, and tracker attribute
        for type in Constants.ACH_IDEALS:
            # Finds the correct achievement box
            for box in self.boxes:
                if box.text == type:

                    # Updates achievement box values
                    box.unlocked = self.achievements[type]
                    box.values[0] = self.tracker[type]

    def save(self):
        # Saves the achievements and tracker attributes, to save achievement progress
        pickle.dump([self.tracker, self.achievements], open('SAVEDATA', 'wb'))
        return False

    def notify(self, event):
        if isinstance(event, PopEvent):
            # If a CircleToy was popped
            self.tracker['POPPER'] += 1

            # Find the correct achievment box
            for box in self.boxes:
                if box.text == 'POPPER':

                    # Update the boxes value
                    box.values[0] = self.tracker['POPPER']

                    # Check to see if the POPPER achievement was unlocked
                    if self.tracker['POPPER'] >= self.ideals['POPPER'] and not self.achievements['POPPER']:
                        box.unlocked = True
                        self.achievements['POPPER'] = True

                        # The textbox created has a lower layer value so that it appears over anything else that might be registered to the timer
                        Constants.globalTimer.registerItem(TextBoxEvent.from_text(Vector2d(64, 64), 'Achievement unlocked: POPPER', self.display, evManager=self.evManager), 60)

        # Same thing as above, but instead of adding to the tracker value, the tracker value is set to the speed
        # if the speed is greater than the tracker value
        # (since this keeps track of the highest speed a node has experienced
        if isinstance(event, MoveEvent):
            if event.velocity > self.tracker['SPEED']:
                for box in self.boxes:
                    if box.text == 'SPEED':
                        box.values[0] = event.velocity
                        if event.velocity >= self.ideals['SPEED'] and not self.achievements['SPEED']:
                            box.unlocked = True
                            self.achievements['SPEED'] = True
                            self.tracker['SPEED'] = event.velocity
                            Constants.globalTimer.registerItem(TextBoxEvent.from_text(Vector2d(64, 64), 'Achievement unlocked: SPEED', self.display, evManager=self.evManager, layer=-3), 60)


        # Same thing as above
        if isinstance(event, CollideEvent):
            if event.velocity > self.tracker['COLLIDER']:
                for box in self.boxes:
                    if box.text == 'COLLIDER':
                        box.values[0] = event.velocity
                        if event.velocity >= self.ideals['COLLIDER'] and not self.achievements['COLLIDER']:
                            box.unlocked = True
                            self.achievements['COLLIDER'] = True
                            self.tracker['COLLIDER'] = event.velocity
                            Constants.globalTimer.registerItem(
                                TextBoxEvent.from_text(Vector2d(64, 64), 'Achievement unlocked: COLLIDER', self.display,
                                                       evManager=self.evManager, layer=-3), 60)
        # Same thing as the POPPER checker
        if isinstance(event, BuildEvent):
            if event.type == 'NODE':
                self.tracker['NODER'] += 1
                for box in self.boxes:
                    if box.text == 'NODER':
                        box.values[0] = self.tracker['NODER']
                        if self.tracker['NODER'] >= self.ideals['NODER'] and not self.achievements['NODER']:
                            box.unlocked = True
                            self.achievements['NODER'] = True
                            Constants.globalTimer.registerItem(
                                TextBoxEvent.from_text(Vector2d(64, 64), 'Achievement unlocked: NODER', self.display,
                                                       evManager=self.evManager, layer=-3), 60)

            if event.type == 'EDGE':
                self.tracker['EDGER'] += 1
                for box in self.boxes:
                    if box.text == 'EDGER':
                        box.values[0] = self.tracker['EDGER']
                        if self.tracker['EDGER'] >= self.ideals['EDGER'] and not self.achievements['EDGER']:
                            box.unlocked = True
                            self.achievements['EDGER'] = True
                            Constants.globalTimer.registerItem(
                                TextBoxEvent.from_text(Vector2d(64, 64), 'Achievement unlocked: EDGER', self.display,
                                                       evManager=self.evManager, layer=-3), 60)

            if event.type == 'FACE':
                self.tracker['FACER'] += 1
                for box in self.boxes:
                    if box.text == 'FACER':
                        box.values[0] = self.tracker['FACER']
                        if self.tracker['FACER'] >= self.ideals['FACER'] and not self.achievements['FACER']:
                            box.unlocked = True
                            self.achievements['FACER'] = True
                            Constants.globalTimer.registerItem(
                                TextBoxEvent.from_text(Vector2d(64, 64), 'Achievement unlocked: FACER', self.display,
                                                       evManager=self.evManager, layer=-3), 60)
