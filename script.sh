#!/bin/bash

# 현재 스크립트가 위치한 디렉토리로 이동
SCRIPT_DIR=$(dirname "$(realpath "$0")")

echo "$(date): script executed" >> "$SCRIPT_DIR/log/script_log.txt"

# Python 가상 환경 활성화
deactivate 2>/dev/null
source "$SCRIPT_DIR/roomenv/bin/activate"

# 작업 디렉토리 변경
cd "$SCRIPT_DIR"

# Python 코드 실행
python code/sensor.py | python code/camera.py
