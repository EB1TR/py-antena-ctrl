#!/bin/bash
HOST_CMD_VENV=/home/pi/venvs/host_status
HOST_CMD_PYTH=/home/pi/py-antena-ctrl/svc/host_status
. $HOST_CMD_VENV/bin/activate
python $HOST_CMD_PYTH/host_status.py &