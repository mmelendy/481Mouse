import numpy as np

#hsv color space for different colors

hsv_red_l = [np.array([0,50,50]), np.array([10,255,255])]

hsv_red_h = [np.array([170,50,50]), np.array([179,255,255])]

hsv_yellow = [np.array([80,50,50]), np.array([100,255,255])]

hsv_green = [np.array([50,50,50]), np.array([70,255,255])]

hsv_blue = [np.array([110,50,50]), np.array([130,255,255])]

hsv_cyan = [np.array([78,50,50]), np.array([116,255,255])]

color_dict = {
        'red' : [hsv_red_l, hsv_red_h],
        'yellow' : hsv_yellow,
        'green' : hsv_green,
        'blue' : hsv_blue,
        'cyan' : hsv_cyan
        }
