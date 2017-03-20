import sys
import cv2
import math
import subprocess

subprocess.check_output("rm -rf frames/*",shell=True)
vidCap = cv2.VideoCapture(u' '.join(sys.argv[1:]))
print sys.argv[1:]
frameRate = vidCap.get(cv2.CAP_PROP_FPS)
captureIntervals = 10
while (vidCap.isOpened()):
    frameId = vidCap.get(cv2.CAP_PROP_POS_FRAMES)  # starting position is 0.. returns current frame position
    success, image = vidCap.read()
    if (success != True):
        break
    if (frameId % math.floor(captureIntervals * frameRate) == 0):  # 1 frame in 1 sec
        millisec = vidCap.get(cv2.CAP_PROP_POS_MSEC)
        print 'Read a new frame : ', str(millisec)
        cv2.imwrite("./frames/frame%d.jpg" % int(millisec), image)  # save frame as JPEG file
vidCap.release()
