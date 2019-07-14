# -*- coding: utf-8 -*-
import time
import sys
import os
import math
import numpy as np
from PIL import Image
import cv2
from threading import Thread, Lock
import OLED_SEPS525_SPI_BGR565
import array
import struct
from edgetpu.detection.engine import DetectionEngine
from label_coco import label2string

MODEL_NAME = "mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite"
MODEL_WIDTH = 300
MODEL_HEIGHT = 300
CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 480
DISPLAY_WIDTH = 160
DISPLAY_HEIGHT = 128

g_is_exit = False
g_is_shutdown = False
g_display_mode = 1

def func_capture(buff_cap2disp, lock_cap2disp, buff_cap2det, lock_cap2det):
	global g_is_exit

	# workaround: 一度'0'で開かないと、/dev/video0開くときにfreeze。原因不明
	cap = cv2.VideoCapture(0)
	cap.release()

	cap = cv2.VideoCapture("/dev/video0")
	cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
	# cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! video/x-raw, width=1280, height=720, format=NV12 ! videoscale ! video/x-raw, width=(int)%d, height=(int)%d ! videoconvert  ! appsink" % (CAPTURE_WIDTH, CAPTURE_HEIGHT))

	if cap.isOpened() == False:
		print("cannot open")
		sys.exit(1)

	while True:
		### Capture image
		time_start = time.time()
		ret, img = cap.read()
		if ret == False:
			break

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

def cv2pil(image_cv):
	image_cv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
	image_pil = Image.fromarray(image_cv)
	image_pil = image_pil.convert('RGB')
	return image_pil

def func_detection(buffer_cap2det, lock_cap2det, result_det2disp, lock_det2disp):
	global g_is_exit
	engine = DetectionEngine(MODEL_NAME)
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
			pil_img = cv2pil(buff)
			ans = engine.DetectWithImage(pil_img, threshold=0.5, keep_aspect_ratio=False, relative_coord=True, top_k=10)
			results = []
			if ans:
				for obj in ans:
					# print ('-----------------------------------------')
					# print('label = ', label2string[obj.label_id])
					# print('score = ', obj.score)
					box = obj.bounding_box.flatten().tolist()
					# print ('box = ', box)
					results.append([box[0], box[1], box[2], box[3], label2string[obj.label_id]])
			
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
	global g_is_exit
	global g_display_mode
	display = OLED_SEPS525_SPI_BGR565.OLED_SEPS525_SPI_BGR565()
	display.init()
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
			buff = cv2.resize(buff, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
			if g_display_mode == 3:
				# mode3: display icons only
				buff = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
			# Draw detected results
			if results is not None:
				# print("results: ", results)
				for obj in results:
					x0 = (int)(obj[0] * DISPLAY_WIDTH)
					y0 = (int)(obj[1] * DISPLAY_HEIGHT)
					x1 = (int)(obj[2] * DISPLAY_WIDTH)
					y1 = (int)(obj[3] * DISPLAY_HEIGHT)
					label = obj[4]
					if g_display_mode == 1:
						### mode1: draw bounding box
						cv2.rectangle(buff, (x0, y0), (x1, y1), (255, 0, 0), 1)
						y0 = y0 + 12
						if y0 > DISPLAY_HEIGHT:
							y0 = DISPLAY_HEIGHT
						cv2.putText(buff, label, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), thickness=3)
						cv2.putText(buff, label, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), thickness=2)
					elif g_display_mode == 2 or g_display_mode == 3:
						### mode2,3: icon overlay
						if os.path.exists("icons/" + label + ".jpg"):
							img_icon = cv2.imread("icons/" + label + ".jpg")
							img_icon = cv2.resize(img_icon, (x1 - x0, y1 - y0))
							buff[y0:y0+img_icon.shape[0], x0:x0+img_icon.shape[1]] = img_icon
						else:
							cv2.rectangle(buff, (x0, y0), (x1, y1), (255, 0, 0), 1)

			data = cv2.cvtColor(buff, cv2.COLOR_RGB2BGR565)	# for some reasons, RGB not BGR
			data = data.flatten()
			data = struct.unpack('>' + 'H' * (int)(len(data)/2), data)	# fix endian (AB CD -> CD AB)
			data = struct.pack('H' * len(data), *data)
			display.draw_bgr565(data)

			# cv2.imshow('img', buff)
			# if cv2.waitKey(1) & 0xFF == ord('q'):
			 	# g_is_exit = True

		if g_is_exit == True:
			break
		time_end = time.time()
		# print ("Display:{0}".format((time_end - time_start) * 1000) + "[msec]")
	
	display.finalize()
	# cv2.destroyAllWindows()
	print("func_display: exit")

