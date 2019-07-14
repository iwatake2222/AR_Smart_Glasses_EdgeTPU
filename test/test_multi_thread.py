# -*- coding: utf-8 -*-
import time
import sys
import math
import numpy as np
from PIL import Image
import cv2
from threading import Thread,  Lock

WIDTH = 320
HEIGHT = 240
g_is_exit = False

def func_capture(buff_cap2disp, lock_cap2disp, buff_cap2det, lock_cap2det):
	print("func_capture: start")
	global g_is_exit
	cnt = 0
	while(True):
		### Capture image
		cnt = cnt + 1
		if cnt > 300:
			cnt = 0
		time_start = time.time()
		# print("func_capture")
		# time.sleep(0.03)
		img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
		cv2.rectangle(img, (cnt, 100), (cnt + 10, 100 + 10), (255, 0, 0), -1)

		### Send captured buffer to DISPLAY
		lock_cap2disp.acquire()
		for i in range(len(buffer_cap2disp)):
			# delete all of the old buffers (no need to release memory explicitly (GC will be done automatically))
			_ = buffer_cap2disp.pop()
		buff_cap2disp.append(img)
		lock_cap2disp.release()

		### Send captured buffer to DETECTION
		lock_cap2det.acquire()
		for i in range(len(buff_cap2det)):
			# delete all of the old buffers (no need to release memory explicitly (GC will be done automatically))
			_ = buff_cap2det.pop()
		buff_cap2det.append(img)
		lock_cap2det.release()

		if g_is_exit == True:
			break
		time_end = time.time()
		# print ("Capture:{0}".format((time_end - time_start) * 1000) + "[msec]")

	print("func_capture: exit")

def func_detection(buffer_cap2det, lock_cap2det, result_det2disp, lock_det2disp):
	print("func_detection: start")
	global g_is_exit
	buff = None
	while True:
		time_start = time.time()
		# print("func_detection")

		### Receive captured image from CAPTURE
		lock_cap2det.acquire()
		if len(buffer_cap2det) > 0:
			buff = buffer_cap2det.pop()
		lock_cap2det.release()
		
		if buff is not None:
			### Detect objects
			# time.sleep(0.1)
			results = [[10,20,30,40,"abc"], [40,50,60,70,"def"]]
			
			### Send detection results to DISPLAY
			lock_det2disp.acquire()
			for i in range(len(result_det2disp)):
				# delete all of the old buffers (no need to release memory explicitly (GC will be done automatically))
				_ = result_det2disp.pop()
			result_det2disp.append(results)
			lock_det2disp.release()
		
		if g_is_exit == True:
			break

		time_end = time.time()
		# print ("Detection:{0}".format((time_end - time_start) * 1000) + "[msec]")

	print("func_detection: exit")

def func_display(buffer_cap2disp, lock_cap2disp, result_det2disp, lock_det2disp):
	print("func_display: start")
	global g_is_exit
	buff = None
	results = None
	while True:
		time_start = time.time()
		# print("func_display")

		### Receive captured image from CAPTURE
		lock_cap2disp.acquire()
		if len(buffer_cap2disp) > 0:
			buff = buffer_cap2disp.pop()
		lock_cap2disp.release()
		
		### Receive detection results from DETECTION
		lock_det2disp.acquire()
		if len(result_det2disp) > 0:
			results = result_det2disp.pop()
		lock_det2disp.release()

		### Display image
		if buff is not None:
			# Draw detected results
			if results is not None:
				# print("results: ", results)
				for obj in results:
					cv2.rectangle(buff, (obj[0], obj[1]), (obj[2], obj[3]), (255, 0, 0), 1)
					cv2.putText(buff, obj[4], (obj[0], obj[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), thickness=3)
					cv2.putText(buff, obj[4], (obj[0], obj[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), thickness=2)

			cv2.imshow('img', buff)
			# time.sleep(0.05)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break
		
		time_end = time.time()
		# print ("Display:{0}".format((time_end - time_start) * 1000) + "[msec]")

	cv2.destroyAllWindows()
	g_is_exit = True
	print("func_display: exit")


if __name__ == "__main__":
	buffer_cap2disp = []
	lock_cap2disp = Lock()
	buffer_cap2det = []
	lock_cap2det = Lock()
	result_det2disp = []
	lock_det2disp = Lock()

	threads = []

	# Start CAPTURE thread
	t = Thread(target=func_capture, args=(buffer_cap2disp, lock_cap2disp, buffer_cap2det, lock_cap2det))
	t.start()
	threads.append(t)

	# Start DETECTION thread
	t = Thread(target=func_detection, args=(buffer_cap2det, lock_cap2det, result_det2disp, lock_det2disp))
	t.start()
	threads.append(t)

	# Start DISPLAY thread
	t = Thread(target=func_display, args=(buffer_cap2disp, lock_cap2disp, result_det2disp, lock_det2disp))
	t.start()
	threads.append(t)


	for t in threads:
		t.join()

