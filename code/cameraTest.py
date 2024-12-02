import os
import subprocess
import requests
import socket
import time


requests.packages.urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

CAMERA_URL = "https://skycastle.cho0h5.org/stream/"

# HLS 파일 경로
HLS_DIR = "/home/yuyu/teamproject/camera"

# ffmpeg 명령어 실행 함수
def generate_hls():
    ffmpeg_command = [
        "ffmpeg",
        "-f", "v4l2",                      # Video4Linux2 포맷 사용
        "-i", "/dev/video0",               # 카메라 장치
        "-codec:v", "libx264",             # H.264 인코딩
        "-preset", "fast",            # 빠른 인코딩
        "-f", "hls",                       # HLS 포맷
        "-hls_time", "1",                  # 세그먼트 길이 (1초)
        "-hls_list_size", "3",             # 최신 3개의 세그먼트 유지
        "-hls_flags", "delete_segments+split_by_time",  # 오래된 세그먼트 삭제
        os.path.join(HLS_DIR, "index.m3u8")  # 출력 파일 경로
    ]
    try:
        subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ffmpeg started successfully.")
    except Exception as e:
        print(f"Error starting ffmpeg: {e}")

# HLS 파일 전송 함수
def upload_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(CAMERA_URL, files=files)
            
            # 서버 응답 확인
            if response.ok:
                json_response = response.json()
                # if json_response.get("status") == "success":
                print(f"Server Response: {json_response['message']}")
                # else:
                #     print(f"Server Error: {json_response.get('message', 'Unknown error')}")
            else:
                print(f"Failed to upload: {file_path}, Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        
try:
    last_sensor_time = time.time()  # 온도와 조도 센서의 마지막 전송 시간
    last_camera_time = last_sensor_time
    # ffmpeg 실행
    generate_hls()
    # 이미 전송된 파일 추적
    uploaded_files = set()
    while True:
        current_time = time.time()
        print(current_time)
        # 2. 카메라 파일 1초마나 서버로 전송
        if current_time - last_camera_time >= 1:
            files = os.listdir(HLS_DIR)
            # 파일 이름에서 숫자 추출 및 정렬
            files = sorted(
                files,
                key=lambda x: int(x.split('.')[0].replace('index', '')) if x.startswith('index') and x.endswith('.ts') else float('inf')
            )
            last_camera_time = current_time
            for file in files:
                file_path = os.path.join(HLS_DIR, file)
                print(file_path)
                if (file_path not in uploaded_files and os.path.isfile(file_path)) or file_path == os.path.join(HLS_DIR, "index.m3u8"):
                    upload_file(file_path)
                    uploaded_files.add(file_path)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("프로그램 종료")
