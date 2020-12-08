#!/bin/bash
cd /home/pi/venv
source bin/activate
cd /home/pi
./ip.sh&
sleep 5
./udp.sh&
sleep 5
./control.sh&
