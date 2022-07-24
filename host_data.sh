#!/bin/bash

# Dependencia del paquete "systat"

while true
do
        cpuu=$(ps -A -o pcpu | tail -n+2 | paste -sd+ | bc)
        #cpuf=$(mpstat | awk 'NR==4{print $12}')
        mt=$(free -h | awk 'NR==2{print $2}' | egrep -o '[0-9]*')
        mu=$(free -h | awk 'NR==2{print $3}' | egrep -o '[0-9]*')
        #mf=$(free -h | awk 'NR==2{print $7}' | egrep -o '[0-9]*')
        temp=$(vcgencmd measure_temp | egrep -o '[0-9]*\.[0-9]*')
        mosquitto_pub -t host/status/temp -m $temp
        mosquitto_pub -t host/status/memory/total -m $mt
        mosquitto_pub -t host/status/memory/used -m $mu
        #mosquitto_pub -t host/status/memory/free -m $mf
        #mosquitto_pub -t host/status/cpu/free -m $cpuf
        mosquitto_pub -t host/status/cpu/used -m $cpuu
        sleep 5
done