from pymouse import PyMouse
import numpy as np

class MouseController:
    # Moves the mouse. x and y are floats from 0 to 1.
    # 0,0 is the bottom left and 1,1 is the top right.
    def move(self, x, y):
        raise NotImplementedError()
    def click(self):
        raise NotImplementedError()

class BasicController(MouseController):
    def __init__(self):
        self.mouse = PyMouse()
        self.width, self.height = self.mouse.screen_size()
        self.margin = 0.0

    # The margin is the proportion of camera space that maps beyond the edge
    # of the computer screen. With a margin of 0.1, moving your hand anywhere
    # in the left 10% of the camera's vision moves the cursor to the left edge
    # of the screen. The same is true for the top/bottom/right sides.
    def get_margin(self):
        return self._margin
    def set_margin(self, val):
        self._margin = np.clip([val], 0.0, 0.49)
    margin = property(get_margin, set_margin)

    def move(self, x, y):
        # Rescale x and y so that moving the hand to the margin of the camera
        # space moves the cursor to the edge of the screen.
        dims = np.array([x, y])
        dims -= self.margin
        dims /= 1 - (2 * self.margin)
        dims = np.clip(dims, 0.0, 1.0)
        x = dims[0]
        y = dims[1]

        # Map from 0-1 onto actual screen dimensions.
        x = int(self.width * (1.0 - x))
        y = int(self.height * y)

        self.mouse.move(x, y)

    def click(self):
        pass
