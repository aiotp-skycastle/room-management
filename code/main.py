import os
import subprocess
import serial
import serial.tools.list_ports
import RPi.GPIO as GPIO
import requests
import socket
import time
import logging
import shutil
import hashlib


requests.packages.urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

# **로깅 설정**
logging.basicConfig(
    filename='log.txt',  # 로그 파일 이름
    level=logging.INFO,  # 로깅 수준
    format='%(asctime)s - %(levelname)s - %(message)s',  # 시간, 로그 수준, 메시지 형식
    datefmt='%Y-%m-%d %H:%M:%S'  # 시간 형식
)

# GPIO 핀 설정
GPIO.setwarnings(False)  # 경고 메시지 비활성화
GPIO.setmode(GPIO.BCM)
SERVO_PIN = 17  # 서보 모터 핀
GPIO.setup(SERVO_PIN, GPIO.OUT)

# 서버 URL 설정
TEMP_POST_URL = "https://skycastle.cho0h5.org/room/temperature"
TEMP_GET_URL = "https://skycastle.cho0h5.org/room/temperature"
LIGHT_POST_URL = "https://skycastle.cho0h5.org/room/illuminance"
LIGHT_GET_URL = "https://skycastle.cho0h5.org/room/illuminance"
SERVO_URL = "https://skycastle.cho0h5.org/room/servo"
CAMERA_URL = "https://skycastle.cho0h5.org/stream/"

# HLS 파일 경로
HLS_DIR = "/home/yuyu/teamproject/camera"

# 시리얼 포트 자동 감지
def initialize_serial_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        raise Exception("No serial devices found. Please check the connection.")
    return serial.Serial(ports[0].device, 115200, timeout=1)

try:
    ser = initialize_serial_port()
    logging.info(f"Connected to serial port: {ser.port}")
except Exception as e:
    logging.error(f"Serial initialization error: {e}")
    ser = None


# 각도 설정 함수
def set_servo_angle(angle, servo):
    angle = 180 - angle
    duty = 2 + (angle / 18)
    GPIO.output(SERVO_PIN, True)
    servo.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    servo.ChangeDutyCycle(0)


# 디렉토리 초기화 함수
def initialize_directory():
    if os.path.exists(HLS_DIR):
        # print(HLS_DIR)
        shutil.rmtree(HLS_DIR)
    os.makedirs(HLS_DIR)

# 파일 해시 계산 함수
def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


# ffmpeg 명령어 실행 함수
def generate_hls():
    ffmpeg_command = [
        "ffmpeg",
        "-f", "v4l2",
        "-i", "/dev/video0",
        "-codec:v", "libx264",
        "-preset", "ultrafast",
        "-f", "hls",
        "-hls_time", "3",
        "-hls_list_size", "3",
        "-hls_flags", "delete_segments+split_by_time",
        "-hls_start_number_source", "epoch",  # 타임스탬프 기반 시작 번호
        os.path.join(HLS_DIR, "index.m3u8")
    ]
    try:
        subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ffmpeg started successfully.")
    except Exception as e:
        print(f"Error starting ffmpeg: {e}")


# HLS 파일 전송 함수
def upload_file(file_path, file_hashes):
    try:
        filename = os.path.basename(file_path)
        current_hash = get_file_hash(file_path)
        
        # .m3u8 파일이거나 파일 내용이 변경된 경우에만 업로드
        if filename.endswith('.m3u8') or file_path not in file_hashes or file_hashes[file_path] != current_hash:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                response = requests.post(CAMERA_URL, files=files)
                
                if response.status_code in [200, 201]:
                    print(f"Successfully uploaded: {file_path}")
                    file_hashes[file_path] = current_hash
                else:
                    print(f"Failed to upload: {file_path}, Status code: {response.status_code}, Response: {response.text}")
        else:
            print(f"File not changed, skipping upload: {file_path}")
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        

# POST 요청 함수
def send_sensor_data(url, sensor_value):
    payload = {"status": sensor_value}
    try:
        response = requests.post(url, json=payload)
        logging.info(f"POST {url} 성공: {response.json()}")
    except requests.RequestException as e:
        logging.error(f"POST 요청 오류: {e}")

