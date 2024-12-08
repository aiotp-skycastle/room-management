// LM35DZ 온도 센서 
const int APIN = A0;

// 조도 센서 3pcs
const int APIN1 = A1;
const int APIN2 = A2;
const int APIN3 = A3;

// LED
const int LED = 9;

float temperatureSum = 0.0;
float luxSum = 0.0;
int sampleCount = 0;
// currentTime
unsigned long currentTime = 0;
unsigned long lastSensorTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED, OUTPUT);
  delay(500);
}

void loop() {
  unsigned long currentTime = millis();

  // 0.5초마다 센서값 읽기
  if (abs(currentTime - lastSensorTime) >= 500) {
    lastSensorTime = currentTime;

    // LM35DZ 온도 센서 읽기
    int tempValue = analogRead(APIN); // 0 ~ 1023
    float temperature = (tempValue * 5.0 / 1023) * 100; 
    temperatureSum += temperature;

    // LDR 조도 센서 읽기
    int ldr1 = analogRead(APIN1);
    int ldr2 = analogRead(APIN2);
    int ldr3 = analogRead(APIN3);
    float averageLux = (ldr1 + ldr2 + ldr3) / 3.0;
    luxSum += averageLux;

    // Serial 통신으로 LED 밝기 조정
    if (Serial.available() > 0) {
      String receivedData = Serial.readStringUntil('\n');
      if (receivedData.startsWith("Lux:")) {
        int luxValue = receivedData.substring(4).toInt();
        int ledBrightness = luxValue / 4;
        analogWrite(LED, 255 - ledBrightness);
      }
    }

    sampleCount++; // 샘플 수 증가
  }

  // 5초마다 Serial 통신
  if (sampleCount == 10) {

    // 평균값 계산
    float averageTemperature = temperatureSum / sampleCount;
    float averageLux = luxSum / sampleCount;

    // 라즈베리파이로 데이터 전송
    Serial.print("Temperature:");
    Serial.print(averageTemperature);
    Serial.print(",Lux:");
    Serial.println(averageLux);

    // 평균값 초기화
    temperatureSum = 0.0;
    luxSum = 0.0;
    sampleCount = 0;
  }

 
}