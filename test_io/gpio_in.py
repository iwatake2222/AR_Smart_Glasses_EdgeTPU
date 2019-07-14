# -*- coding: utf-8 -*-
import time

fd_gpio_export = open("/sys/class/gpio/export", mode='w')
fd_gpio_export.write("17")
# time.sleep(0.1)
fd_gpio_export.flush()

fd_gpio17_dir = open("/sys/class/gpio/gpio17/direction", mode='w')
fd_gpio17_dir.write("in")
fd_gpio17_dir.flush()

fd_gpi17_value = open("/sys/class/gpio/gpio17/value", mode='r')

while(True):
	value_str = fd_gpi17_value.read()
	fd_gpi17_value.seek(0)
	value = int(value_str[0])
	print(str(value))

fd_gpio17_dir.close()
fd_gpio17_dir.close()
fd_gpio_export.close()