# GET 요청 함수
def get_sensor_data(url):
    try:
        # logging.info(f"timesponse_data")
        response = requests.get(url, timeout=5)
        # logging.info(response)
        response_data = response.json()
        # logging.info(f"timem: {response_data}")
        if response_data.get("success", False):  # success가 true인지 확인
            return response_data.get("status", 0)  # status 값 반환
        else:
            logging.warning(f"GET {url} 실패: success가 false입니다.")
            return None  # success가 false일 경우 None 반환
    except requests.exceptions.Timeout:
        print("요청이 타임아웃되었습니다.")
    except requests.RequestException as e:
        logging.error(f"GET 요청 오류: {e}")
        return None  # 요청 실패 시 None 반환

try:
    # 서보 모터 PWM 설정
    servo = GPIO.PWM(SERVO_PIN, 50)
    servo.start(0)

    # 초기 (이전) 서보 모터의 각도
    previous_angle = 90
    initialize_directory()
    last_sensor_time = time.time()  # 온도와 조도 센서의 마지막 전송 시간
    last_camera_time = last_sensor_time
    last_servo_time = last_sensor_time
    # ffmpeg 실행
    generate_hls()
    # 이미 전송된 파일 추적
    file_hashes = {}
    while True:
        current_time = time.time()
        # 2. 카메라 파일 1초마나 서버로 전송
        if current_time - last_camera_time >= 1:
            files = sorted(os.listdir(HLS_DIR))
            for file in files:
                file_path = os.path.join(HLS_DIR, file)
                if os.path.isfile(file_path):
                    upload_file(file_path, file_hashes)
            
            # 오래된 파일 해시 제거
            current_files = set(os.path.join(HLS_DIR, f) for f in os.listdir(HLS_DIR))
            file_hashes = {k: v for k, v in file_hashes.items() if k in current_files}
            last_camera_time = current_time
        # 1. 온도와 조도 데이터는 3초마다 서버로 전송
        if current_time - last_sensor_time >= 5 and ser:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    logging.info(f"Received from Arduino: {data}")
                    try:
                        parts = data.split(',')
                        temperature = float(parts[0].split(':')[1])
                        lux = float(parts[1].split(':')[1])

                        # 서버에 온도와 조도 데이터 POST
                        send_sensor_data(TEMP_POST_URL, temperature)
                        send_sensor_data(LIGHT_POST_URL, lux)
                    except (ValueError, IndexError) as e:
                        logging.error(f"Data parsing error: {e}")

            # 서버에서 조도 값 GET
            server_light = get_sensor_data(LIGHT_GET_URL)
            if server_light is not None:  # success가 true일 때만 아두이노로 전송
                logging.info(f"Received from Server - light: {server_light}")
                if ser:
                    ser.write(f"Lux:{server_light}\n".encode())  # 아두이노로 조도 값 전송

            # 서버에서 온도 값 GET
            server_temperature = get_sensor_data(TEMP_GET_URL)
            if server_temperature is not None:
                logging.info(f"Received from Server - temperature: {server_temperature}")
                # 에어컨에 전달 (추가 구현 필요)

            last_sensor_time = current_time  # 마지막 전송 시간 업데이트

        # 2. 서보 모터는 0.5초마다 서버로부터 각도 값을 가져와 제어
        if current_time - last_servo_time >= 0.5:
            desired_angle = get_sensor_data(SERVO_URL)
            if desired_angle is not None:
                logging.info(f"Received from Server - servo: {desired_angle}")
                if desired_angle != previous_angle:
                    set_servo_angle(desired_angle, servo)
                    previous_angle = desired_angle  # 각도 업데이트
            last_servo_time = current_time
            
        # 루프 제어 주기
        time.sleep(0.01)

except KeyboardInterrupt:
    logging.info("프로그램 종료")

finally:
    if ser:
        ser.close()
    servo.stop()
    GPIO.cleanup()
