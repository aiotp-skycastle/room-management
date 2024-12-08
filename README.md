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
<br>[server(in control-panel repository) - raspberrypi(servo motor, webcamera) - arduino(photoresistor, temperature sensor, LED)]

<br>2. log
<br>    camera_log.txt => camera.py log
<img width="763" alt="camera log" src="https://github.com/user-attachments/assets/4e46cddf-9c45-4d66-9876-7cf91ddb7dc2">
<br>    room_log.txt => sensor.py log
<img width="747" alt="room_log" src="https://github.com/user-attachments/assets/db25834a-7e69-4a83-96eb-a1aeee055bb6">
<br>    script_log.txt => script.sh log (if you use)

<br>3. camera
<br>    index\d+\.ts => media segment file (include video data)
<br>    index.m3u8 => playlist file (include segment file path, duration, quality information)
<br>
<h2>시제품 사진</h2>
<img width="343" alt="방 모듈" src="https://github.com/user-attachments/assets/6cb7df45-8d19-4ab9-82d3-230625a6ddf6">
<img width="647" alt="방 모듈2" src="https://github.com/user-attachments/assets/a487be55-0b46-480d-9672-308b8e0cc5c5">