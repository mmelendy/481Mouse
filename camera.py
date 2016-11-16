import cv2
import sys
import argparse
import numpy as np
import math
from collections import deque
import threading

import colors
#from interface import ColorApp
from mouse import BasicController

def main(argv): 
    
    cap = cv2.VideoCapture(0)
    kernel = np.ones((5,5),np.uint8)
    #get_camera_values(cap)

    parser = argparse.ArgumentParser(description='HSV Color Space of a Single Color')
    parser.add_argument("color", help="choose common color to start, bad color defaults blue")
    parser.add_argument("--circle", "-c", help="draw circle around object", action="store_true")
    parser.add_argument("--bars", "-b", help="add trackbars for erosion and dilation", action="store_true")
    args = parser.parse_args()
    color = set_color(args.color)
    

    #app = ColorApp()
    #app.MainLoop()


    #print app.frame.curr_color
    #sys.stdout.flush()

    frame_width = cap.get(3)
    frame_height = cap.get(4)
    mouse = BasicController()
    mouse.margin = (0.1, 0.2, 0.15, 0.15)

    ero_it = 2
    dil_it = 1
    if args.bars:
        cv2.namedWindow("mask")
        cv2.createTrackbar("Erosion", "mask", ero_it, 10, nothing)
        cv2.createTrackbar("Dilation", "mask", dil_it, 10, nothing)

    button_size = 30
    current_l_button_size = 30
    current_r_button_size = 30

    right_button_color = "blue"
    right_button_flag = False

    left_button_color = "yellow"
    left_button_flag = False

    while True:
        ret, img = cap.read()
        img = cv2.GaussianBlur(img, (11,11), 0)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        mask = get_mask(hsv, args.color)

        #get trackbar positions
        if args.bars:
            ero_it = cv2.getTrackbarPos("Erosion", "mask")
            dil_it = cv2.getTrackbarPos("Dilation", "mask")

        mask = cv2.erode(mask,kernel,iterations = ero_it)
        mask = cv2.dilate(mask,kernel,iterations = dil_it)

        contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)[-2]
        #mouse movement
        if len(contours) > 0:
            max_con = max(contours, key=cv2.contourArea)
            ((x,y), radius) = cv2.minEnclosingCircle(max_con)
            moments = cv2.moments(max_con)
            if moments["m00"] == 0:
                continue
            center = (int(moments["m10"] / moments["m00"]),
                      int(moments["m01"] / moments["m00"]))

            scaled_x = center[0] / frame_width
            scaled_y = center[1] / frame_height
            mouse.move(scaled_x, scaled_y)

            if args.circle:
                cv2.circle(img, (int(x), int(y)), int(radius), (255,0,0), 2)


        # get a smaller range of glove
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
        if len(circles) > 0:
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
            # if radius <= 15:
            #     continue

            black = np.zeros((int(frame_height), int(frame_width), 3), np.uint8)
            cv2.circle(black, (int(x), int(y)), int(radius), (255,255,255), -1)
            glove = cv2.bitwise_and(hsv, black)
            # glove = cv2.cvtColor(glove, cv2.COLOR_BGR2HSV)

            cv2.imshow("glove", glove)

            left_mb = get_mask(glove, left_button_color)
            left_mb = cv2.erode(left_mb,kernel,iterations = 2)
            left_mb = cv2.dilate(left_mb,kernel,iterations = 1)

            left_contour = cv2.findContours(left_mb.copy(), cv2.RETR_EXTERNAL,
                                         cv2.CHAIN_APPROX_SIMPLE)[-2]

            right_mb = get_mask(glove, right_button_color)
            right_mb = cv2.erode(right_mb,kernel,iterations = 2)
            right_mb = cv2.dilate(right_mb,kernel,iterations = 1)

            right_contour = cv2.findContours(right_mb.copy(), cv2.RETR_EXTERNAL,
                                         cv2.CHAIN_APPROX_SIMPLE)[-2]

            cv2.imshow("left_mb", left_mb)
            cv2.imshow("right_mb", right_mb)
            
            l_radius = 0
            l_radius, current_l_button_size, left_button_flag = \
                    detect_button(left_contour, l_radius, left_button_flag, \
                                current_l_button_size, button_size, "left")

            r_radius = 0
            r_radius, current_r_button_size, right_button_flag = \
                    detect_button(right_contour, r_radius, right_button_flag, \
                         current_r_button_size, button_size, "right")

        # cv2.imshow("mask", mask)
        #cv2.imshow("input", img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    cv2.VideoCapture(1).release()

def detect_button(contour, radius, button_flag, current_size, button_size, button):

    if len(contour) > 0:
        max_con = max(contour, key=cv2.contourArea)
        ((x,y), radius) = cv2.minEnclosingCircle(max_con)

    if not button_flag:
        if radius > button_size: 
            button_flag = True
            current_size  = radius
    else:
        if radius < current_size * 0.5:
            # mouse.click(True, False)
            button_flag = False
            current_size = button_size
            print button

            sys.stdout.flush()
        else:
            current_size = radius

    return radius, current_size, button_flag


def get_mask(hsv, color):
    color_range = colors.color_dict.get(color, colors.hsv_blue)
    if color != 'red':
        return cv2.inRange(hsv, color_range[0], color_range[1])
    else: 
        return cv2.inRange(hsv, color_range[0][0], color_range[0][1]) \
             + cv2.inRange(hsv, color_range[1][0], color_range[1][1])

def get_camera_values(cap):
    test = cap.get(0) #cv2.cv.CV_CAP_PROP_POS_MSEC
    ratio = cap.get(1) #cv2.cv.CV_CAP_PROP_POS_AVI_RATIO
    frame_rate = cap.get(2) #cv2.cv.CV_CAP_PROP_FPS
    width = cap.get(3) #cv2.cv.CV_CAP_PROP_FRAME_WIDTH
    height = cap.get(4) #cv2.cv.CV_CAP_PROP_FRAME_HEIGHT
    brightness = cap.get(5) #cv2.cv.CV_CAP_PROP_BRIGHTNESS
    contrast = cap.get(6) #cv2.cv.CV_CAP_PROP_CONTRAST
    saturation = cap.get(7) #cv2.cv.CV_CAP_PROP_SATURATION
    hue = cap.get(8) #cv2.cv.CV_CAP_PROP_HUE
    gain = cap.get(9) #cv2.cv.CV_CAP_PROP_GAIN
    exposure = cap.get(10) #cv2.cv.CV_CAP_PROP_EXPOSURE
    print("Test: ", test)
    print("Ratio: ", ratio)
    print("Frame Rate: ", frame_rate)
    print("Height: ", height)
    print("Width: ", width)
    print("Brightness: ", brightness)
    print("Contrast: ", contrast)
    print("Saturation: ", saturation)
    print("Hue: ", hue)
    print("Gain: ", gain)
    print("Exposure: ", exposure)
    sys.stdout.flush()

def set_color(color):
    return colors.color_dict.get(color,colors.hsv_blue)

def nothing(x):
    pass

if __name__ == '__main__':
    main(sys.argv)



