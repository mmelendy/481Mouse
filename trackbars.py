import cv2
import numpy as np
import sys

def nothing(x):
    pass


#defaults to RBG trackbars
#rgb for rgb trackbars, hsv for hsv trackbars
def main(argv):

    #Capture video from the stream
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('Colorbars') #Create a window named 'Colorbars'
    wnd = 'Track Bars'

    if len(argv) == 0 or argv[0] == 'rgb':
        rl = 'Red Low'
        rh = 'Red High'
        gl = 'Green Low'
        gh = 'Green High'
        bl = 'Blue Low'
        bh = 'Blue High'
        

        bars = [rl, rh, gl, gh, bl, bh]

        #begin creating trackbars for rgb
        cv2.createTrackbar(rl, wnd,0,255,nothing)
        cv2.createTrackbar(rh, wnd,0,255,nothing)
        cv2.createTrackbar(gl, wnd,0,255,nothing)
        cv2.createTrackbar(gh, wnd,0,255,nothing)
        cv2.createTrackbar(bl, wnd,0,255,nothing)
        cv2.createTrackbar(bh, wnd,0,255,nothing)

    elif len(argv) > 0 and argv[0] == 'hsv':
        
        #assign strings for ease of coding
        hh='Hue High'
        hl='Hue Low'
        sh='Saturation High'
        sl='Saturation Low'
        vh='Value High'
        vl='Value Low'
        bars = [hl,hh,sl,sh,vl,vh]

        #Begin Creating trackbars for hsv
        cv2.createTrackbar(hl, wnd,0,179,nothing)
        cv2.createTrackbar(hh, wnd,0,179,nothing)
        cv2.createTrackbar(sl, wnd,0,255,nothing)
        cv2.createTrackbar(sh, wnd,0,255,nothing)
        cv2.createTrackbar(vl, wnd,0,255,nothing)
        cv2.createTrackbar(vh, wnd,0,255,nothing)

    else:
        print 'stop trying to break the program\n \
                insert nothing for rgb, \'rgb\' for \
                rgb or \'hsv\' for hsv!'

    #begin our 'infinite' while loop
    while(1):
        #read the streamed frames (we previously named this cap)
        _,frame=cap.read()
     
        #it is common to apply a blur to the frame
        frame=cv2.GaussianBlur(frame,(5,5),0)
     
        #convert from a BGR stream to an HSV stream
        hsv=cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        bar1low=cv2.getTrackbarPos(bars[0],wnd)
        bar1high=cv2.getTrackbarPos(bars[1],wnd)
        bar2low=cv2.getTrackbarPos(bars[2],wnd)
        bar2high=cv2.getTrackbarPos(bars[3],wnd)
        bar3low=cv2.getTrackbarPos(bars[4],wnd)
        bar3high=cv2.getTrackbarPos(bars[5],wnd)

        rangelow = np.array([bar1low,bar2low,bar3low])
        rangehigh = np.array([bar1high,bar2high,bar3high])

        #create a mask for that range
        if len(argv) > 1 and argv[0] == 'hsv':
            mask = cv2.inRange(hsv,rangelow, rangehigh)
        else:
            mask = cv2.inRange(frame,rangelow,rangehigh)


        res = cv2.bitwise_and(frame,frame, mask =mask)
        hsv_res = cv2.bitwise_and(hsv,hsv, mask =mask)
     
        cv2.imshow(wnd, res)
        cv2.imshow("hsv", hsv_res)
        k = cv2.waitKey(5) & 0xFF
        if k == ord('q'):
            break
     
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main(sys.argv[1:])
    