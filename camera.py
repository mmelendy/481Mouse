import cv2
import sys
import numpy as np

#capture from camera at location 0
cap = cv2.VideoCapture(1)
# Change the camera setting using the set() function
# cap.set(cv2.cv.CV_CAP_PROP_EXPOSURE, -6.0)
# cap.set(cv2.cv.CV_CAP_PROP_GAIN, 4.0)
# cap.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS, 144.0)
# cap.set(cv2.cv.CV_CAP_PROP_CONTRAST, 27.0)
# cap.set(cv2.cv.CV_CAP_PROP_HUE, 13.0) # 13.0
# cap.set(cv2.cv.CV_CAP_PROP_SATURATION, 28.0)
# Read the current setting from the camera
test = cap.get(cv2.cv.CV_CAP_PROP_POS_MSEC)
ratio = cap.get(cv2.cv.CV_CAP_PROP_POS_AVI_RATIO)
frame_rate = cap.get(cv2.cv.CV_CAP_PROP_FPS)
width = cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
brightness = cap.get(cv2.cv.CV_CAP_PROP_BRIGHTNESS)
contrast = cap.get(cv2.cv.CV_CAP_PROP_CONTRAST)
saturation = cap.get(cv2.cv.CV_CAP_PROP_SATURATION)
hue = cap.get(cv2.cv.CV_CAP_PROP_HUE)
gain = cap.get(cv2.cv.CV_CAP_PROP_GAIN)
exposure = cap.get(cv2.cv.CV_CAP_PROP_EXPOSURE)
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
while True:
    ret, img = cap.read()
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([110,50,50])
    upper_blue = np.array([130,255,255])

    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    res = cv2.bitwise_and(img, img, mask= mask)
    
    cv2.imshow("input", img)
    cv2.imshow("mask", mask)
    #cv2.imshow("res", res)
    
    key = cv2.waitKey(10) & 0xFF
    if key == 27:
        break

cv2.destroyAllWindows()
cv2.VideoCapture(0).release()

