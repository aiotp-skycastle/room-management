# 서보 모터 test용
import RPi.GPIO as GPIO
import time

# GPIO 설정
GPIO.setmode(GPIO.BCM)
SERVO_PIN = 17 # 실제는 위치 상으로는 11번 핀 (gpio 17)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# PWM 설정 (50Hz)
servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz 주파수로 PWM 생성
servo.start(0)

# 각도 설정 함수
def set_servo_angle(angle):
    duty = 2 + (angle / 18)
    GPIO.output(SERVO_PIN, True)
    servo.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    servo.ChangeDutyCycle(0)

try:
    while True: # 0 -> 90 -> 180 -> 0도로 이동 반복
        set_servo_angle(0)
        time.sleep(1)
        set_servo_angle(90)
        time.sleep(1)
        set_servo_angle(180)
        time.sleep(1)

except KeyboardInterrupt:
    print("프로그램 종료")

finally:
    servo.stop()
    GPIO.cleanup()
