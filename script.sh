#!/bin/bash
echo "$(date): script executed" >> /home/yuyu/teamproject/log/script_log.txt
deactivate
source ~/teamproject/roomenv/bin/activate
cd ~/teamproject/code
python sensor.py | python camera.py
