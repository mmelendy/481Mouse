import cv2
import numpy as np
from collections import deque
import wx
import sys
import threading
import math
from threading import Timer
import colors
from mouse import BasicController, JoystickController, external_movement_detector

def std_out(value):
    #return
    print value
    sys.stdout.flush()

class CameraThread(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)

        self.camera_num = None
        self._released = False

        self.cap = self.set_camera()
        self.kernel = np.ones((5,5),np.uint8)

        self.erode_it = 3
        self.dilation_it = 2

        self.frame_width = self.cap.get(3)
        self.frame_height = self.cap.get(4)

        self.basic_mouse = BasicController()
        self.joystick_mouse = JoystickController()

        self.mouse = self.basic_mouse

        self.camera_color = ''
        self.new_color = ''

        self.left_button_color = None
        self.right_button_color = None

        self.button_size = 10
        self.current_l_button_size = 10
        self.current_r_button_size = 10

        self.right_button_flag = False
        self.left_button_flag = False

        self._want_abort = threading.Event()
        self._want_color_change = 0

        self.start()


    def run(self):
        color = None

        while not self.camera_color:
            if self._want_color_change == 1:
                self.camera_color = self.new_color
                self._want_color_change = 0
                color = self.set_color(self.camera_color)
                #but = "lmb: ", self.left_button_color, "  rmb: ", self.right_button_color
                #std_out(but)
            if self._want_abort.isSet():
                break

        
        while not self._want_abort.isSet():

            if self._want_color_change == 1:
                self.camera_color = self.new_color
                self._want_color_change = 0
                color = self.set_color(self.camera_color)
                #but = "lmb: ", self.left_button_color, "  rmb: ", self.right_button_color
                #std_out(but)

            ret, img = self.cap.read()
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            mask, contours = self.get_image_contour(hsv, self.camera_color)

            #mask = cv2.erode(mask,self.kernel,iterations = self.erode_it)
            #mask = cv2.dilate(mask,self.kernel,iterations = self.dilation_it)
            
            #contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            #                             cv2.CHAIN_APPROX_SIMPLE)[-2]

            #mouse movement
            if len(contours) == 0:
                continue

            max_con, radius = self.enclosing_circle(contours)

            #max_con = max(contours, key=cv2.contourArea)
            #((x,y), radius) = cv2.minEnclosingCircle(max_con)
            
            moments = cv2.moments(max_con)
            if moments["m00"] == 0:
                continue
            center = (int(moments["m10"] / moments["m00"]),
                      int(moments["m01"] / moments["m00"]))
            
            # Scale x and y to between 0.0 and 1.0, and invert both: the camera
            # is rotated 180 degrees from the user, and y=0 is the bottom, not
            # the top.
            # if not self.right_button_flag or not self.left_button_flag:
            scaled_x = center[0] / self.frame_width
            scaled_y = center[1] / self.frame_height
            self.mouse.move(1.0 - scaled_x, 1.0 - scaled_y)



            circles = []
            for con in contours:
                ((x,y), radius) = cv2.minEnclosingCircle(con)
                if radius <= 15:
                    continue
                moments = cv2.moments(con)
                if moments["m00"] == 0:
                    continue
                center = (int(moments["m10"] / moments["m00"]),
                          int(moments["m01"] / moments["m00"]))
                circles.append((center, radius))
            
            if len(circles) == 0:
                continue

            x = sum(circle[0][0] for circle in circles)
            x /= len(circles)
            y = sum(circle[0][1] for circle in circles)
            y /= len(circles)
            radius = 0
            for circle in circles:
                tempx = circle[0][0]
                tempy = circle[0][1]
                dist = (tempx-x) * (tempx-x) + (tempy-y) * (tempy-y)
                dist = math.sqrt(dist)
                radius = max(radius, dist + circle[1])

            black = np.zeros((int(self.frame_height), int(self.frame_width), 3), np.uint8)
            cv2.circle(black, (int(x), int(y)), int(radius), (255,255,255), -1)
            glove = cv2.bitwise_and(hsv, black)


            left_mb, left_contour = self.get_image_contour(glove, self.left_button_color)

            right_mb, right_contour = self.get_image_contour(glove, self.right_button_color)


            # cv2.imshow("left", left_mb)
            # cv2.imshow("right", right_mb)
            # cv2.imshow("glove", glove)


            self.current_l_button_size, self.left_button_flag = \
                self.detect_button(left_contour, self.left_button_flag, 
                                    self.current_l_button_size, 'left')
            
            self.current_r_button_size, self.right_button_flag = \
                self.detect_button(right_contour,  self.right_button_flag, 
                                    self.current_r_button_size, 'right')





            if self.release_resources():
                return


        self._released = self.release_resources()

    def get_mask(self, hsv, color):
        color_range = colors.color_dict.get(color, colors.hsv_blue)
        if color != 'red':
            return cv2.inRange(hsv, color_range[0], color_range[1])
        else: 
            return cv2.inRange(hsv, color_range[0][0], color_range[0][1]) \
                 + cv2.inRange(hsv, color_range[1][0], color_range[1][1])


    def get_image_contour(self, image, color):
        mask = self.get_mask(image, color)
        mask = cv2.erode(mask,self.kernel,iterations = self.erode_it)
        mask = cv2.dilate(mask,self.kernel,iterations = self.dilation_it)

        contour = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)[-2]
        return mask, contour

    def detect_button(self, contour, flag, current_size, button):
    
        radius = 0
        if len(contour) > 0:
            max_con, radius = self.enclosing_circle(contour)

        #max_con = max(contour, key=cv2.contourArea)
        #((x,y), radius) = cv2.minEnclosingCircle(max_con)

        if not flag:
            if radius > self.button_size: 
                flag = True
                current_size  = radius
        else:
            # std_out("Possible button")
            if radius < current_size * 0.5:
                if button == 'left':
                    self.mouse.click(True, False)
                elif button == 'right':
                    self.mouse.click(False, True)
                flag = False
                current_size = self.button_size
                # std_out(button)
            else:
                current_size = radius


        return current_size, flag

    def enclosing_circle(self, contour):
        max_con = max(contour, key=cv2.contourArea)
        ((x,y), radius) = cv2.minEnclosingCircle(max_con)
        return max_con, radius

    def set_color(self, color):
        self.left_button_color = colors.lmb_dict.get(color, 'yellow')
        self.right_button_color = colors.rmb_dict.get(color, 'green')
        return colors.color_dict.get(color,colors.hsv_cyan)

    def change_color(self, color):
        self._want_color_change = 1
        self.new_color = color

    def set_camera(self):
        for i in reversed(xrange(5)):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.camera_num = i
                return cap

    def abort(self):
        self._want_abort.set()

    def release_resources(self):
        if self._want_abort.isSet():
            if self._released:
                cv2.destroyAllWindows()
                cv2.VideoCapture(self.camera_num).release()
                self._released = True
            return True

        return False

