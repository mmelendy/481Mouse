from pymouse import PyMouse
import numpy as np
import sys

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
        self.last_pos = (0, 0)
        self.p0 = None
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.n0 = None
        self.n1 = None
        self.n2 = None
        self.n3 = None
        self.set_margin(((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)))
        self.frames = 0

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
        # Map hand space onto screen space. Algorithm from StackExchange.
        # http://math.stackexchange.com/questions/13404/mapping-irregular-quadrilateral-to-a-rectangle/104595#104595
        p = np.array([x, y])

        du0 = np.dot((p - self.p0), self.n0)
        du1 = np.dot((p - self.p2), self.n2)
        u = du0 / (du0 + du1)

        dv0 = np.dot((p - self.p0), self.n1)
        dv1 = np.dot((p - self.p3), self.n3)
        v = dv0 / (dv0 + dv1)

        self.frames += 1
        if (self.frames >= 50):
            print 'corners: ', self.p3, self.p2, self.p1, self.p0
            print 'p: ', p
            print 'du0, du1, u: ', du0, du1, u
            print 'dv0, dv1, v: ', dv0, dv1, v
            print
            sys.stdout.flush()
            self.frames = 0

        # Map from 0-1 onto actual screen dimensions.
        x = int(self.width * u)
        y = int(self.height * (1.0 - v))

        self.last_pos = (x, y)
        self.mouse.move(x, y)

    def click(self, left, right):
        x, y = self.last_pos
        if left:
            self.mouse.click(x, y, 1)
        if right:
            self.mouse.click(x, y, 2)

class JoystickController(MouseController):
    def __init__(self):
        self.mouse = PyMouse()
        self.width, self.height = self.mouse.screen_size()
        self.last_pos = (0.5, 0.5)
        self.frames = 0

        # The origin is the center of the hand space, where no movement occurs.
        self.origin = np.array([0.5, 0.5])

        # The dead zone is the minimum distance from origin at which any
        # movement will occur, the size of the "center" of the hand space.
        self.dead_zone = 0.1

        # Higher speed means the mouse moves faster at all distances.
        self.speed = 8.0

        # Higher acceleration means the mouse moves *slower* for low distances.
        self.acceleration = 4.0

    def move(self, x, y):
        p = np.array([x, y])

        vec = p - self.origin
        r = np.linalg.norm(vec)

        distance = r - self.dead_zone
        if (distance > 0.0):
            distance = distance**self.acceleration * self.speed

            vec /= r
            vec *= distance

            x = vec[0] + self.last_pos[0]
            y = vec[1] + self.last_pos[1]

            x, y = np.clip([x, y], 0.0, 1.0)
            self.last_pos = (x, y)

            # Map from 0-1 onto actual screen dimensions.
            x = int(self.width * x)
            y = int(self.height * (1.0 - y))

            self.frames += 1
            if self.frames >= 50:
                print 'p: ', p
                print 'r, distance: ', r, distance
                print 'vec: ', vec
                print 'last pos: ', self.last_pos
                print 'x, y: ', x, y
                print
                sys.stdout.flush()
                self.frames = 0

            self.mouse.move(x, y)

    def click(self, left, right):
        x, y = self.last_pos
        if left:
            self.mouse.click(x, y, 1)
        if right:
            self.mouse.click(x, y, 2)
