import wx
import sys
import colors

class ColorFrame(wx.Frame):
	def __init__(self):
		super(ColorFrame, self).__init__(None,-1,"Color Selector",wx.Point(100,100),wx.Size(250,400))
		self._panel = wx.Panel(self)
		self._box = wx.BoxSizer(wx.VERTICAL)
		
		self._curr_color = 'blank'
		
		self.createDisplay()	

		self._panel.SetSizer(self._box)
		self.Center()
		#self.Show(True)	

	@property
	def curr_color(self):
		return self._curr_color

	@curr_color.setter
	def curr_color(self, value):
		self._curr_color = value
		print self._curr_color
		sys.stdout.flush()

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
		self._curr_color = colors.color_list[id] 
		#c = colors.color_list[id]
		#self.curr_color(c)

class ColorApp(wx.App):
	def OnInit(self):
		# Create an instance of our customized Frame class
		self.frame = ColorFrame()
		self.frame.Show(True)
		return True



#app = ColorApp()
#app.MainLoop()
