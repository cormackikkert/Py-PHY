from Vectors import *
from Events import *
from statistics import median
import Constants
import pygame


# This file holds a lot of the objects related to the GUI of the game

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

pygame.font.init()
font = pygame.font.Font(None, 36)

# This function draws text in the middle of a rect
def drawtext(surface, text, rect):
    textsurf = font.render(text, False, (255, 255, 255))
    # Gets the dimensions of the text
    values = getDimensions(text)

    # Places the surface in the middle of the rect
    surface.blit(textsurf, (rect.x + (rect.w - values[0]) / 2, rect.y + (rect.h - values[1]) / 2))

# Returns the width and height of a surface made created from text
def getDimensions(text):
    # Turns the text into a surface
    textsurf = font.render(text, False, (255, 255, 255))
    # Returns the width and height of that surface
    return textsurf.get_size()

# A rect super class
class Rect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    # Checks to see if a point is within itself (iself being a rect)
    def collidepoint(self, point):
        if self.x <= point.x < self.x + self.w and self.y <= point.y < self.y + self.h:
            return True
        return False

    def tuple(self):
        return eval(self.__str__())

    def __str__(self):
        return '({}, {}, {}, {})'.format(self.x, self.y, self.w, self.h)

# Creates the input box. Gets input from a user, then when they press enter,
# Executes the callback function with the text the user entered
class InputBox(Rect):
    @EventAdder
    def __init__(self, x, y, w, h, colour, func, prompt, display, **kwargs):
        super().__init__(x, y, w, h)
        self.colour = colour # The colour of the box
        self.func = func     # The callback function
        self.display = display
        self.prompt = prompt # The text that appears on the input Box, guiding the user, and telling them what to do
        self.text = ''
        self.layer = -3      # Uses a low layer so it is the first to recieve events

        # Variables that allow for the effect of holding down backspacing and deleting a lot of characters
        # I only decided to add the feature for the backspace key, since I can't think of why it would be needed
        # for other characters.
        self.timer = 0
        self.increment = False  # Represents if the backspace key is being held down

    def notify(self, event):
        if isinstance(event, MouseClick):
            return True
        if isinstance(event, KeyEvent):
            if event.action == 'P':
                if event.type == 'ENTER':
                    Constants.SOUND_KEYSTROKE.play()

                    # Calls the callback function with the text
                    self.func(self.text)
                    self.evManager.unregisterListener(self)

                elif event.type == 'BACKSPACE':
                    Constants.SOUND_KEYSTROKE.play()
                    self.text = self.text[:-1]

                    # Sets increment to True if the backspace was pressed.
                    # increment is only set to False if the backspace key was released
                    self.increment = True
                else:
                    if len(self.text) < 20:
                        # Adds whatever the user pressed into the text attribute
                        self.text += event.type
                        Constants.SOUND_KEYSTROKE.play()
                    else:
                        # If there are too many characters in the box, notify the player that he cannot type anything more
                        Constants.globalTimer.registerItem(TextBoxEvent.from_text(Vector2d(64, 64), 'Too many characters', self.display, evManager=self.evManager), 60)
                        Constants.SOUND_ERROR.play()

            else:
                # If the backspace key is released
                if event.type == 'BACKSPACE':
                    self.increment = False
                    # Resets the timer
                    self.timer = 0
            return True

        if isinstance(event, TickEvent):
            # Adds to the timer if the back space is being held
            # Caps at 30
            self.timer += self.increment and self.timer < 30
            if self.timer >= 30:
                if len(self.text) > 0:
                    # If the backspace key has been held down for 30 frames
                    # Continually deletes the last character from the text
                    self.text = self.text[:-1]
                    Constants.SOUND_KEYSTROKE.play()

        if isinstance(event, RenderEvent):
            # Draws the text box
            pygame.draw.rect(self.display, self.colour, self.tuple())
            lightcolour = (min(255, self.colour[0] * 1.1), min(255, self.colour[1] * 1.1), min(255, self.colour[2] * 1.1))
            pygame.draw.rect(self.display, lightcolour, (self.x + 10, self.y + 10, self.w - 20, 30))
            pygame.draw.rect(self.display, lightcolour, (self.x + 10, self.y + 50, self.w - 20, self.h - 60))
            drawtext(self.display, self.prompt, Rect(self.x + 10, self.y + 10, self.w - 20, 30))
            drawtext(self.display, self.text, Rect(self.x + 10, self.y + 50, self.w - 20, self.h - 60))

