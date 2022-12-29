// Example5 code for Brian Schmalz's Easy Driver Example page
// https://www.schmalzhaus.com/EasyDriver/index.html

// this version with temperature probe LM35


// pin 4 : switch de buttée
// pin 5 : interrupteur de devant
// 4 or 5 at GND = sleep 

// 11 12 13 pwm led rgb


/////////// recode following changes //////////////// 
// removed pot - set fixed speed
// red LED ON = stopped, blink = running

#include <AccelStepper.h>

// Define the stepper and the pins it will use
AccelStepper stepper1(AccelStepper::DRIVER, 9, 8);//step,dir

// define LED pin
#define LED 7

// Define our three input button pins
#define  FLIP_SWITCH  5   // interrupteur de devant
#define  STOP_SWITCH  4   // switch de butée
#define  LM35 A0
#define  PIN_Sleep  10

// LED RGB
#define PIN_BLUE 11
#define PIN_GREEN 12
#define PIN_RED 13

// declaring variables here makes them global (essential for temp)
// otherwise scope is limited to if statement
unsigned int intervalMeasure = 3000;
unsigned int currentMillis = 0;
unsigned int measurepreviousMillis = 0;
float temp = 0.0;

void setup() {
  // The only AccelStepper value we have to set here is the max speeed, which is higher than we'll ever go
  stepper1.setMaxSpeed(10000.0);
 
  // Set up the three button inputs, with pullups
  pinMode(FLIP_SWITCH, INPUT_PULLUP);
  pinMode(STOP_SWITCH, INPUT_PULLUP);
  pinMode(LED, OUTPUT);

    pinMode(PIN_Sleep, OUTPUT);
    digitalWrite(PIN_Sleep, LOW); 
    
  pinMode(PIN_RED,   OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_BLUE,  OUTPUT);

   Serial.begin(9600);

}

void loop() {

  const int stepper_speed = 725;
  static char sign = 0;                     // Holds -1 or 0 to turn the motor on/off 
  static float new_speed = 0.0;

currentMillis = millis();
if ((unsigned int)(currentMillis - measurepreviousMillis) >= intervalMeasure ) {
  
  int analog0 = analogRead(LM35);
  temp = analog0 * (5000 / 1024.0) / 10;

    if (temp < 35) {    
      digitalWrite(PIN_RED, LOW);
      digitalWrite(PIN_GREEN, LOW);
      digitalWrite(PIN_BLUE, HIGH); 
  }

      if ( (temp >= 35) && (temp <= 60) ) {    
      digitalWrite(PIN_RED, LOW);
      digitalWrite(PIN_GREEN, HIGH);
      digitalWrite(PIN_BLUE, LOW); 
  }

      if ( (temp > 60) && (temp <= 80) ) {    
      digitalWrite(PIN_RED, HIGH);
      digitalWrite(PIN_GREEN, HIGH);
      digitalWrite(PIN_BLUE, LOW); 
  }

  
      if (temp > 80 ) {    
      digitalWrite(PIN_RED, HIGH);
      digitalWrite(PIN_GREEN, LOW);
      digitalWrite(PIN_BLUE, LOW); 
  }


//  Serial.print("temperature = ");
 //Serial.println(temp);
  
measurepreviousMillis = millis();

} // end  currentmillis

  
// tests
 if ( (digitalRead(FLIP_SWITCH) == 1) && (digitalRead(STOP_SWITCH) == 1) ) {    
    sign = -1;
   digitalWrite(PIN_Sleep, HIGH);
    digitalWrite(LED, HIGH);
  }
 if ( (digitalRead(FLIP_SWITCH) == 0) || (digitalRead(STOP_SWITCH) == 0) || (temp > 90) ) {
    sign = 0;
   digitalWrite(PIN_Sleep, LOW);
    digitalWrite(LED, LOW);
  }

// Serial.println(temp);  
new_speed = sign * stepper_speed;
  stepper1.setSpeed(new_speed);
  stepper1.runSpeed();
}
