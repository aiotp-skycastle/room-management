# upload_hls_files.py

import os
import requests
import hashlib
import time

HLS_DIR = "/home/yuyu/teamproject/camera"
CAMERA_URL = "https://skycastle.cho0h5.org/stream/"

# 파일 해시 계산 함수
def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# HLS 파일 전송 함수
def upload_file(file_path, file_hashes):
    try:
        filename = os.path.basename(file_path)
        current_hash = get_file_hash(file_path)
        
        # .m3u8 파일이거나 변경된 경우에만 업로드
        if filename.endswith('.m3u8') or file_path not in file_hashes or file_hashes[file_path] != current_hash:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                response = requests.post(CAMERA_URL, files=files)
                
                if response.status_code in [200, 201]:
                    print(f"Successfully uploaded: {file_path}")
                    file_hashes[file_path] = current_hash
                else:
                    print(f"Failed to upload: {file_path}, Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")

if __name__ == "__main__":
    file_hashes = {}
    while True:
        files = sorted(os.listdir(HLS_DIR))
        for file in files:
            file_path = os.path.join(HLS_DIR, file)
            if os.path.isfile(file_path):
                upload_file(file_path, file_hashes)
        
        # 오래된 파일 해시 제거
        current_files = set(os.path.join(HLS_DIR, f) for f in os.listdir(HLS_DIR))
        file_hashes = {k: v for k, v in file_hashes.items() if k in current_files}

        time.sleep(1)  # 1초 주기로 실행
