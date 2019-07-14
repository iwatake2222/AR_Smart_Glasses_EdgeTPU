# -*- coding: utf-8 -*-
import time
import sys
import math
from PIL import Image
import spidev

class OLED_SEPS525_SPI_BGR565:
	def __init__(self):
		self.spi_buffer_size = 4096	# depends on linux setting ( /sys/module/spidev/parameters/bufsiz)
		self.spi_speed = 20 * 1000 * 1000
		self.width = 160
		self.height = 128
		self.fd_gpio_dc_value = None
		self.fd_gpio_res_value = None
		self.spi = None
		self.init_gpio()
		self.init_spi()

	def finalize(self):
		self.clr_res()
		self.spi.close()
		self.fd_gpio_dc_value.close()
		self.fd_gpio_res_value.close()

	def init_gpio(self):
		try:
			fd_gpio_export = open("/sys/class/gpio/export", mode='w')
			fd_gpio_export.write("4")
			time.sleep(0.1)
			fd_gpio_export.flush()
			fd_gpio_export.close()
		except:
			print("GPIO4 is already exported")

		try:
			fd_gpio_export = open("/sys/class/gpio/export", mode='w')
			fd_gpio_export.write("5")
			time.sleep(0.1)
			fd_gpio_export.flush()
			fd_gpio_export.close()		
		except:
			print("GPIO5 is already exported")

		fd_gpio_dc_dir = open("/sys/class/gpio/gpio4/direction", mode='w')
		fd_gpio_dc_dir.write("out")
		fd_gpio_dc_dir.flush()
		fd_gpio_dc_dir.close()

		fd_gpio_res_dir = open("/sys/class/gpio/gpio5/direction", mode='w')
		fd_gpio_res_dir.write("out")
		fd_gpio_res_dir.flush()
		fd_gpio_res_dir.close()

		self.fd_gpio_dc_value = open("/sys/class/gpio/gpio4/value", mode='w')
		self.fd_gpio_res_value = open("/sys/class/gpio/gpio5/value", mode='w')

	def init_spi(self):
		self.spi = spidev.SpiDev()
		self.spi.open(0, 0)
		self.spi.max_speed_hz = self.spi_speed
		self.spi.lsbfirst = False
		self.spi.mode = 3

	def set_dc(self):
		# D/C = 1: data
		self.fd_gpio_dc_value.write("1")
		self.fd_gpio_dc_value.flush()

	def clr_dc(self):
		# D/C = 0: command
		self.fd_gpio_dc_value.write("0")
		self.fd_gpio_dc_value.flush()

	def set_res(self):
		# Active low reset
		self.fd_gpio_res_value.write("1")
		self.fd_gpio_res_value.flush()

	def clr_res(self):
		# Active low reset
		self.fd_gpio_res_value.write("0")
		self.fd_gpio_res_value.flush()

	def send_data(self, data):
		# set_res()
		self.set_dc()
		self.spi.writebytes(data)
		# spi.xfer(data)

	def send_cmd(self, data):
		# set_res()
		self.clr_dc()
		self.spi.writebytes(data)
		# spi.xfer(data)

	def send_init_cmd(self, cmd, data):
		self.send_cmd([cmd,])
		self.send_data([data,])
		# time.sleep(0.001)

	def init(self):
		self.clr_res()
		time.sleep(0.500)
		self.set_res()
		time.sleep(0.500)

		self.send_init_cmd(0x04, 0x03)
		time.sleep(0.002)
		self.send_init_cmd(0x04, 0x00)
		time.sleep(0.002)
		self.send_init_cmd(0x3B, 0x00)
		self.send_init_cmd(0x02, 0x01)
		self.send_init_cmd(0x03, 0x90)
		self.send_init_cmd(0x80, 0x01)
		self.send_init_cmd(0x08, 0x04)
		self.send_init_cmd(0x09, 0x05)
		self.send_init_cmd(0x0A, 0x05)
		self.send_init_cmd(0x0B, 0x9D)
		self.send_init_cmd(0x0C, 0x8C)
		self.send_init_cmd(0x0D, 0x57)
		self.send_init_cmd(0x10, 0x56)
		self.send_init_cmd(0x11, 0x4D)
		self.send_init_cmd(0x12, 0x46)
		self.send_init_cmd(0x13, 0xA0)
		self.send_init_cmd(0x14, 0x11)	# 16-bit interface (no effect?)
		self.send_init_cmd(0x16, 0x64)	# BGR565, V reverted
		self.send_init_cmd(0x20, 0x00)
		self.send_init_cmd(0x21, 0x00)
		self.send_init_cmd(0x28, 0x7F)
		self.send_init_cmd(0x29, 0x00)
		self.send_init_cmd(0x06, 0x01)
		self.send_init_cmd(0x05, 0x00)
		self.send_init_cmd(0x15, 0x00)

		self.send_init_cmd(0x17, 0x00)
		self.send_init_cmd(0x18, self.width - 1)
		self.send_init_cmd(0x19, 0x00)
		self.send_init_cmd(0x1A, self.height - 1)
		self.send_init_cmd(0x20, 0x00)
		self.send_init_cmd(0x21, 0x00)

	def draw_bgr565(self, bgr565):
		start = time.time()
		self.send_init_cmd(0x17, 0x00)
		self.send_init_cmd(0x18, self.width - 1)
		self.send_init_cmd(0x19, 0x00)
		self.send_init_cmd(0x1A, self.height - 1)
		self.send_init_cmd(0x20, 0x00)
		self.send_init_cmd(0x21, 0x00)

		self.send_cmd([0x22,])		
		self.set_dc()
		total_byte = self.width * self.height * 2
		block_num = (int)(math.floor(total_byte / self.spi_buffer_size))
		for i in range(block_num):
			self.spi.writebytes(bgr565[i * self.spi_buffer_size:(i + 1) * self.spi_buffer_size])
		last_size = total_byte - self.spi_buffer_size * block_num
		if last_size > 0:
			self.spi.writebytes(bgr565[total_byte - last_size:total_byte])
		elapsed_time = time.time() - start
		# print ("elapsed_time:{0}".format(elapsed_time) + "[sec]")


def convert_RGB888_to_BGR565(image888):
	image565 = []
	for y in range(0, image888.height):
		for x in range(0, image888.width):
			r, g, b = image888.getpixel((x, y))
			# image565.extend([0x07, 0xE0]) #  Green
			# image565.extend([0xF8, 0x00])  # Blue
			# image565.extend([0x00, 0x1F])  # Red
			r >>= 3
			g >>= 2
			b >>= 3
			image565.extend([b << 3 | g >> 3, (g >> 3) << 5 | r])
	return image565

def create_solid_color_BGR565(width, height):
	image565 = []
	for y in range(0, height):
		for x in range(0, width):
			image565.extend([0x07, 0xE0]) # Green
			# image565.extend([0xF8, 0x00]) # Blue
			# image565.extend([0x00, 0x1F]) # Red
	return image565



if __name__ == '__main__':
	display = OLED_SEPS525_SPI_BGR565()
	display.init()

	image1 = create_solid_color_BGR565(display.width, display.height)
	im = Image.open("red.png").convert('RGB')
	im = im.resize((display.width, display.height))
	image2 = convert_RGB888_to_BGR565(im)

	while True:
		display.draw_bgr565(image1)
		time.sleep(1)
		display.draw_bgr565(image2)
		time.sleep(1)

	display.finalize()

