import numpy as np

#hsv color space for different colors

hsv_red_l = [np.array([0,50,50]), np.array([10,255,255])]

hsv_red_h = [np.array([170,50,50]), np.array([179,255,255])]

hsv_red = [hsv_red_l, hsv_red_h]

hsv_yellow = [np.array([20,50,50]), np.array([40,255,255])]

hsv_green = [np.array([50,50,50]), np.array([70,255,255])]

hsv_cyan = [np.array([90,50,50]), np.array([110,255,255])]

hsv_blue = [np.array([110,50,50]), np.array([130,255,255])]

hsv_purple = [np.array([130,50,50]), np.array([150,255,255])]

color_dict = {
        'red' : hsv_red,
        'yellow' : hsv_yellow,
        'green' : hsv_green,
        'cyan' : hsv_cyan,
        'blue' : hsv_blue,
        'purple' : hsv_purple
        }

color_list = ['yellow','green','cyan','blue', 'purple']
