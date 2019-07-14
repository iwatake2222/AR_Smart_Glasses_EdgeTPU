# -*- coding: utf-8 -*-
# import time
# import struct, fcntl, os
# from ioctl_numbers import _IOR, _IOW
# from struct import pack

# fd_spi = open("/dev/spidev0.0", mode='w')

# # fcntl.fcntl(fd_spi, USBDEVFS_RESET, 0)

# fd_spi.close()
# # _IOW(SPI_IOC_MAGIC, 1, __u8)

# from spi import SPI
# connection = SPI("/dev/spidev0.0")
# connection.set_speed(100000)
# connection.set_mode(0)
# received = connection.transfer("HELLO WORLD")

import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1 * 1000 * 1000

response = spi.xfer([0xaa,0xbb])
print(response)

spi.close()