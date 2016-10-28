import cv2
import numpy as np
from collections import deque
import wx
import sys
from threading import *

import colors
#from interface import ColorApp
from mouse import BasicController

'''
EVT_RESULT_ID = wx.NewID()

def EVENT_RESULT(win, func):
	win.Connect(-1,-1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
	def __init__(self, data):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_RESULT_ID)
		sefl.data = data
'''

def std_out(value):
	print value
	sys.stdout.flush()

class CameraThread(Thread):
	def __init__(self):

		Thread.__init__(self)
		#self.setDaemon(True)

		self.camera_num = 1

		self.cap = cv2.VideoCapture(self.camera_num)
		self.kernel = np.ones((5,5),np.uint8)


		self.pts = deque(maxlen=32)

		self.frame_width = self.cap.get(3)
		self.frame_height = self.cap.get(4)
		self.mouse = BasicController()
		self.mouse.margin = (0.1, 0.3, 0.15, 0.15)

		self.camera_color = ''
		self.new_color = ''

		#self._notify_window = notify_window
		self._want_abort = 0
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
		dil_it = 3

		while True:

			if self._want_color_change == 1:
				std_out("while loop want to change color")
				self.camera_color = self.new_color
				self._want_color_change = 0
				color = self.set_color(self.camera_color)

			if self._want_abort == 1:
				std_out("while loop about to abort")
				cv2.destroyAllWindows()
				cv2.VideoCapture(self.camera_num).release()
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

			erode = cv2.erode(mask,self.kernel,iterations = ero_it)
			dil = cv2.dilate(mask,self.kernel,iterations = dil_it)
			opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)

			contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
										 cv2.CHAIN_APPROX_SIMPLE)[-2]
		
			#print len(contours)
			#sys.stdout.flush()

			if len(contours) > 0:
				max_con = max(contours, key=cv2.contourArea)
				((x,y), radius) = cv2.minEnclosingCircle(max_con)
				moments = cv2.moments(max_con)
				if moments["m00"] == 0:
					continue
				center = (int(moments["m10"] / moments["m00"]),
						  int(moments["m01"] / moments["m00"]))

				
				#draw circle around image
				
				#if radius > 10 and args.circle:
				#	cv2.circle(img, (int(x), int(y)), int(radius), (255,0,0), 2)
				#	cv2.circle(img, center, 5,(0,0,255), -1)
				#	pts.appendleft(center)

				#mouse movement
				
				x = center[0] / self.frame_width
				y = center[1] / self.frame_height
				self.mouse.move(x, y)

				#self.show_image()
				#cv2.imshow("input", img)

	def set_color(self, color):
		std_out("set color")
		return colors.color_dict.get(color,colors.hsv_blue)

	def change_color(self, color):
		self._want_color_change = 1
		self.new_color = color

		std_out("change color")

	def abort(self):
		self._want_abort = 1
		std_out("set abort")

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


		#self.Bind(wx.EVT_CLOSE, self.OnClose)

		'''
		self.cap = cv2.VideoCapture(0)
		self.kernel = np.ones((5,5),np.uint8)


		self.pts = deque(maxlen=32)

		self.frame_width = self.cap.get(3)
		self.frame_height = self.cap.get(4)
		self.mouse = BasicController()
		self.mouse.margin = (0.1, 0.3, 0.15, 0.15)
		'''


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

	def OnStop(self, event):
		if self.camera:
			self.camera.abort()

	def OnClicked(self, event):

		std_out("Clicked Color")
		
		if not self.camera:
			self.camera = CameraThread()

		id = event.GetEventObject().GetId()
		self.camera.change_color(colors.color_list[id])

		std_out(colors.color_list[id])
		#if self._curr_color == colors.color_list[id]:
		#	return
		#self._curr_color = colors.color_list[id] 
		#self.run_camera()

	def run_camera(self):
		pass
		
		'''camera_color = self._curr_color

		color = self.set_color(camera_color)


		ero_it = 2
		dil_it = 3


		while camera_color == self._curr_color:

			ret, img = self.cap.read()
			hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

			if camera_color != 'red':
				mask = cv2.inRange(hsv, color[0], color[1])

			#red special case
			else:
				mask0 = cv2.inRange(hsv, color[0][0], color[0][1])
				mask1 = cv2.inRange(hsv, color[1][0], color[1][1])
				mask = mask0 + mask1

			erode = cv2.erode(mask,self.kernel,iterations = ero_it)
			dil = cv2.dilate(mask,self.kernel,iterations = dil_it)
			opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)

			contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
										 cv2.CHAIN_APPROX_SIMPLE)[-2]
		
			#print len(contours)
			#sys.stdout.flush()

			if len(contours) > 0:
				max_con = max(contours, key=cv2.contourArea)
				((x,y), radius) = cv2.minEnclosingCircle(max_con)
				moments = cv2.moments(max_con)
				if moments["m00"] == 0:
					continue
				center = (int(moments["m10"] / moments["m00"]),
						  int(moments["m01"] / moments["m00"]))

				
				#draw circle around image
				
				if radius > 10 and args.circle:
					cv2.circle(img, (int(x), int(y)), int(radius), (255,0,0), 2)
					cv2.circle(img, center, 5,(0,0,255), -1)
					pts.appendleft(center)

				#mouse movement
				
				x = center[0] / self.frame_width
				y = center[1] / self.frame_height
				self.mouse.move(x, y)

				#self.show_image()
				cv2.imshow("input", img)

	def set_color(self, color):
		return colors.color_dict.get(color,colors.hsv_blue)
	'''

	def show_image(self):
		#cv2.imshow("input", img)
		#cv2.imshow("opening", opening)
		#cv2.imshow("mask", mask)
		#cv2.imshow("dil", dil)
		#cv2.imshow("erode", erode)
		#cv2.imshow("erosion and dilation", morph)
		#res = cv2.bitwise_and(img, img, mask= mask)
		#cv2.imshow("res " + args.color, res)
		return

	
class ColorApp(wx.App):
	def OnInit(self):
		self.frame = ColorFrame()
		self.frame.Show(True)
		return True



