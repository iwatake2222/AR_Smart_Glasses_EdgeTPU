# -*- coding: utf-8 -*-
import time
import sys
import math
from PIL import Image
import cv2
import OLED_SEPS525_SPI_BGR565
import array
import numpy as np
import struct

'''
sudo modprobe bcm2835-v4l2
'''

display = OLED_SEPS525_SPI_BGR565.OLED_SEPS525_SPI_BGR565()
display.init()

cap = cv2.VideoCapture("k-on.mp4")
# cap = cv2.VideoCapture(0)
if (cap.isOpened() == False):
	print("cannot open")
	sys.exit(1)

while(cap.isOpened()):
	start = time.time()
	ret, img = cap.read()
	if ret == False:
		break

	img = cv2.resize(img, (160, 128))
	data = cv2.cvtColor(img, cv2.COLOR_RGB2BGR565)	# for some reasons, RGB not BGR
	data = data.flatten()
	data = struct.unpack('>' + 'H' * (int)(len(data)/2), data)	# fix endian (AB CD -> CD AB)
	data = struct.pack('H' * len(data), *data)
	display.draw_bgr565(data)

	elapsed_time = time.time() - start
	print ("elapsed_time:{0}".format(elapsed_time) + "[sec]")

	# cv2.imshow('img', img)
	# if cv2.waitKey(1) & 0xFF == ord('q'):
	# 	break

cap.release()
cv2.destroyAllWindows()

display.finalize()
