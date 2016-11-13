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

        self._circle = False
        self._show_images = False

        self.frame_width = self.cap.get(3)
        self.frame_height = self.cap.get(4)

        self.basic_mouse = BasicController()
        self.joystick_mouse = JoystickController()

        self.mouse = self.basic_mouse

        self.camera_color = ''
        self.new_color = ''

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

        ero_it = 2
        dil_it = 1

        while not self._want_abort.isSet():

            if self._want_color_change == 1:
                std_out("while loop want to change color")
                self.camera_color = self.new_color
                self._want_color_change = 0
                color = self.set_color(self.camera_color)


            if self.release_resources():
                return

            ret, img = self.cap.read()
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            if self.camera_color != 'red':
                mask = cv2.inRange(hsv, color[0], color[1])

            #red special case
            else:
                mask0 = cv2.inRange(hsv, color[0][0], color[0][1])
                mask1 = cv2.inRange(hsv, color[1][0], color[1][1])
                mask = mask0 + mask1


            if self.release_resources():
                return

            erode = cv2.erode(mask,self.kernel,iterations = ero_it)
            dil = cv2.dilate(mask,self.kernel,iterations = dil_it)

            contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                         cv2.CHAIN_APPROX_SIMPLE)[-2]

            max_con = max(contours, key=cv2.contourArea)
            ((x,y), radius) = cv2.minEnclosingCircle(max_con)
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
            #if clicking gesture active:
            #    self.mouse.click(True, False)

            if self.release_resources():
                return

            # #draw circle around image
            # if self._circle:
            #     cv2.circle(img, (int(x), int(y)), int(radius), (255,0,0), 2)

            # circles = []
            # for con in contours:
            #     ((x,y), radius) = cv2.minEnclosingCircle(con)
            #     if radius <= 15:
            #         continue
            #     moments = cv2.moments(con)
            #     if moments["m00"] == 0:
            #         continue
            #     center = (int(moments["m10"] / moments["m00"]),
            #               int(moments["m01"] / moments["m00"]))
            #     circles.append((center, radius))
            # if len(circles) > 0:
            #     x = sum(circle[0][0] for circle in circles)
            #     x /= len(circles)
            #     y = sum(circle[0][1] for circle in circles)
            #     y /= len(circles)
            #     radius = 0
            #     for circle in circles:
            #         tempx = circle[0][0]
            #         tempy = circle[0][1]
            #         dist = (tempx-x) * (tempx-x) + (tempy-y) * (tempy-y)
            #         dist = math.sqrt(dist)
            #         radius = max(radius, dist + circle[1])
            #     if radius <= 15:
            #         continue

            #     black = np.zeros((int(self.frame_height), int(self.frame_width), 3), np.uint8)
            #     cv2.circle(black, (int(x), int(y)), int(radius), (255,255,255), -1)
            #     glove = cv2.bitwise_and(img, black)

            #     if self._show_images:
            #         cv2.imshow("glove", glove)

        self._released = self.release_resources()

    def get_circle(self, image):
        pass

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

        corner_label = wx.StaticText(self._panel, -1, label="Corner coordinates", style=wx.ALIGN_CENTER)
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




