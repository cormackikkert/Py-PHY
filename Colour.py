from Events import *
from Vectors import *
import Constants

# Converts RGB to HSV
def RGBtoHSV(rgb):
    # follows the formula explained by this website
    # http://www.rapidtables.com/convert/color/rgb-to-hsv.htm

    # X component of vector = red
    # Y component of vector = yellow
    # Z component of vector = blue

    normalised = rgb / 255
    cMax = max(value for value in normalised)
    cMin = min(value for value in normalised)
    delta = cMax - cMin

    if delta == 0:
        hue = 0
    elif cMax == normalised.x:
        hue = 60 * ((normalised.y - normalised.z) / delta % 6)
    elif cMax == normalised.y:
        hue = 60 * ((normalised.z - normalised.x) / delta + 2)
    elif cMax == normalised.z:
        hue = 60 * ((normalised.z - normalised.x) / delta + 2)

    if abs(cMax - 0) < 0.0004:
        sat = 0
    else:
        sat = delta / cMax

    val = cMax
    final = Vector3d(hue, sat, val)
    return final

# Converts HSV to RGB, following the algorithm defined here
# http://www.rapidtables.com/convert/color/hsv-to-rgb.htm
def HSVtoRGB(hsv):
    C = hsv.y * hsv.z
    X = C * (1 - abs((hsv.x / 60) % 2 - 1))
    m = hsv.z - C

    if 0 <= hsv.x < 60:
        prime = (C, X, 0)
    elif 60 <= hsv.x < 120:
        prime =  (X, C, 0)
    elif 120 <= hsv.x < 180:
        prime = (0, C, X)
    elif 180 <= hsv.x < 240:
        prime = (0, X, C)
    elif 240 <= hsv.x < 300:
        prime = (X, 0, C)
    elif 300 <= hsv.x < 360:
        prime = (C, 0, X)
    return Vector3d((prime[0] + m) * 255, (prime[1] + m) * 255, (prime[2] + m) * 255)

class ColourUpdater:
    @EventAdder
    def __init__(self, **kwargs):
        self.layer = -2
        self.degrees = 0 # Hue used when this object updates the global colours. Hue changes over time

    def notify(self, event):
        if isinstance(event, TickEvent):
            # Update the new hue
            self.degrees = (self.degrees + 0.1) % 360

            # Creates new RGB colours
            newlight = HSVtoRGB(Vector3d(self.degrees, 1, 0.65))  # High value means it appears lighter
            newdark = HSVtoRGB(Vector3d(self.degrees, 1, 0.4))  # Low value means it appears darker

            # Updates GLOBAL_COLOUR, while maintaining the vector (not creating a new one)
            Constants.GLOBAL_COLOUR.x = newlight.x
            Constants.GLOBAL_COLOUR.y = newlight.y
            Constants.GLOBAL_COLOUR.z = newlight.z

            # Updates GLOBAL_COLOUR_DARK, while maintaining the vector (not creating a new one)
            Constants.GLOBAL_COLOUR_DARK.x = newdark.x
            Constants.GLOBAL_COLOUR_DARK.y = newdark.y
            Constants.GLOBAL_COLOUR_DARK.z = newdark.z


