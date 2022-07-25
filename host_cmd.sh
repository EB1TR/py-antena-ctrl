#!/bin/bash
HOST_CMD_VENV=/home/pi/venvs/host_cmd
HOST_CMD_PYTH=/home/pi/py-antena-ctrl/svc/host_cmd
. $HOST_CMD_VENV/bin/activate
python $HOST_CMD_PYTH/host_cmd.py &