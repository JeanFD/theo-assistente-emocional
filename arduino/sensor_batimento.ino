#define SENSOR_PIN A0

void setup() {
  Serial.begin(9600);
}

void loop() {
  int valorSensor = analogRead(SENSOR_PIN);

  Serial.println(valorSensor);
  delay(100);
}