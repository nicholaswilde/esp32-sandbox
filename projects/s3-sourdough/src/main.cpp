#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  Serial.println("Hello from sandbox!");
}

void loop() {
  delay(1000);
}
