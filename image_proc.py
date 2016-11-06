import cv2
import numpy as np
from collections import deque
import wx
import sys
import threading
import math

import colors
from mouse import BasicController

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
        self.mouse = BasicController()
        self.mouse.margin = (0.1, 0.3, 0.15, 0.15)

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
            opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)

            contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                         cv2.CHAIN_APPROX_SIMPLE)[-2]

            #mouse movement
            if len(contours) == 0:
                continue

            max_con = max(contours, key=cv2.contourArea)
            ((x,y), radius) = cv2.minEnclosingCircle(max_con)
            moments = cv2.moments(max_con)
            if moments["m00"] == 0:
                continue
            center = (int(moments["m10"] / moments["m00"]),
                      int(moments["m01"] / moments["m00"]))


            scaled_x = center[0] / self.frame_width
            scaled_y = center[1] / self.frame_height
            self.mouse.move(scaled_x, scaled_y)
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

        self._curr_color = ''
        self._curr_color = 'black'

        self.createDisplay()

        self._panel.SetSizer(self._box)
        self.Center()


        self.camera = None


        self.Bind(wx.EVT_CLOSE, self.closeWindow)

    def createDisplay(self):
        txt = wx.StaticText(self._panel, -1, label="Select a Color that Matches your Cloth", style=wx.ALIGN_CENTER, name='')
        self._box.Add(txt, 0, wx.CENTER)
        self._box.AddSpacer((25,5))
        self._panel.SetSizer(self._box)

        counter = 0
        for color in colors.color_list:
            btn = wx.Button(self._panel,counter,'')
            btn.SetBackgroundColour(color)
            self._box.Add(btn,1,wx.ALIGN_CENTER)
            btn.Bind(wx.EVT_BUTTON,self.OnClicked)
            counter += 1

    def closeWindow(self, event):
        std_out("closeWindow")
        if self.camera:
            self.camera.abort()
            self.camera.join()
        event.Skip()

    def OnClicked(self, event):

        std_out("Clicked Color")
        
        if not self.camera:
            self.camera = CameraThread()

        id = event.GetEventObject().GetId()
        self.camera.change_color(colors.color_list[id])

        std_out(colors.color_list[id])
    
    
class ColorApp(wx.App):
    def OnInit(self):
        self.frame = ColorFrame()
        self.frame.Show(True)
        return True




