import sys

import image_proc

def main(argv):

	app = image_proc.ColorApp()

	app.MainLoop()



if __name__ == '__main__':
    main(sys.argv)
