# -*- coding: utf-8 -*-
import time
import sys
import math
from PIL import Image
import cv2

'''
Increase VRAM to 256
export DISPLAY=:0
sudo modprobe bcm2835-v4l2
# sudo rmmod bcm2835-v4l2
# sudo modprobe bcm2835-v4l2 gst_v4l2src_is_broken=1
# v4l2-ctl -d /dev/video0 --list-formats-ext

gst-launch-1.0 videotestsrc! autovideosink
gst-launch-1.0 videotestsrc! ximagesink

gst-launch-1.0 v4l2src device=/dev/video0 ! autovideosink
gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw, width=1280, height=720, format=NV12 ! videoconvert ! autovideosink
gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw, width=1280, height=720, format=NV12 ! videoscale ! video/x-raw, width=320, height=240 ! videoconvert ! autovideosink
gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw, width=1640, height=1232, format=NV12 ! videoscale ! video/x-raw, width=320, height=240 ! videoconvert ! autovideosink
gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw, width=3280, height=2464, format=NV12 ! videoscale ! video/x-raw, width=320, height=240 ! videoconvert ! autovideosink
'''

# 速いけど画角狭い
# cap = cv2.VideoCapture(0)

cap = cv2.VideoCapture("/dev/video0")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 速いけど画角狭い
# cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! video/x-raw, width=1280, height=720, format=NV12 ! videoscale ! video/x-raw, width=320, height=240 ! videoconvert  ! appsink")

# 遅い
# cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! video/x-raw, width=1640, height=1232, format=NV12 ! videoscale ! video/x-raw, width=320, height=240 ! videoconvert ! appsink") 

if (cap.isOpened() == False):
	print("cannot open")
	sys.exit(1)

fps_start = time.time()
cnt = 0
while(cap.isOpened()):
	cnt = cnt + 1
	time_start = time.time()

	ret, img = cap.read()
	if ret == False:
		break
	time_capture = time.time()

	cv2.imshow('img', img)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
	time_display = time.time()

	print ("Total:{0}".format((time_display - time_start) * 1000) + "[msec]")
	print ("Capture:{0}".format((time_capture - time_start) * 1000) + "[msec]")
	print ("Display:{0}".format((time_display - time_capture) * 1000) + "[msec]")

print ("fps:{0}".format(cnt / (time.time() - fps_start)))

cap.release()
cv2.destroyAllWindows()

