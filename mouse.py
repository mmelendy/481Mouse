from pymouse import PyMouse, PyMouseEvent
import numpy as np
from collections import deque
import sys
from threading import Thread, Timer

class MouseController:
    # Moves the mouse. x and y are floats from 0 to 1.
    # 0,0 is the bottom left and 1,1 is the top right.
    def move(self, x, y):
        raise NotImplementedError()

    def click(self, left, right):
        raise NotImplementedError()

mouse = PyMouse()
width, height = mouse.screen_size()

# Detects when the mouse is moved. is_active() returns true iff the mouse
# hasn't been moved recently. Use this to let the user override the CV.
# Call intend() before moving the mouse with PyMouse.
class ExternalMouseMovement(PyMouseEvent):
    def __init__(self):
        PyMouseEvent.__init__(self)
        self.active = True
        self.timer = Timer(0.0, lambda: None)
        self.intended_move = False

        # Start tracking the mouse when the object is initialized.
        thread = Thread(target=self.run)
        thread.start()

    def move(self, x, y):
        # Disable mouse movement for a period if we detect external movement
        if self.intended_move:
            self.intended_move = False
        else:
            self.disable()

    def disable(self):
        self.active = False
        self.timer.cancel()
        self.timer = Timer(1.0, self.enable)
        self.timer.start()

    def enable(self):
        self.active = True
        self.timer.cancel()

    def is_active(self):
        return self.active

    def intend(self):
        self.intended_move = True

external_movement_detector = ExternalMouseMovement()

class BasicController(MouseController):
    def __init__(self):
        self.positions = deque(maxlen=6)
        self.p0 = None
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.n0 = None
        self.n1 = None
        self.n2 = None
        self.n3 = None
        self.set_margin(((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)))

    # Margin is a 4-tuple of pairs of floats in the order top-left, top-right,
    # bottom-right, bottom-left. Each (x,y) pair represents a corner of the
    # space in which the user moves their hand. For example, the default top
    # left corner (0.0, 1.0) means the corner of the screen corresponds to the
    # actual corner of the camera's field of view. But (0.1, 0.9) means the
    # corner of the screen is 10% in from the left and 90% in from the bottom
    # edge of the camera space.
    def set_margin(self, corners):
        if len(corners) != 4:
            raise RuntimeError("Must specify four corners when setting margins")
        for corner in corners:
            if len(corner) != 2:
                raise RuntimeError("Must specify (x, y) for each corner")
        self.p0 = np.array(corners[3])
        self.p1 = np.array(corners[2])
        self.p2 = np.array(corners[1])
        self.p3 = np.array(corners[0])

        def ccw(vec):
            return np.array([vec[1], -vec[0]])
        def normalize(vec):
            norm = np.linalg.norm(vec)
            return vec / norm

        self.n0 = normalize(ccw(self.p0 - self.p3))
        self.n1 = normalize(ccw(self.p1 - self.p0))
        self.n2 = normalize(ccw(self.p2 - self.p1))
        self.n3 = normalize(ccw(self.p3 - self.p2))

    def move(self, x, y):
        if not external_movement_detector.is_active():
            return

        # Map hand space onto screen space. Algorithm from StackExchange.
        # http://math.stackexchange.com/questions/13404/mapping-irregular-quadrilateral-to-a-rectangle/104595#104595
        p = np.array([x, y])

        du0 = np.dot((p - self.p0), self.n0)
        du1 = np.dot((p - self.p2), self.n2)
        u = du0 / (du0 + du1)

        dv0 = np.dot((p - self.p0), self.n1)
        dv1 = np.dot((p - self.p3), self.n3)
        v = dv0 / (dv0 + dv1)

        # Map from 0-1 onto actual screen dimensions.
        x = int(width * u)
        y = int(height * (1.0 - v))
        if self.positions:
            x0, y0 = self.avg_pos()
            if abs(x0 - x) > 0.5 * width or abs(y0 - y) > 0.5 * height:
                self.positions.append(np.array([x, y]))
                x, y = self.avg_pos()
                mouse.move(x, y)
                return False

        self.positions.append(np.array([x, y]))
        x, y = self.avg_pos()

        external_movement_detector.intend()
        mouse.move(x, y)

        return True

    def click(self, left, right):
        if not external_movement_detector.is_active():
            return

        x, y = self.avg_pos()
        if left:
            mouse.click(x, y, 1)
        if right:
            mouse.click(x, y, 2)

    def avg_pos(self):
        return sum(p for p in self.positions) / len(self.positions)

class JoystickController(MouseController):
    def __init__(self):
        self.last_uv = (0.5, 0.5)

        # The origin is the center of the hand space, where no movement occurs.
        self.origin = np.array([0.5, 0.5])

        # The dead zone is the minimum distance from origin at which any
        # movement will occur, the size of the "center" of the hand space.
        self.dead_zone = 0.0

        # Higher speed means the mouse moves faster at all distances.
        self.speed = 1.0

        # Higher acceleration means the mouse moves *slower* for low distances.
        self.acceleration = 1.0

    def move(self, x, y):
        if not external_movement_detector.is_active():
            return False

        p = np.array([x, y])

        vec = p - self.origin
        r = np.linalg.norm(vec)

        distance = r - self.dead_zone
        if (distance > 0.0):
            distance = distance**self.acceleration * self.speed

            vec /= r
            vec *= distance

            x = vec[0] + self.last_uv[0]
            y = vec[1] + self.last_uv[1]

            x, y = np.clip([x, y], 0.0, 1.0)
            self.last_uv = (x, y)

            # Map from 0-1 onto actual screen dimensions.
            x = int(width * x)
            y = int(height * (1.0 - y))

            self.last_pos = (x, y)

            external_movement_detector.intend()
            mouse.move(x, y)
            return True
        return False

    def click(self, left, right):
        if not external_movement_detector.is_active():
            return

        x, y = self.last_pos
        if left:
            mouse.click(x, y, 1)
        if right:
            mouse.click(x, y, 2)
