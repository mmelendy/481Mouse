import cv2
import sys
import argparse
import colors
import numpy as np
from collections import deque
from pymouse import PyMouse

def main(argv): 
    #capture from camera at location 0
    cap = cv2.VideoCapture(0)
    kernel = np.ones((5,5),np.uint8)
    get_camera_values(cap)

    parser = argparse.ArgumentParser(description='HSV Color Space of a Single Color')
    parser.add_argument("color", help="choose common color to start, bad color defaults blue")
    parser.add_argument("--circle", "-c", help="draw circle around object", action="store_true")
    args = parser.parse_args()
    color = set_color(args.color)
    #dont use red yet

    #cap.set(3, 1280)
    #cap.set(4,720)
    
    pts = deque(maxlen=32)
    counter = 0

    mouse = PyMouse()
    screen_size = mouse.screen_size()
    screen_ratio = (float(screen_size[0] / cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    float(screen_size[1] / cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    #sys.stdout.flush()
    
    while True:
        ret, img = cap.read()
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        mask = cv2.inRange(hsv, color[0], color[1])

        res = cv2.bitwise_and(img, img, mask= mask)

        opening = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel)
        #erosion = cv2.erode(mask,kernel,iterations = 2)
        #ero_dil = cv2.dilate(erosion,kernel,iterations = 3)
        ero_dil = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


        contours = cv2.findContours(ero_dil.copy(), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)[-2]
        
        if len(contours) > 0:
            max_con = max(contours, key=cv2.contourArea)
            ((x,y), radius) = cv2.minEnclosingCircle(max_con)
            moments = cv2.moments(max_con)
            center = (int(moments["m10"] / moments["m00"]),
                      int(moments["m01"] / moments["m00"]))

            #draw circle around image
            if radius > 10 and args.circle:
                cv2.circle(img, (int(x), int(y)), int(radius), (255,0,0), 2)
                cv2.circle(img, center, 5,(0,0,255), -1)
                pts.appendleft(center)

            #mouse movement
            #print "Width ", screen_ratio[0] * center[0]
            #print "Height ", screen_ratio[1] * center[1]
            width = abs(int(screen_ratio[0] * center[0]) - screen_size[0])
            height = int(screen_ratio[1] * center[1])
            mouse.move(width, height) 
               
            
        cv2.imshow("input", img)

        #cv2.imshow("opening", opening)
        #cv2.imshow("input", img)
        #cv2.imshow("mask", mask)
        #cv2.imshow("erosion and dilation", ero_dil)
        #cv2.imshow("res " + args.color, res)

        counter += 1
             
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    cv2.VideoCapture(0).release()


def get_camera_values(cap):
    test = cap.get(cv2.CAP_PROP_POS_MSEC)
    ratio = cap.get(cv2.CAP_PROP_POS_AVI_RATIO)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
    contrast = cap.get(cv2.CAP_PROP_CONTRAST)
    saturation = cap.get(cv2.CAP_PROP_SATURATION)
    hue = cap.get(cv2.CAP_PROP_HUE)
    gain = cap.get(cv2.CAP_PROP_GAIN)
    exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
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

if __name__ == '__main__':
    main(sys.argv)



