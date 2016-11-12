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

        self.erode_it = 2
        self.dilation_it = 1

        self.frame_width = self.cap.get(3)
        self.frame_height = self.cap.get(4)
        self.mouse = BasicController()
        self.mouse.margin = (0.1, 0.3, 0.15, 0.15)

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


            scaled_x = center[0] / self.frame_width
            scaled_y = center[1] / self.frame_height
            self.mouse.move(scaled_x, scaled_y)


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
                self.std_out(button)
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




