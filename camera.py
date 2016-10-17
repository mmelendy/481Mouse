import cv2
import sys
import argparse
import colors
import numpy as np
from collections import deque
from pymouse import PyMouse

def main(argv): 
    
    cap = cv2.VideoCapture(1)
    kernel = np.ones((5,5),np.uint8)
    #get_camera_values(cap)

    parser = argparse.ArgumentParser(description='HSV Color Space of a Single Color')
    parser.add_argument("color", help="choose common color to start, bad color defaults blue")
    parser.add_argument("--circle", "-c", help="draw circle around object", action="store_true")
    parser.add_argument("--bars", "-b", help="add trackbars for erosion and dilation", action="store_true")
    args = parser.parse_args()
    color = set_color(args.color)
    
    pts = deque(maxlen=32)

    mouse = PyMouse()
    screen_size = mouse.screen_size()
    screen_ratio = (float(screen_size[0] / cap.get(3)),
                    float(screen_size[1] / cap.get(4)))
    
    if args.bars:
        cv2.namedWindow("mask")
        cv2.createTrackbar("Erosion", "mask", 0, 10, nothing)
        cv2.createTrackbar("Dilation", "mask", 0, 10, nothing)

    ero_it = 2
    dil_it = 3

    while True:
        ret, img = cap.read()
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
     
        #red special scase
        if args.color != 'red': 
            mask = cv2.inRange(hsv, color[0], color[1])
        else:
            mask0 = cv2.inRange(hsv, color[0][0], color[0][1])
            mask1 = cv2.inRange(hsv, color[1][0], color[1][1])
            mask = mask0 + mask1

        #get trackbar positions, iterations cant be 0
        if args.bars:
            ero_it = cv2.getTrackbarPos("Erosion", "mask")
            if ero_it == 0:
                ero_it = 1
            dil_it = cv2.getTrackbarPos("Dilation", "mask")
            if dil_it == 0:
                dil_it = 1            

        #opening = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel)
        erode = cv2.erode(mask,kernel,iterations = ero_it)
        dil = cv2.dilate(mask,kernel,iterations = dil_it)
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)[-2]
        
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
            width = abs(int(screen_ratio[0] * center[0]) - screen_size[0])
            height = int(screen_ratio[1] * center[1])
            mouse.move(width, height) 
               
            
        cv2.imshow("input", img)

        #list of various views
        #cv2.imshow("opening", opening)
        #cv2.imshow("mask", mask)
        #cv2.imshow("dil", dil)
        #cv2.imshow("erode", erode)
        #cv2.imshow("erosion and dilation", morph)
        #res = cv2.bitwise_and(img, img, mask= mask)
        #cv2.imshow("res " + args.color, res)
             
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    cv2.VideoCapture(0).release()


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



