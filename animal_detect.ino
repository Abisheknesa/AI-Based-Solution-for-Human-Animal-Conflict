#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Pins
const int ledPin1 = 9;       // First LED
const int ledPin2 = 8;       // Second LED
const int buzzerPin = 10;
const int vibrationPin = 2;

// Alert states
bool elephantDetected = false;
bool postDetectionActive = false;
unsigned long detectionStartTime = 0;
unsigned long postDetectionStartTime = 0;
const long blinkInterval = 500;
const long alertDuration = 5000;

void setup() {
  // Initialize pins
  pinMode(ledPin1, OUTPUT);
  pinMode(ledPin2, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(vibrationPin, INPUT);

  // Initialize display
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    while(1); // Halt if display fails
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0,0);
  display.println("System Ready");
  display.display();
  
  Serial.begin(9600);
}

void loop() {
  unsigned long currentMillis = millis();
  int vibrationState = digitalRead(vibrationPin);

  // Handle serial commands
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'H' && !elephantDetected) {
      elephantDetected = true;
      detectionStartTime = currentMillis;
      postDetectionActive = false;
      showAlertMessage();
    } else if (command == 'L' && elephantDetected) {
      elephantDetected = false;
      postDetectionActive = true;
      postDetectionStartTime = currentMillis;
    }
  }

  // Vibration override
  if (vibrationState == HIGH) {
    digitalWrite(ledPin1, HIGH);
    digitalWrite(ledPin2, HIGH);
    digitalWrite(buzzerPin, HIGH);
    showAlertMessage();
    return;
  }

  // Elephant alert logic
  if (elephantDetected) {
    if (currentMillis - detectionStartTime <= alertDuration) {
      // Blinking phase
      if ((currentMillis / blinkInterval) % 2 == 0) {
        digitalWrite(ledPin1, HIGH);
        digitalWrite(ledPin2, HIGH);
        digitalWrite(buzzerPin, HIGH);
      } else {
        digitalWrite(ledPin1, LOW);
        digitalWrite(ledPin2, LOW);
        digitalWrite(buzzerPin, LOW);
      }
    } else {
      // Solid phase
      digitalWrite(ledPin1, HIGH);
      digitalWrite(ledPin2, HIGH);
      digitalWrite(buzzerPin, HIGH);
    }
  } 
  else if (postDetectionActive) {
    if (currentMillis - postDetectionStartTime <= alertDuration) {
      // Post-detection blinking
      if ((currentMillis / blinkInterval) % 2 == 0) {
        digitalWrite(ledPin1, HIGH);
        digitalWrite(ledPin2, HIGH);
        digitalWrite(buzzerPin, HIGH);
      } else {
        digitalWrite(ledPin1, LOW);
        digitalWrite(ledPin2, LOW);
        digitalWrite(buzzerPin, LOW);
      }
    } else {
      postDetectionActive = false;
      allOff();
      showStandbyMessage();
    }
  }
  else {
    allOff();
  }
}

void allOff() {
  digitalWrite(ledPin1, LOW);
  digitalWrite(ledPin2, LOW);
  digitalWrite(buzzerPin, LOW);
}

void showAlertMessage() {
  display.clearDisplay();
  display.setTextSize(2);
  display.setCursor(0,20);
  display.println("ANIMAL");
  display.println("DETECTED");
  display.setTextSize(1);
  display.setCursor(0,50);
  display.println("Just now");
  display.display();
}

void showStandbyMessage() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0,0);
  display.println("Elephant Alert System");
  display.println("---------------------");
  display.println("Monitoring...");
  display.display();
}
