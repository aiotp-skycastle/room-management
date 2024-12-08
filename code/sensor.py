import os
import serial
import serial.tools.list_ports
import RPi.GPIO as GPIO
import requests
import socket
import time
import logging


requests.packages.urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

# **로깅 설정**
logging.basicConfig(
    filename='./log/room_log.txt',  # 로그 파일 이름
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
TEMP_POST_URL = "http://skycastle.cho0h5.org:8001/room/temperature"
TEMP_GET_URL = "http://skycastle.cho0h5.org:8001/room/temperature"
LIGHT_POST_URL = "http://skycastle.cho0h5.org:8001/room/illuminance"
LIGHT_GET_URL = "http://skycastle.cho0h5.org:8001/room/illuminance"
SERVO_URL = "http://skycastle.cho0h5.org:8001/room/servo"
# CAMERA_URL = "https://skycastle.cho0h5.org/stream/"

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

# 서보 모터 PWM 설정
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

# 초기 (이전) 서보 모터의 각도
previous_angle = 90

# # 각도 설정 함수
def set_servo_angle(angle):
    if angle > 180:
        angle = 180
    elif angle < 0:
        angle = 0
    
    angle = 180 - angle
    duty = 2 + (angle / 18)
    GPIO.output(SERVO_PIN, True)
    servo.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    servo.ChangeDutyCycle(0)

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
        response.raise_for_status() 
        # logging.info(response)
        response_data = response.json()
        # logging.info(f"timem: {response_data}")
        if response_data.get("success", False):  # success가 true인지 확인
            return response_data.get("status", 0)  # status 값 반환
        else:
            logging.warning(f"GET {url} 실패: success가 false입니다.")
            return None  # success가 false일 경우 None 반환
    except requests.exceptions.Timeout:
        logging.error("요청이 타임아웃되었습니다.")
    except requests.RequestException as e:
        logging.error(f"GET 요청 오류: {e}")
    except ValueError:
        logging.error("JSON 디코딩 오류")
    return None  # 실패 시 None 반환

try:
    last_sensor_time = time.time()  # 온도와 조도 센서의 마지막 전송 시간

    while True:
        if ser and ser.in_waiting > 0:
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
        
        # 2. 서보 모터는 0.5초마다 서버로부터 각도 값을 가져와 제어
        desired_angle = get_sensor_data(SERVO_URL)
        if desired_angle is not None:
            logging.info(f"Received from Server - servo: {desired_angle}")
            if desired_angle != previous_angle:
                # set_servo_angle(previous_angle, desired_angle)
                set_servo_angle(desired_angle)
                previous_angle = desired_angle  # 각도 업데이트


        # logging.info(f"time4: {current_time}")
        # 서보 모터 제어 주기
        time.sleep(0.5)

except KeyboardInterrupt:
    logging.info("프로그램 종료")

finally:
    if ser:
        ser.close()
    servo.stop()
    GPIO.cleanup()
