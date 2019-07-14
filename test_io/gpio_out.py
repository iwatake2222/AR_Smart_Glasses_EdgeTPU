# -*- coding: utf-8 -*-
import time

fd_gpio_export = open("/sys/class/gpio/export", mode='w')
fd_gpio_export.write("4")
# time.sleep(0.1)
fd_gpio_export.flush()

fd_gpio4_dir = open("/sys/class/gpio/gpio4/direction", mode='w')
fd_gpio4_dir.write("out")
fd_gpio4_dir.flush()

fd_gpi4_value = open("/sys/class/gpio/gpio4/value", mode='w')

while(True):
	fd_gpi4_value.write("1")
	fd_gpi4_value.flush()
	fd_gpi4_value.write("0")
	fd_gpi4_value.flush()

fd_gpi4_value.close()
fd_gpio4_dir.close()
fd_gpio_export.close()
