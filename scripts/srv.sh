#!/bin/bash
<<<<<<< HEAD
cd /home/pi/py-stn
python3 udp.py&
sleep 2
python3 control.py&
sleep 30
python3 mqtt-spider.py&
sleep 2
python3 mqtt-rbn-cw.py&
sleep 2
python3 mqtt-rbn-mgm.py&
sleep 2
nuevaip="$(hostname -I)"
nuevaip="${nuevaip::-1}"
cd /home/pi/py-stn/static
sed -r 's/(\b[0-9]{1,3}\.){3}[0-9]{1,3}\b'/"$nuevaip"/ mqtt.js > mqtt2.js
mv mqtt2.js mqtt.js
chown pi:pi mqtt.js
=======
cd /home/pi/venv
source bin/activate
cd /home/pi
./ip.sh&
sleep 5
./udp.sh&
sleep 5
./control.sh&
>>>>>>> monobanda
