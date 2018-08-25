import pygame
from Features import *
from Events import *
from Vectors import *
import pickle

# Initialise the pygame and mixer modul
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# Create the screen. Uses a double buffer to prevent tearing
SCREEN_SIZE = (800, 600)
gameDisplay = pygame.display.set_mode(SCREEN_SIZE, pygame.DOUBLEBUF)

# Creates global variables
Controller = EventManager()
globalTimer = Timer(evManager=Controller)

# Create achievement names, and the score required to unlock the achievement
# The class "Achievements" knows what to do with this
ACH_NAMES = ['POPPER', 'SPEED', 'COLLIDER', 'NODER', 'EDGER', 'FACER']

# Might want to change these values, so its quicker to unlock the achievement and make sure it works.
ACH_IDEALS = {
    'POPPER': 50,
    'SPEED': 13,
    'COLLIDER': 10,
    'NODER': 20,
    'EDGER': 30,
    'FACER': 40
}

# Creates the achievement boxes that will display on the achievement screen
AchievementBoxes = [AchievementBox(60, 250, 150, 100, 'POPPER', False, [0, ACH_IDEALS['POPPER'], 'Ballons popped'], gameDisplay, evManager=Controller),
                    AchievementBox(220, 250, 150, 100, 'SPEED', False, [0, ACH_IDEALS['SPEED'], 'Maxiumum speed reached'], gameDisplay, evManager=Controller),
                    AchievementBox(380, 250, 150, 100, 'COLLIDER', False, [0, ACH_IDEALS['COLLIDER'], 'Maxiumum collision speed'], gameDisplay, evManager=Controller),
                    AchievementBox(60, 400, 150, 100, 'NODER', False, [0, ACH_IDEALS['NODER'], 'Nodes built'], gameDisplay, evManager=Controller),
                    AchievementBox(220, 400, 150, 100, 'EDGER', False, [0, ACH_IDEALS['EDGER'], 'Edges built'], gameDisplay, evManager=Controller),
                    AchievementBox(380, 400, 150, 100, 'FACER', False, [0, ACH_IDEALS['FACER'], 'Faces built'], gameDisplay, evManager=Controller)
                    ]

# Creates the achievement tracker. Keeps track on the progress the player makes
globalAchievements = Achievements(AchievementBoxes, gameDisplay, evManager=Controller)

# Checks to see if the achievement progress was already saved
try:
    # Loads data from the file
    vars = pickle.load(open('SAVEDATA', 'rb'))
    globalAchievements.tracker = vars[0]
    globalAchievements.achievements = vars[1]

    # Update the achievement tracker with the new data
    globalAchievements.update()
except:
    pass

# Defines sound paths (incase it is called through pygame.mixer.music)
SOUND_FILE_ERROR = 'Sounds/Error.wav'
SOUND_FILE_BUILD = 'Sounds/Build.wav'
SOUND_FILE_CLEAR = 'Sounds/Clear.wav'
SOUND_FILE_THUMP = 'Sounds/Thump.wav'
SOUND_FILE_SELECT = 'Sounds/Selection.wav'
SOUND_FILE_DESELECT = 'Sounds/Deselect.wav'
SOUND_FILE_KEYSTROKE = 'Sounds/Keystroke.wav'
SOUND_FILE_BACKGROUND = 'Sounds/Background.mp3'
SOUND_FILE_FIREWORK = 'Sounds/Firework.wav'

# Create pygame.mixer Sound objects, based on previous file paths
SOUND_ERROR = pygame.mixer.Sound(SOUND_FILE_ERROR)
SOUND_BUILD = pygame.mixer.Sound(SOUND_FILE_BUILD)
SOUND_CLEAR = pygame.mixer.Sound(SOUND_FILE_CLEAR)
SOUND_THUMP = pygame.mixer.Sound(SOUND_FILE_THUMP)
SOUND_SELECT = pygame.mixer.Sound(SOUND_FILE_SELECT)
SOUND_DESELECT = pygame.mixer.Sound(SOUND_FILE_DESELECT)
SOUND_KEYSTROKE = pygame.mixer.Sound(SOUND_FILE_KEYSTROKE)
SOUND_FIREWORK = pygame.mixer.Sound(SOUND_FILE_FIREWORK)
ALL_SOUNDS = [SOUND_ERROR, SOUND_BUILD, SOUND_SELECT, SOUND_DESELECT, SOUND_KEYSTROKE, SOUND_FIREWORK]

# Variable used to keep track of what sound level the player wants
SOUND_VOLUME = 1

# Defines variables used for the physics engine
PHY_BOUNCE = 0.9 # Energy lost from a collision
PHY_PRECISION = 4 # How many times the engine loops through and calculates positions of nodes per frame
PHY_GRAV_3D = Vector3d(0, 0.2, 0) # Gravity vector
PHY_GRAV_2D = Vector2d(0, 0.2) # Gravity vector used by the bubbles and fireworks

REND_PREC = 20 # How many nodes across should the grid be. (It is the only area where you can place objects)

# How many firework parts a bubble breaks into
FIREWORK_PARTS = 40

# Variable that keeps track of the state the game is in
GAME_STATE = 0

# The colours that are used for buttons and text boxes.
# Both of these values are going to be updated soon anyway by the colour updater
GLOBAL_COLOUR = Vector3d(0, 255, 20)
GLOBAL_COLOUR_DARK = Vector3d(0, 255, 20)
