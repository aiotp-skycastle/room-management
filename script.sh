#!/bin/bash
echo "$(date): script executed" >> ~/teamproject/log/script_log.txt
deactivate
source ~/teamproject/roomenv/bin/activate
cd ~/teamproject
python code/sensor.py | python code/camera.py
