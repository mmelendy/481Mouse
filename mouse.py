from pymouse import PyMouse
import numpy as np

class MouseController:
    # Moves the mouse. x and y are floats from 0 to 1.
    # 0,0 is the bottom left and 1,1 is the top right.
    def move(self, x, y):
        raise NotImplementedError()

    def click(self, left, right):
        raise NotImplementedError()

class BasicController(MouseController):
    def __init__(self):
        self.mouse = PyMouse()
        self.width, self.height = self.mouse.screen_size()
        self.margin = (0.0, 0.0, 0.0, 0.0)
        self.last_pos = (0,0)

    # The margin is the proportion of camera space that maps beyond the edge
    # of the computer screen. With a left margin of 0.1, moving your hand
    # anywhere in the left 10% of the camera's vision moves the cursor to the
    # left edge of the screen. The same is true for the top/bottom/right sides.
    # Margin is a 4-tuple of floats in the order left, right, bottom, top.
    def get_margin(self):
        return self._margin
    def set_margin(self, val):
        if len(val) != 4 or val[0] + val[1] >= 1.0 or val[2] + val[3] >= 1.0:
            raise RuntimeError("Invalid margin values")
        self._margin = np.clip(val, 0.0, 0.99)
    margin = property(get_margin, set_margin)

    def move(self, x, y, left=False, right=False):
        # Rescale x and y so that moving the hand to the margin of the camera
        # space moves the cursor to the edge of the screen.
        def rescale(val, lower, upper):
            val -= lower
            val /= 1 - (lower + upper)
            val = np.clip([val], 0.0, 1.0)
            return val
        x = rescale(x, self.margin[1], self.margin[0])
        y = rescale(y, self.margin[2], self.margin[3])

        # Map from 0-1 onto actual screen dimensions.
        x = int(self.width * (1.0 - x))
        y = int(self.height * y)

        self.last_pos = (x, y)
        self.mouse.move(x, y)

    def click(self, left, right):
        x, y = self.last_pos
        if left:
            self.mouse.click(x, y, 1)
        if right:
            self.mouse.click(x, y, 2)