class ColorFrame(wx.Frame):
    def __init__(self):
        super(ColorFrame, self).__init__(None,-1,"Color Selector",wx.Point(100,100),wx.Size(250,400))
        self._panel = wx.Panel(self)
        self._box = wx.BoxSizer(wx.VERTICAL)

        self.camera = CameraThread()

        self.createDisplay()
        self.rb1.SetValue(True)
        self.default_margins()
        self.default_joystick()
        self.setController()

        self._panel.SetSizer(self._box)
        self.Center()
        self.Bind(wx.EVT_CLOSE, self.closeWindow)

    def createDisplay(self):
        color_label = wx.StaticText(self._panel, -1, label="Select a Color that Matches your Cloth", style=wx.ALIGN_CENTER, name='')
        self._box.Add(color_label, 0, wx.CENTER)
        self._box.AddSpacer((25,5))

        counter = 0
        for color in colors.color_list:
            btn = wx.Button(self._panel, counter, '')
            btn.SetBackgroundColour(color)
            self._box.Add(btn,1,wx.ALIGN_CENTER)
            btn.Bind(wx.EVT_BUTTON,self.SelectColor)
            counter += 1

        # Controller selection
        self.rb1 = wx.RadioButton(self._panel, label="Mouse mode", style=wx.RB_GROUP)
        self.rb1.Bind(wx.EVT_RADIOBUTTON, self.setController)
        self.rb2 = wx.RadioButton(self._panel, label="Joystick mode")
        self.rb2.Bind(wx.EVT_RADIOBUTTON, self.setController)

        rb_box = wx.BoxSizer(wx.HORIZONTAL)
        rb_box.AddStretchSpacer()
        rb_box.Add(self.rb1, 1, wx.ALIGN_CENTER)
        rb_box.AddStretchSpacer()
        rb_box.Add(self.rb2, 1, wx.ALIGN_CENTER)
        rb_box.AddStretchSpacer()
        self._box.Add(rb_box)

        # Mouse controller settings
        self.mouse_box = wx.BoxSizer(wx.VERTICAL)
        corner_label = wx.StaticText(self._panel, -1, label="Corner coordinates (?)", style=wx.ALIGN_CENTER)
        corner_label.SetToolTip(wx.ToolTip("Coordinates are given as percentage offsets from the bottom and left of the screen. These corners define the shape and size of the space across which your hand needs to move to reach the corners and edges of the screen."))
        self.mouse_box.Add(corner_label, 0, wx.CENTER)

        self.corners = []

        def make_corner():
            corner_box = wx.BoxSizer(wx.HORIZONTAL)
            for x in xrange(2):
                c = wx.SpinCtrl(self._panel, size=(50,20))
                corner_box.Add(c)
                self.corners.append(c)
            return corner_box
        tl = make_corner()
        tr = make_corner()
        br = make_corner()
        bl = make_corner()

        default_ranges = [(0,49), (51,100), (51,100), (51,100), (51,100), (0,49), (0,49), (0,49)]
        for i in range(len(self.corners)):
            self.corners[i].SetRange(default_ranges[i][0], default_ranges[i][1])

        top_row = wx.BoxSizer(wx.HORIZONTAL)
        top_row.Add(tl, 0)
        top_row.AddStretchSpacer()
        top_row.Add(tr, 0)

        bottom_row = wx.BoxSizer(wx.HORIZONTAL)
        bottom_row.Add(bl)
        bottom_row.AddStretchSpacer()
        bottom_row.Add(br)

        self.mouse_box.Add(top_row, flag=wx.EXPAND)
        self.mouse_box.AddSpacer(20, 5)
        self.mouse_box.Add(bottom_row, flag=wx.EXPAND)

        default_margin_button = wx.Button(self._panel, label="Default margins")
        default_margin_button.Bind(wx.EVT_BUTTON, self.default_margins)
        apply_margin_button = wx.Button(self._panel, label="Apply changes")
        apply_margin_button.Bind(wx.EVT_BUTTON, self.update_margin)

        margin_buttons_box = wx.BoxSizer(wx.HORIZONTAL)
        margin_buttons_box.Add(default_margin_button, 1)
        margin_buttons_box.Add(apply_margin_button, 1)
        self.mouse_box.Add(margin_buttons_box, 0, wx.EXPAND)

        self._box.Add(self.mouse_box, 1, wx.EXPAND)

        # Joystick controller settings
        self.joystick_box = wx.BoxSizer(wx.VERTICAL)

        def label_control(text, tooltip, ctrl):
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self._panel, label=text)
            label.SetToolTip(wx.ToolTip(tooltip))
            sizer.Add(label)
            sizer.AddStretchSpacer()
            sizer.AddSpacer((5,5))
            sizer.Add(ctrl, 0, wx.ALIGN_RIGHT)
            return sizer

        joystick_controls = wx.BoxSizer(wx.VERTICAL)
        self.joy_speed = wx.SpinCtrl(self._panel, size=(50,20))
        self.joy_speed.SetRange(1, 40)
        joystick_controls.Add(label_control("Speed (?)", "Higher values mean the cursor moves faster", self.joy_speed), 1, wx.EXPAND)
        self.joy_accel = wx.SpinCtrl(self._panel, size=(50,20))
        self.joy_accel.SetRange(1, 20)
        joystick_controls.Add(label_control("Acceleration (?)", "Higher values mean the cursor moves more slowly at small distances", self.joy_accel), 1, wx.EXPAND)
        self.joy_dz = wx.SpinCtrl(self._panel, size=(50,20))
        self.joy_dz.SetRange(0, 40)
        joystick_controls.Add(label_control("Dead zone (?)", "The percentage of the screen corresponding to the 'center', where no movement occurs", self.joy_dz), 1, wx.EXPAND)
        self.joystick_box.Add(joystick_controls, 0, wx.CENTER)

        # Sort of gross hard-coded space to make the two panels equally tall.
        self.joystick_box.AddSpacer((5,16))

        joystick_buttons_box = wx.BoxSizer(wx.HORIZONTAL)
        default_joystick_button = wx.Button(self._panel, label="Default settings")
        default_joystick_button.Bind(wx.EVT_BUTTON, self.default_joystick)
        apply_joystick_button = wx.Button(self._panel, label="Apply changes")
        apply_joystick_button.Bind(wx.EVT_BUTTON, self.apply_joystick)
        joystick_buttons_box.Add(default_joystick_button, 1)
        joystick_buttons_box.Add(apply_joystick_button, 1)
        self.joystick_box.Add(joystick_buttons_box, 0, wx.EXPAND)

        self._box.Add(self.joystick_box, 1, wx.EXPAND)

    def default_margins(self, event=None):
        default_corners = [10,80, 70,70, 80,10, 10,10]
        for i in xrange(len(self.corners)):
            self.corners[i].SetValue(default_corners[i])
        self.update_margin()

    def update_margin(self, event=None):
        def adjacent_pairs(lst):
            for i in xrange(0, len(lst), 2):
                yield (lst[i].GetValue() / 100., lst[i+1].GetValue() / 100.)

        new_corners = tuple(adjacent_pairs(self.corners))
        self.camera.basic_mouse.set_margin(new_corners)

    def default_joystick(self, event=None):
        self.joy_speed.SetValue(8)
        self.joy_accel.SetValue(4)
        self.joy_dz.SetValue(5)
        self.apply_joystick()

    def apply_joystick(self, event=None):
        self.camera.joystick_mouse.speed = self.joy_speed.GetValue()
        self.camera.joystick_mouse.acceleration = self.joy_accel.GetValue()
        self.camera.joystick_mouse.dead_zone = self.joy_dz.GetValue() / 100.0

    def setController(self, event=None):
        if self.rb1.GetValue():
            self.camera.mouse = self.camera.basic_mouse
            self.mouse_box.ShowItems(True)
            self.joystick_box.ShowItems(False)
        else:
            self.camera.mouse = self.camera.joystick_mouse
            self.mouse_box.ShowItems(False)
            self.joystick_box.ShowItems(True)
        self._box.Layout()

    def SelectColor(self, event):
        id = event.GetEventObject().GetId()
        self.camera.change_color(colors.color_list[id])

        # Start tracking right after the user clicks, without making them wait
        # for the full mouse override timeout.
        t = Timer(0.2, external_movement_detector.enable)
        t.start()

    def closeWindow(self, event):
        if self.camera:
            self.camera.abort()
            self.camera.join()
        event.Skip()
        external_movement_detector.stop()

class ColorApp(wx.App):
    def OnInit(self):
        self.frame = ColorFrame()
        self.frame.Show(True)
        return True