# Creates a coloured box
# Like a rect, but draws itself every frame and blocks mouse clicks
class ColouredBox(Rect):
    @EventAdder
    def __init__(self, x, y, w, h, colour, display, **kwargs):
        super().__init__(x, y, w, h)
        self.colour = colour
        self.display = display
        self.layer = -0.5

    def notify(self, event):
        if isinstance(event, MouseClick):
            # Blocks mouse clicks if the mouse is within the rect
            return self.collidepoint(Vector2d(*pygame.mouse.get_pos()))

        if isinstance(event, RenderEvent):
            # Allows the colour to be a tuple or a vector
            if isinstance(self.colour, tuple):
                pygame.draw.rect(self.display, self.colour, self.tuple())
            else:
                pygame.draw.rect(self.display, [self.colour.x, self.colour.y, self.colour.z], self.tuple())

# A text box. Like a normal box but displays text
class TextBoxEvent(Rect):
    @EventAdder
    def __init__(self, x, y, w, h, text, surface, **kwargs):
        super().__init__(x, y, w, h)
        self.layer = -1
        self.t = text
        self.surface = surface

    # Alternate constructor. Builds the smallest rect from the given pos that covers the text given
    @classmethod
    def from_text(cls, pos, text, surface, **kwargs):
        return cls(pos.x, pos.y, *getDimensions(text), text, surface, **kwargs)

    # Creates a text property. This allows for x.text = something
    # instead of x.setText(something)
    @property
    def text(self):
        return self.t

    @text.setter
    def text(self, text):
        # Updates the width and height of the rect if the text changes
        self.t = text
        dimens = getDimensions(text)
        self.w = dimens[0]
        self.h = dimens[1]

    def notify(self, event):
        if isinstance(event, MouseClick):
            # See the colouredBox notify method
            return self.collidepoint(Vector2d(*pygame.mouse.get_pos()))

        if isinstance(event, RenderEvent):
            self.render()

    def render(self):
        pygame.draw.rect(self.surface, Constants.GLOBAL_COLOUR_DARK.tuple(), self.tuple())
        drawtext(self.surface, self.text, self)


class Button(Rect):
    @EventAdder
    def __init__(self, text, func, display, hover = 1.1, **kwargs):
        # Allows the user to build the button from a rect or from a position
        if 'rect' in kwargs:
            rect = kwargs['rect']
        elif 'pos' in kwargs:
            pos = kwargs['pos']
            dimens = getDimensions(text)
            rect = Rect(pos.x, pos.y, dimens[0] + 2, dimens[1] + 2)

        super().__init__(rect.x, rect.y, rect.w, rect.h)

        self.text = text
        self.colour = (Constants.GLOBAL_COLOUR, Constants.GLOBAL_COLOUR_DARK)
        self.hover = hover     # The width and height is multiplied when the mouse is above the button. This is how much it is multiplied by
        self.display = display
        self.func = func       # The callback function
        self.state = 0         # 0 is normal. 1 is when the mouse is hovering over the button
        self.layer = -1

    def notify(self, event):
        if isinstance(event, MouseClick):
            if event.action == 'R':
                if self.collidepoint(Vector2d(*pygame.mouse.get_pos())):
                    self.func() # Executes the call back function on a mouse click
                    return True

        elif isinstance(event, TickEvent):
            mouseposition = Vector2d(*pygame.mouse.get_pos())
            # Changes the state, based on wether or not the mouse is hovering over the button
            if self.collidepoint(mouseposition):
                self.state = 1
            else:
                self.state = 0

        elif isinstance(event, RenderEvent):
            self.render()

    def render(self):
        rect = self.tuple()

        # Creates a bigger rect when the mouse is hovering over the button
        if self.state == 1:
            # multiplies the width and height by the hover attribute
            neww = rect[2] * self.hover
            newh = rect[3] * self.hover

            # repositions the x and y value so that the center of the new rect is at the same point
            # as the center of the original rect
            newx = rect[0] - (neww - rect[2]) / 2
            newy = rect[1] - (newh - rect[3]) / 2
            rect = (newx, newy, neww, newh)

        pygame.draw.rect(self.display, self.colour[self.state].tuple(), rect)
        drawtext(self.display, self.text, self)

