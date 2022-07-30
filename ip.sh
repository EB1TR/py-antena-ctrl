#!/bin/bash
nuevaip="$(hostname -I | awk '{ print $1}')"
cd $PATHCTRL/static
sed -r 's/([0-9]{1,3}\.){3}[0-9]{1,3}'/"$nuevaip"/g mqtt.js > mqtt2.js
mv mqtt2.js mqtt.js

sed -r 's/([0-9]{1,3}\.){3}[0-9]{1,3}'/"$nuevaip"/g config.js > config2.js
mv config.js config.js