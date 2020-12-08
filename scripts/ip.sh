#/bin/bash
nuevaip="$(hostname -I)"
nuevaip="${nuevaip::-1}"
cd /home/pi/py-stn/static
sed -r 's/(\b[0-9]{1,3}\.){3}[0-9]{1,3}\b'/"$nuevaip"/ mqtt.js > mqtt2.js
sed -r 's/(\b[0-9]{1,3}\.){3}[0-9]{1,3}\b'/"$nuevaip"/ config.js > config2.js
mv mqtt2.js mqtt.js
mv config2.js config.js
chown 1000:1000 mqtt.js config.js