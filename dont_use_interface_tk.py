import Tkinter
import colors
import sys

class ColorSelector():

	def __init__(self):
		self.colors = ['red','yellow','green','cyan','blue']
		self.top = Tkinter.Tk()
		self._curr_color = ''
		self._buttons = []


	@property
	def curr_color(self):
		return self._curr_color

	@curr_color.setter
	def curr_color(self, value):
		self._curr_color = value
		print self._curr_color
		sys.stdout.flush()
	
	def createDisplay(self):
		background_color = '#e5fcfa'
		self.top.config(bg=background_color)
		self.frame = Tkinter.Frame(self.top,bg=background_color)

		directions = Tkinter.Label(self.top,text="Choose a color that matches your finger cloth")
		directions.pack()


		for key in self.colors:
			print key
		#for button in self._buttons:
		#	button.pack(pady=1)

			sys.stdout.flush()
			button = Tkinter.Button(self.frame,bg=key,
									padx=40,pady=20)#,command=lambda: curr_color(self,key))
			#self._buttons.insert(0,button)
			#self.frame.
			button.pack(pady=1)
		self.frame.pack()
		self.top.mainloop()



c = ColorSelector()
c.createDisplay()
