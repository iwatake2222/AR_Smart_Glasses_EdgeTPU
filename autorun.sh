#!/bin/sh
CURRENT_DIR=$(cd $(dirname $0);pwd)

sleep 30s
echo `date` > $CURRENT_DIR/log_run.txt 
cd $CURRENT_DIR
# sudo modprobe bcm2835-v4l2
sleep 1s
sudo python3 smart_glasses.py > log_exe.txt 