# The scoller class.
# Creates a slider that can be moved up and down.
# Executes a callback function continually when the slider is being held
class Scroller(Rect):
    @EventAdder
    def __init__(self, x, y, h, values, func, display, **kwargs):
        super().__init__(x, y, 1, h)
        self.values = values

        # Creates the holder (the rectangle which moves up and down on the slider)
        # Size is proportionate to how tall the slider is
        width = self.h / 6
        height = width / 2
        self.holder = Rect(x - width // 2, y + h // 2 - height // 2, width, height)

        self.func = func
        self.display = display
        self.layer = -1.5
        self.state = 0 # 0 is normal. 1 means that the holder is being held by the mouse

        self.textbox = False # Used to store the textbox, if there is one.
        # The textbox just shows the value of the slider to the right of it, when it is being pressed

    def getValue(self):
        # Returns the value of the slider.
        # Gets the value by getting the relative position of the holder and the slider
        # then multiplying that by the range of values, then adding the lowest value
        maxy = self.y + self.holder.h / 2
        posy = self.holder.y + self.holder.h / 2
        miny = self.y + self.h + 1 - self.holder.h / 2

        # percent up the slider * range of values + lowest value
        return (posy - miny) / (maxy - miny) * (self.values[1] - self.values[0]) + self.values[0]

    def render(self):
        pygame.draw.line(self.display, (145, 195, 210), (self.x, self.y), (self.x, self.y + self.h), 3)
        pygame.draw.rect(self.display, (255, 0, 0), self.holder.tuple())

    def notify(self, event):
        if isinstance(event, MouseClick):
            if event.action == 'P':
                # If the holder was clicked on
                if self.holder.collidepoint(Vector2d(*pygame.mouse.get_pos())):
                    self.state = 1 # updates the state

                    # Adds a textbox. This textbox's text is continually updated to show the value of the slider
                    self.textbox = TextBoxEvent.from_text(Vector2d(self.holder.x + self.holder.w + 10, self.holder.y), '{0:.1f}'.format(self.getValue()), self.display, evManager=self.evManager, layer=-2)
                    return True

            elif event.action == 'R':
                self.state = 0 # updates state

                # removes the textbox created from the event manager (so it no longer display)
                self.evManager.unregisterListener(self.textbox)
                self.textbox = False

        elif isinstance(event, TickEvent):
            if self.state == 1:
                self.textbox.text = '{0:.1f}'.format(self.getValue()) # Updates the textbox's text

                # Moves the holder to the mouse's y value. Caps so it doesn't go off the slider
                self.holder.y = median([self.y, pygame.mouse.get_pos()[1], self.y + self.h - self.holder.h + 1])
                self.textbox.y = self.holder.y

                # Continually use the callback function.
                # Looks smoother than the callback function executing only when the holder is released.
                # (makes the game seem more responsive and more user friendly)
                self.func(self.getValue())

        elif isinstance(event, RenderEvent):
            self.render()