def func_controller_kb():
	global g_is_exit
	global g_display_mode
	while True:
		inp = input()
		if inp == "q":
			g_is_exit = True
		elif inp == "1":
			g_display_mode = 1
		elif inp == "2":
			g_display_mode = 2
		elif inp == "3":
			g_display_mode = 3
		
		if g_is_exit == True:
			break
	print("func_killer: exit")

def func_controller_btn():
	global g_is_exit
	global g_is_shutdown
	global g_display_mode

	try:
		fd_gpio_export = open("/sys/class/gpio/export", mode='w')
		fd_gpio_export.write("23")
		time.sleep(0.1)
		fd_gpio_export.flush()
		fd_gpio_export.close()
	except:
		print("GPIO23 is already exported")

	try:
		fd_gpio_export = open("/sys/class/gpio/export", mode='w')
		fd_gpio_export.write("24")
		time.sleep(0.1)
		fd_gpio_export.flush()
		fd_gpio_export.close()		
	except:
		print("GPIO24 is already exported")

	try:
		fd_gpio_export = open("/sys/class/gpio/export", mode='w')
		fd_gpio_export.write("25")
		time.sleep(0.1)
		fd_gpio_export.flush()
		fd_gpio_export.close()		
	except:
		print("GPIO25 is already exported")

	fd_gpio_dir = open("/sys/class/gpio/gpio23/direction", mode='w')
	fd_gpio_dir.write("in")
	fd_gpio_dir.flush()
	fd_gpio_dir.close()

	fd_gpio_dir = open("/sys/class/gpio/gpio24/direction", mode='w')
	fd_gpio_dir.write("in")
	fd_gpio_dir.flush()
	fd_gpio_dir.close()

	fd_gpio_dir = open("/sys/class/gpio/gpio25/direction", mode='w')
	fd_gpio_dir.write("in")
	fd_gpio_dir.flush()
	fd_gpio_dir.close()

	fd_btn0_value = open("/sys/class/gpio/gpio23/value", mode='r')
	fd_btn1_value = open("/sys/class/gpio/gpio24/value", mode='r')
	fd_btn2_value = open("/sys/class/gpio/gpio25/value", mode='r')

	while True:
		time.sleep(0.2)
		btn0 = fd_btn0_value.read()
		fd_btn0_value.seek(0)
		btn0 = 1 if int(btn0[0]) == 0 else 0

		btn1 = fd_btn1_value.read()
		fd_btn1_value.seek(0)
		btn1 = 1 if int(btn1[0]) == 0 else 0

		btn2 = fd_btn2_value.read()
		fd_btn2_value.seek(0)
		btn2 = 1 if int(btn2[0]) == 0 else 0

		inp = btn2 << 2 | btn1 << 1 | btn0
		# print(str(inp))
		if inp == 6:
			time.sleep(3)
			if inp == 6:
				g_is_shutdown = True
				g_is_exit = True
				os.system("sudo shutdown -h now")
		elif inp == 1:
			g_display_mode = 1
		elif inp == 2:
			g_display_mode = 2
		elif inp == 4:
			g_display_mode = 3
		if g_is_exit == True:
			break

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

	# Start CONTROLLER(Keyboard) thread
	t = Thread(target=func_controller_kb, args=())
	t.start()
	threads.append(t)

	# Start CONTROLLER(button(GPIO)) thread
	t = Thread(target=func_controller_btn, args=())
	t.start()
	threads.append(t)

	for t in threads:
		t.join()

	if g_is_shutdown == True:
		print("shutdown system")
		os.system("sudo shutdown -h now")
