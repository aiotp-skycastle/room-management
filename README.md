<h2>실행 방법</h2>

<br>1. clone repository
<br>    git clone git@github.com:aiotp-skycastle/room-management.git teamproject
<br>
<br>2. move to directory
<br>    cd teamproject
<br>
<br>3-1. execute
<br>    ./script.sh
<br>
<br>3-2. use crontab (optional)
<br>    copy "copy_to_crontab.txt" in 'crontab -e'
<br>    sudo reboot
<br>
<h2>구성요소</h2>
<br>1. code directory
<br>    camera.py => upload video stream using hls method.
<br>    sensor.py => exchange sensor(photoresistor, temperature sensor)and motor(servo motor) data with server(post, get) and arduino(serial). 
<br>[server(GUI) - raspberrypi(servo motor, webcamera) - arduino(photoresistor, temperature sensor, LED)]

<br>2. log
<br>    camera_log.txt => camera.py log
<br>    sensor_log.txt => sensor.py log
<br>    script_log.txt => script.sh log (if you use)