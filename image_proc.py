import cv2
import numpy as np
from collections import deque
import wx
import sys
import threading
import math

import colors
from mouse import BasicController, JoystickController

def std_out(value):
    return
    print value
    sys.stdout.flush()

class CameraThread(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)

        self.camera_num = None
        self._released = False

        self.cap = self.set_camera()
        self.kernel = np.ones((5,5),np.uint8)

        self.erode_it = 2
        self.dilation_it = 1

        self.frame_width = self.cap.get(3)
        self.frame_height = self.cap.get(4)

        self.basic_mouse = BasicController()
        self.joystick_mouse = JoystickController()

        self.mouse = self.basic_mouse

        self.camera_color = ''
        self.new_color = ''

        self.left_button_color = 'blue'
        self.right_button_color = 'yellow'

        self.button_size = 30
        self.current_l_button_size = 30
        self.current_r_button_size = 30

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
            if self._want_abort.isSet():
                break

        
        while not self._want_abort.isSet():

            if self._want_color_change == 1:
                std_out("while loop want to change color")
                self.camera_color = self.new_color
                self._want_color_change = 0
                color = self.set_color(self.camera_color)

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

            self.current_l_button_size, self.left_button_flag = \
                self.detect_button(left_contour, self.left_button_flag, 
                                    self.current_l_button_size, 'left')
            
            self.current_r_button_size, self.right_button_flag = \
                self.detect_button(right_contour,  self.left_button_flag, 
                                    self.current_l_button_size, 'right')

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
        image = cv2.erode(mask,self.kernel,iterations = self.erode_it)
        image = cv2.dilate(mask,self.kernel,iterations = self.dilation_it)

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
            if radius < current_size * 0.5:
                # mouse.click(True, False)
                flag = False
                current_size = self.button_size
                std_out(button)
            else:
                current_size = radius

        return current_size, flag

    def enclosing_circle(self, contour):
        max_con = max(contour, key=cv2.contourArea)
        ((x,y), radius) = cv2.minEnclosingCircle(max_con)
        return max_con, radius

    def set_color(self, color):
        std_out("set color")
        return colors.color_dict.get(color,colors.hsv_blue)

    def change_color(self, color):
        self._want_color_change = 1
        self.new_color = color

        std_out("change color")

    def set_camera(self):
        for i in reversed(xrange(5)):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.camera_num = i
                return cap

    def abort(self):
        self._want_abort.set()
        std_out(self._want_abort.isSet())
        std_out("set abort")

    def release_resources(self):
        if self._want_abort.isSet():
            if self._released:
                cv2.destroyAllWindows()
                cv2.VideoCapture(self.camera_num).release()
                self._released = True
                std_out("released")
            return True

        return False

class ColorFrame(wx.Frame):
    def __init__(self):
        super(ColorFrame, self).__init__(None,-1,"Color Selector",wx.Point(100,100),wx.Size(250,400))
        self._panel = wx.Panel(self)
        self._box = wx.BoxSizer(wx.VERTICAL)

        self.camera = CameraThread()

        self.createDisplay()
        self._panel.SetSizer(self._box)
        self.Center()
        self.Bind(wx.EVT_CLOSE, self.closeWindow)

    def createDisplay(self):
        color_label = wx.StaticText(self._panel, -1, label="Select a Color that Matches your Cloth", style=wx.ALIGN_CENTER, name='')
        self._box.Add(color_label, 0, wx.CENTER)
        self._box.AddSpacer((25,5))

        counter = 0
        for color in colors.color_list:
            btn = wx.Button(self._panel,counter,'')
            btn.SetBackgroundColour(color)
            self._box.Add(btn,1,wx.ALIGN_CENTER)
            btn.Bind(wx.EVT_BUTTON,self.OnClicked)
            counter += 1

        self.rb1 = wx.RadioButton(self._panel, label="Mouse mode", style=wx.RB_GROUP)
        self._box.Add(self.rb1, 1, wx.ALIGN_CENTER)
        self.rb1.Bind(wx.EVT_RADIOBUTTON, self.setController)

        corner_label = wx.StaticText(self._panel, -1, label="Corner coordinates (?)", style=wx.ALIGN_CENTER)
        corner_label.SetToolTip(wx.ToolTip("Coordinates are given as percentage offsets from the bottom and left of the screen. These corners define the shape and size of the space across which your hand needs to move to reach the corners and edges of the screen."))
        self._box.Add(corner_label, 0, wx.CENTER)

        self.corners = []

        def make_corner():
            corner_box = wx.BoxSizer(wx.HORIZONTAL)
            for x in xrange(2):
                c = wx.SpinCtrl(self._panel, size=(50,20))
                c.SetRange(0, 100)
                corner_box.Add(c)
                self.corners.append(c)
            return corner_box
        tl = make_corner()
        tr = make_corner()
        br = make_corner()
        bl = make_corner()

        top_row = wx.BoxSizer(wx.HORIZONTAL)
        top_row.Add(tl, 0)
        top_row.AddStretchSpacer()
        top_row.Add(tr, 0)

        bottom_row = wx.BoxSizer(wx.HORIZONTAL)
        bottom_row.Add(bl)
        bottom_row.AddStretchSpacer()
        bottom_row.Add(br)

        self._box.Add(top_row, flag=wx.EXPAND)
        self._box.AddSpacer(25, 5)
        self._box.Add(bottom_row, flag=wx.EXPAND)

        default_corners = [10,80, 70,70, 80,10, 10,10]
        for i in xrange(len(self.corners)):
            self.corners[i].SetValue(default_corners[i])
        self.update_margin(None)

        margin_button = wx.Button(self._panel, label="Change margins")
        self._box.Add(margin_button)
        margin_button.Bind(wx.EVT_BUTTON, self.update_margin)

        self.rb2 = wx.RadioButton(self._panel, label="Joystick mode")
        self._box.Add(self.rb2, 1, wx.ALIGN_CENTER)
        self.rb2.Bind(wx.EVT_RADIOBUTTON, self.setController)

    def update_margin(self, event):
        def adjacent_pairs(lst):
            for i in xrange(0, len(lst), 2):
                yield (lst[i].GetValue() / 100., lst[i+1].GetValue() / 100.)

        new_corners = tuple(adjacent_pairs(self.corners))
        self.camera.basic_mouse.set_margin(new_corners)

    def setController(self, event):
        if self.rb1.GetValue():
            self.camera.mouse = self.camera.basic_mouse
        else:
            self.camera.mouse = self.camera.joystick_mouse

    def OnClicked(self, event):
        std_out("Clicked Color")

        id = event.GetEventObject().GetId()
        self.camera.change_color(colors.color_list[id])

        std_out(colors.color_list[id])

    def closeWindow(self, event):
        std_out("closeWindow")
        if self.camera:
            self.camera.abort()
            self.camera.join()
        event.Skip()

class ColorApp(wx.App):
    def OnInit(self):
        self.frame = ColorFrame()
        self.frame.Show(True)
        return True




