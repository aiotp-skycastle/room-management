import subprocess

# HLS 전송 스크립트 실행
def start_hls_uploader():
    uploader_script = "/path/to/upload_hls_files.py"  # 실제 경로로 변경
    return subprocess.Popen(["python3", uploader_script])

try:
    # 서보 모터 초기화 및 HLS 디렉토리 초기화
    servo = GPIO.PWM(SERVO_PIN, 50)
    servo.start(0)
    previous_angle = 90
    initialize_directory()

    # ffmpeg 실행
    generate_hls()

    # HLS 전송 스크립트 실행
    hls_uploader = start_hls_uploader()

    last_sensor_time = time.time()
    last_servo_time = last_sensor_time

    while True:
        current_time = time.time()

        # 온도 및 조도 데이터 전송
        if current_time - last_sensor_time >= 5 and ser:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    logging.info(f"Received from Arduino: {data}")
                    try:
                        parts = data.split(',')
                        temperature = float(parts[0].split(':')[1])
                        lux = float(parts[1].split(':')[1])

                        send_sensor_data(TEMP_POST_URL, temperature)
                        send_sensor_data(LIGHT_POST_URL, lux)
                    except (ValueError, IndexError) as e:
                        logging.error(f"Data parsing error: {e}")

            server_light = get_sensor_data(LIGHT_GET_URL)
            if server_light is not None:
                logging.info(f"Received from Server - light: {server_light}")
                if ser:
                    ser.write(f"Lux:{server_light}\n".encode())

            server_temperature = get_sensor_data(TEMP_GET_URL)
            if server_temperature is not None:
                logging.info(f"Received from Server - temperature: {server_temperature}")

            last_sensor_time = current_time

        # 서보 모터 제어
        if current_time - last_servo_time >= 0.5:
            desired_angle = get_sensor_data(SERVO_URL)
            if desired_angle is not None:
                logging.info(f"Received from Server - servo: {desired_angle}")
                if desired_angle != previous_angle:
                    set_servo_angle(desired_angle, servo)
                    previous_angle = desired_angle
            last_servo_time = current_time

        time.sleep(0.01)

except KeyboardInterrupt:
    logging.info("프로그램 종료")

finally:
    if ser:
        ser.close()
    servo.stop()
    GPIO.cleanup()
    if hls_uploader:
        hls_uploader.terminate()
