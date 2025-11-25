const int buzzerPin = 5;

void setup() {
  pinMode(buzzerPin, OUTPUT);
  noTone(buzzerPin);
  digitalWrite(buzzerPin, LOW);
}

void loop() {
  // Silencio
}