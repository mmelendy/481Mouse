import cv2
import numpy as np
from collections import deque
import wx
import sys

import colors
#from interface import ColorApp
from mouse import BasicController

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

		#self.Bind(wx.EVT_CLOSE, self.OnClose)

		self.cap = cv2.VideoCapture(0)
		self.kernel = np.ones((5,5),np.uint8)


		self.pts = deque(maxlen=32)

		self.frame_width = self.cap.get(3)
		self.frame_height = self.cap.get(4)
		self.mouse = BasicController()
		self.mouse.margin = (0.1, 0.3, 0.15, 0.15)
		


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

	def OnClicked(self, event):
		id = event.GetEventObject().GetId()
		if self._curr_color == colors.color_list[id]:
			return
		self._curr_color = colors.color_list[id] 
		self.run_camera()

	def run_camera(self):
		camera_color = self._curr_color

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

				
				'''#draw circle around image
				if radius > 10 and args.circle:
					cv2.circle(img, (int(x), int(y)), int(radius), (255,0,0), 2)
					cv2.circle(img, center, 5,(0,0,255), -1)
					pts.appendleft(center)'''

				#mouse movement
				x = center[0] / self.frame_width
				y = center[1] / self.frame_height
				self.mouse.move(x, y)

				#self.show_image()
				cv2.imshow("input", img)

	def set_color(self, color):
		return colors.color_dict.get(color,colors.hsv_blue)

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


	def OnClose(self):
		cv2.destroyAllWindows()
		cv2.VideoCapture(0).release()
	
class ColorApp(wx.App):
	def OnInit(self):
		self.frame = ColorFrame()
		self.frame.Show(True)
		return True