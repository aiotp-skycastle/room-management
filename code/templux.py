import os
# import subprocess
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
    angle = 180 - angle
    duty = 2 + (angle / 18)
    GPIO.output(SERVO_PIN, True)
    servo.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    servo.ChangeDutyCycle(0)

# 각도 설정 함수 (부드럽게 이동)
# def set_servo_angle(current_angle, target_angle, step=1, delay=0.02):
#     target_angle = 180 - target_angle
#     try:
#         while current_angle != target_angle:
#             if current_angle < target_angle:
#                 current_angle += step
#                 if current_angle > target_angle:
#                     current_angle = target_angle
#             elif current_angle > target_angle:
#                 current_angle -= step
#                 if current_angle < target_angle:
#                     current_angle = target_angle

#             # 서보 모터 동작
#             duty = 2 + (current_angle / 18)
#             GPIO.output(SERVO_PIN, True)
#             servo.ChangeDutyCycle(duty)
#             time.sleep(delay)  # 부드러운 이동을 위한 딜레이
#             GPIO.output(SERVO_PIN, False)
#             servo.ChangeDutyCycle(0)
#     except Exception as e:
#         print(f"Error while moving servo: {e}")


# # ffmpeg 명령어 실행 함수
# def generate_hls():
#     ffmpeg_command = [
#         "ffmpeg",
#         "-f", "v4l2",                      # Video4Linux2 포맷 사용
#         "-i", "/dev/video0",               # 카메라 장치
#         "-codec:v", "libx264",             # H.264 인코딩
#         "-preset", "ultrafast",            # 빠른 인코딩
#         "-f", "hls",                       # HLS 포맷
#         "-hls_time", "1",                  # 세그먼트 길이 (1초)
#         "-hls_list_size", "3",             # 최신 3개의 세그먼트 유지
#         "-hls_flags", "delete_segments+split_by_time",  # 오래된 세그먼트 삭제
#         os.path.join(HLS_DIR, "index.m3u8")  # 출력 파일 경로
#     ]
#     try:
#         subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         print("ffmpeg started successfully.")
#     except Exception as e:
#         print(f"Error starting ffmpeg: {e}")

# # HLS 파일 전송 함수
# def upload_file(file_path):
#     try:
#         with open(file_path, 'rb') as f:
#             files = {'file': (os.path.basename(file_path), f)}
#             response = requests.post(CAMERA_URL, files=files)
            
#             # 서버 응답 확인
#             if response.ok:
#                 json_response = response.json()
#                 # if json_response.get("status") == "success":
#                 print(f"Server Response: {json_response['message']}")
#                 # else:
#                     # print(f"Server Error: {json_response.get('message', 'Unknown error')}")
#             else:
#                 print(f"Failed to upload: {file_path}, Status code: {response.status_code}, Response: {response.text}")
#     except Exception as e:
#         print(f"Error uploading {file_path}: {e}")

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
    last_sensor_time = time.time()  # 온도와 조도 센서의 마지막 전송 시간
    last_camera_time = last_sensor_time
    # ffmpeg 실행
    # generate_hls()
    # 이미 전송된 파일 추적
    uploaded_files = set()
    while True:
        # files = os.listdir(HLS_DIR)
        
        #  # 파일 이름에서 숫자 추출 및 정렬
        # files = sorted(
        #     files,
        #     key=lambda x: int(x.split('.')[0].replace('index', '')) if x.startswith('index') and x.endswith('.ts') else float('inf')
        # )
        current_time = time.time()
        # # 2. 카메라 파일 1초마나 서버로 전송
        # if current_time - last_camera_time >= 1:
        #     last_camera_time = current_time
        #     for file in files:
        #         file_path = os.path.join(HLS_DIR, file)
        #         if (file_path not in uploaded_files and os.path.isfile(file_path)) or file_path == os.path.join(HLS_DIR, "index.m3u8"):
        #             upload_file(file_path)
        #             uploaded_files.add(file_path)
        # 1. 온도와 조도 데이터는 5초마다 서버로 전송
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
        desired_angle = get_sensor_data(SERVO_URL)
        if desired_angle is not None:
            logging.info(f"Received from Server - servo: {desired_angle}")
            if desired_angle != previous_angle:
                # set_servo_angle(previous_angle, desired_angle)
                set_servo_angle(desired_angle)
                previous_angle = desired_angle  # 각도 업데이트


        logging.info(f"time4: {current_time}")
        # 서보 모터 제어 주기
        time.sleep(0.5)

except KeyboardInterrupt:
    logging.info("프로그램 종료")

finally:
    if ser:
        ser.close()
    servo.stop()
    GPIO.cleanup()
