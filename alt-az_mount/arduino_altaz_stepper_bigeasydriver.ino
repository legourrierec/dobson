// Example5 code for Brian Schmalz's Easy Driver Example page
// https://www.schmalzhaus.com/EasyDriver/index.html

// reference code for focus steper and IR:
// https://forum.dronebotworkshop.com/arduino/ir-modual/
// http://www.energiazero.org/meccatronica/stepper_driver/28BYJ-48%20Stepper%20Motor%20with%20ULN2003%20Driver%20and%20Arduino%20Tutorial.pdf

// IR sensor vs1838b
// https://arduino.stackexchange.com/questions/3926/using-vs1838b-with-arduino

// IR remote -  we check continuously
// DHT22 + LM35 sensors - we check every X seconds
// serial communication with Odroid Python
// 3 speeds: all 8th step, with different max speed, position and acceleration
// catches up with backlash if previous dir opposit to requested dir
// this makes use of a second instance of each stepper (Backlash_) with specific speed
// custom movement for python goto, feedback for all actions
// normalised name to ALT instead of DEC or DE

// focus connector:

// B blue D5 - IN1 - DIN1
// P pink D6 - IN2 - DIN2
// Y yellow D7 - IN3 - DIN3
// O orange D8 - IN4 - DIN4
// R red (violet) ----common----> DIN5

// not used (yet)
// marron   DIN 7
// white    

// G grey (black) - GND - DIN 8

//Connector top:
//  X * R B P
//  O G - Y -

// connecteur DIN (female front): cw

//     4
//  3     5
// 2   8   6  
//  1     7

// steps Az et Alt
// https://www.brainy-bits.com/post/stepper-motor-microstepping-what-to-keep-in-mind-when-doing-it
// MS1 MS2 
//
// LOW LOW   = Full Step // CH+
// HIGH LOW  = Half Step // CH
// LOW HIGH  = 1/4 Step //  CH-
// HIGH HIGH = 1/8 Step // (default)

// libraries for steppers, sensors and IR
#include <AccelStepper.h>
#include <DHT.h>
#include <IRremote.h>

// PIN stepper focus
#define HALFSTEP 8
//AccelStepper stepper = AccelStepper(MotorInterfaceType, motorPin1, motorPin3, motorPin2, motorPin4);
AccelStepper FocusStepper = AccelStepper(HALFSTEP,7,9,8,10);  // IN 1 3 2 4

// PIN steps Az et Alt
#define PIN_AZ_MS1 32 // red
#define PIN_AZ_MS2 34 // black
#define PIN_ALT_MS1 30  // blue
#define PIN_ALT_MS2 28  // yellow

// PIN steppers telescope
#define  PIN_alt_Sleep  49 
#define  PIN_azimut_Sleep  40 
AccelStepper AzimutStepper(AccelStepper::DRIVER, 38, 48); //step, dir
AccelStepper AltStepper(AccelStepper::DRIVER, 43, 42);

AccelStepper Backlash_AzimutStepper(AccelStepper::DRIVER, 38, 48); //step, dir
AccelStepper Backlash_AltStepper(AccelStepper::DRIVER, 43, 42);

// PIN sensors
#define  PIN_LM35 A2  //glued to driver heatsink
//define PIN_DHT22_ambiant X //not implemented
#define  PIN_DHT22_intake 6
#define  PIN_DHT22_outflow 2
#define  PIN_DHT22_eq_table 24
#define DHTTYPE DHT22   // DHT 22  (AM2302)
DHT dht_intake(PIN_DHT22_intake, DHTTYPE); //// Initialize DHT sensor
DHT dht_outflow(PIN_DHT22_outflow, DHTTYPE); //// Initialize DHT sensor
DHT dht_eq_table(PIN_DHT22_eq_table, DHTTYPE); //// Initialize DHT sensor

// PIN Infra-Red
#define IR_RECEIVE_PIN 5

// VCC = right pin
// ground = middle pin
// SIGNAL = left pin looking from front

// IR key and codes
#define KEY_REPEAT (0)

///////////// small remote - not very convenient ////////////
//// for azimut and alt 
//#define KEY_1 (4077715200)
//#define KEY_2 (3877175040)
//#define KEY_3 (2707357440)
//#define KEY_4 (4144561920)
//#define KEY_5 (3810328320)
//#define KEY_6 (2774204160)
//#define KEY_7 (3175284480)
//#define KEY_8 (2907897600)
//#define KEY_9 (3041591040)

//// step
//#define KEY_CH_moins (3125149440)
//#define KEY_CH (3108437760)
//#define KEY_CH_plus (3091726080)

//// focus
//#define KEY_plus (3927310080)
//#define KEY_moins (4161273600)
//#define KEY_ffwd (3208707840)
//#define KEY_fbwd (3141861120)

///////////// telecommande de la box ////////////

// for azimut and alt 

#define KEY_U (902495489) // up
#define KEY_L (1721367809) // left
#define KEY_R (1052900609) // right
#define KEY_D (768802049)  // down

// step
#define KEY_1 (1838349569)  // 1- slow 1/4 step
#define KEY_2 (1821637889)  //  2- default 1/2 step
#define KEY_3 (869072129)  // 3- fast full step

// focus
#define KEY_vplus (2139159809)  //v+
#define KEY_vmoins (2122448129)   // v-
#define KEY_pplus (2055601409)   //p+
#define KEY_pmoins (2038889729)   //p-


// PIN power LED
#define  PIN_power_ON_LED 13


// defined measurement intervals for DHT22 and LM35 sensors
unsigned int intervalMeasure = 10000;  // can increase to 5 secs or more later
unsigned int currentMillis = 0;
unsigned int measurepreviousMillis = 0;

// initialise variables
unsigned int azimutValue = 0;
unsigned int altValue = 0;
int azimut_new_speed = 0;
int alt_new_speed = 0;
float h_intake = 0;
float t_intake = 0;
float h_outflow = 0;
float t_outflow = 0;
float h_eq_table = 0;
float t_eq_table = 0;
int analog0 = 0;
float temp = 0;
int sensors = 0;
char odroid_serial;
int dir = 1;
int posi = 1600;
int previous_alt_dir = 0;
int previous_azimut_dir = 0;

////////////////////////////////////// 
// about acceleration
// use moveTo() and run() instead of runSpeed()
// The stepper will accelerate to the speed defined by setMaxSpeed() at the rate defined by setAcceleration()
// !!! more computationally intensive than runSpeed() !!
//
// good idea: multiply readings by 10 so can declare int not floats, this saves memory
// allow time between measurements: no problem, once every 10 seconds or more.
// also, should take 3 measurements ? or plan to remeasure if outside some "make-sense" interval
// can declare only one DHT object:
// https://forum.arduino.cc/t/taking-readings-from-multiple-dht22-sensors-how-to-get-the-mac-address-of-each/211962/5
/////////////////////////////////////

///////////////////////
//////  FUNCTIONS  ////
///////////////////////

void Focus(int dir, int pos, int sp) {
          FocusStepper.setCurrentPosition(0);
          digitalWrite(LED_BUILTIN, LOW);
          FocusStepper.setSpeed(dir*sp);
          while(FocusStepper.currentPosition()!=dir*pos) {
            FocusStepper.runSpeed();
            }
          digitalWrite(LED_BUILTIN, HIGH);  
          dir = 0;
          pos = 0;
          delay(130);

          Serial.println("ARDUINO-DONE");  // done
          delay(1000);
          odroid_serial = ' ';
}

// steps applies to Azimut and Alt steppers


void slow() {
            AzimutStepper.setMaxSpeed(300.0);
            AltStepper.setMaxSpeed(300.0);
            AzimutStepper.setAcceleration(500.0);
            AltStepper.setAcceleration(500.0);
               digitalWrite(PIN_AZ_MS1, HIGH);            
               digitalWrite(PIN_AZ_MS2, HIGH);
               digitalWrite(PIN_ALT_MS1, HIGH);            
               digitalWrite(PIN_ALT_MS2, HIGH);
               posi = 800;
}

void normal() {
            AzimutStepper.setMaxSpeed(600.0);
            AltStepper.setMaxSpeed(600.0);
            AzimutStepper.setAcceleration(1000.0);
            AltStepper.setAcceleration(1000.0);
               digitalWrite(PIN_AZ_MS1, HIGH);            
               digitalWrite(PIN_AZ_MS2, HIGH);
               digitalWrite(PIN_ALT_MS1, HIGH);            
               digitalWrite(PIN_ALT_MS2, HIGH);
               posi = 1600;
}

void fast() {
            AzimutStepper.setMaxSpeed(1200.0);
            AltStepper.setMaxSpeed(1200.0);
            AzimutStepper.setAcceleration(1500.0);
            AltStepper.setAcceleration(1500.0);
               digitalWrite(PIN_AZ_MS1, HIGH);            
               digitalWrite(PIN_AZ_MS2, HIGH);
               digitalWrite(PIN_ALT_MS1, HIGH);            
               digitalWrite(PIN_ALT_MS2, HIGH);
               posi = 3200;
}

void custom(int gosteps) {
            int maxi;
            if (gosteps > 4000)
              { maxi = 4000; }
            else
              { maxi = gosteps; }
            AzimutStepper.setMaxSpeed(int(maxi/2.6));
            AltStepper.setMaxSpeed(int(maxi/2.6));
            AzimutStepper.setAcceleration(int(maxi/2));
            AltStepper.setAcceleration(int(maxi/2));
               digitalWrite(PIN_AZ_MS1, HIGH);            
               digitalWrite(PIN_AZ_MS2, HIGH);
               digitalWrite(PIN_ALT_MS1, HIGH);            
               digitalWrite(PIN_ALT_MS2, HIGH);
               posi = gosteps;
}

// not used anymore
void fullstep() {
            AzimutStepper.setMaxSpeed(200.0);
            AltStepper.setMaxSpeed(200.0);
            AzimutStepper.setAcceleration(1000.0);
            AltStepper.setAcceleration(1000.0);
               digitalWrite(PIN_AZ_MS1, LOW);            
               digitalWrite(PIN_AZ_MS2, LOW);
               digitalWrite(PIN_ALT_MS1, LOW);            
               digitalWrite(PIN_ALT_MS2, LOW);
}

/// changed "int pos" to "int posi" ///
void Alt(int dir, int posi) {
          AltStepper.setCurrentPosition(0);
          digitalWrite(LED_BUILTIN, LOW);
          delay(100);
          digitalWrite(PIN_alt_Sleep, HIGH);
          
          // no acceleration
          //AltStepper.setSpeed(200*dir);
          //while(AltStepper.currentPosition()!=200*dir) {
          //  AltStepper.runSpeed();
          //}


        if ( previous_alt_dir == -1*dir ) {
        Backlash_AltStepper.setMaxSpeed(2500.0);
        Backlash_AltStepper.setSpeed(2500*dir);
            while(Backlash_AltStepper.currentPosition()!=1500*dir) {
            Backlash_AltStepper.runSpeed();
            }
        } 
          
          
          //// with acceleration
          AltStepper.runToNewPosition(posi*dir);
          
          digitalWrite(LED_BUILTIN, HIGH);
          digitalWrite(PIN_alt_Sleep, LOW);
          delay(130);
          //odroid_serial = 'R'; // rien
          
          Serial.println("ARDUINO-DONE");  // done
          delay(1000);
          odroid_serial = ' ';

          previous_alt_dir = dir;
}

void Azimut(int dir, int posi) {

          AzimutStepper.setCurrentPosition(0);
          digitalWrite(LED_BUILTIN, LOW);
          delay(100);
          digitalWrite(PIN_azimut_Sleep, HIGH);

          // no acceleration
          //AzimutStepper.setSpeed(180*dir);
          //while(AzimutStepper.currentPosition()!=200*dir) {
          //  AzimutStepper.runSpeed();
          //}

          if ( previous_azimut_dir == -1*dir ) {
             Backlash_AzimutStepper.setMaxSpeed(2500.0);
             Backlash_AzimutStepper.setSpeed(2500*dir);
                while(Backlash_AzimutStepper.currentPosition()!=3850*dir) {
                Backlash_AzimutStepper.runSpeed();
                }
          }
           

          //// with acceleration
          AzimutStepper.runToNewPosition(posi*dir);
          
          digitalWrite(LED_BUILTIN, HIGH);
          digitalWrite(PIN_azimut_Sleep, LOW);
          delay(130);

          Serial.println("ARDUINO-DONE");  // done
          delay(100);
          odroid_serial = ' ';
          
          previous_azimut_dir = dir;
}

   



void setup() {

  // power on LED
  pinMode(13, OUTPUT);

  // Infra-Red
  IrReceiver.begin(IR_RECEIVE_PIN);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  FocusStepper.setMaxSpeed(1000.0);

  // AccelStepper value:max speeed and acceleration - default values for 1/2 step
  AzimutStepper.setMaxSpeed(600.0);
  AltStepper.setMaxSpeed(600.0);
  AzimutStepper.setAcceleration(1000.0);
  AltStepper.setAcceleration(1000.0);

 
  pinMode(PIN_azimut_Sleep, OUTPUT);
  pinMode(PIN_alt_Sleep, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);

  pinMode(PIN_AZ_MS1, OUTPUT);
  pinMode(PIN_AZ_MS2, OUTPUT);
  pinMode(PIN_ALT_MS1, OUTPUT);
  pinMode(PIN_ALT_MS2, OUTPUT);



// set default step to 1/2 step ( key CH )
  digitalWrite(PIN_AZ_MS1, HIGH);            
  digitalWrite(PIN_AZ_MS2, HIGH);
  digitalWrite(PIN_ALT_MS1, HIGH);            
  digitalWrite(PIN_ALT_MS2, HIGH);

// Set the Sleep mode to sleep.
  digitalWrite(PIN_azimut_Sleep, LOW);            
  digitalWrite(PIN_alt_Sleep, LOW);             

  Serial.begin(9600);
  Serial.setTimeout(1000); // in ms, used to stop Serial read string
  dht_intake.begin();
  dht_outflow.begin();



}

void loop() {

digitalWrite(PIN_power_ON_LED, HIGH); 

// two types of controls: serial from odroid and IR from remote

////////////////////////
// SERIAL with odroid //
////////////////////////

if (Serial.available()) {
  odroid_serial = Serial.read();
}

// if odroid requests a sensor value, send results
if (odroid_serial =='Y') {
  // LM35
  analog0 = analogRead(PIN_LM35);
  temp = analog0 * (5000 / 1024.0) / 10;
  // DHT
  h_intake = dht_intake.readHumidity();
  t_intake = dht_intake.readTemperature();
  h_outflow = dht_outflow.readHumidity();
  t_outflow = dht_outflow.readTemperature();
  h_eq_table = dht_eq_table.readHumidity();
  t_eq_table = dht_eq_table.readTemperature();

  Serial.print("\"temp\":");Serial.print(temp);Serial.print(",");
  Serial.print("\"t_eq_table\":");Serial.print(t_eq_table);Serial.print(",");
  Serial.print("\"h_eq_table\":");Serial.print(h_eq_table);Serial.print(",");
  Serial.print("\"t_intake\":");Serial.print(t_intake);Serial.print(",");
  Serial.print("\"h_intake\":");Serial.print(h_intake);Serial.print(",");
  Serial.print("\"t_outflow\":");Serial.print(t_outflow);Serial.print(",");
  Serial.print("\"h_outflow\":");Serial.println(h_outflow);
  delay(1000);
  odroid_serial = ' ';
 }

//////////// custom for goto ////////////
// O P K L to start receiving digits and M to end
// https://www.baldengineer.com/arduino-multi-digit-integers.html

if (odroid_serial =='O') {
    String steps = "";
    String message_to_odroid = "";
    while (Serial.available() == 0) {} // wait for data
    steps = Serial.readString();
        if (steps == "") {
      message_to_odroid = "steps is empty";
    }
    else {
    steps.trim(); 
    int gosteps = steps.toInt();    
    message_to_odroid = "start AZ-" + steps;
    delay(200);
    Serial.println(message_to_odroid);   // send back to Odroid to check it's OK
    delay(200);
    //move !
    custom(gosteps);
    Azimut(-1,posi);
    odroid_serial = ' '; // rien
    }
 }

if (odroid_serial =='P') {
    String steps = "";
    String message_to_odroid = "";
    while (Serial.available() == 0) {} 
    steps = Serial.readString();
        if (steps == "") {
      message_to_odroid = "steps is empty";
    }
    else {
    steps.trim(); 
    int gosteps = steps.toInt();
    message_to_odroid = "start AZ+" + steps;
    delay(200);
    Serial.println(message_to_odroid);   // send back to Odroid to check it's OK
    delay(200);
    //move !
    custom(gosteps);
    Azimut(1,posi);
    odroid_serial = ' '; // rien
    }
 }

if (odroid_serial =='K') {
    String steps = "";
    String message_to_odroid = "";
    while (Serial.available() == 0) {} 
    steps = Serial.readString();
        if (steps == "") {
      message_to_odroid = "steps is empty";
    }
    else {
    steps.trim(); 
    int gosteps = steps.toInt();
    message_to_odroid = "start VC-" + steps;
    delay(200);
    Serial.println(message_to_odroid);   // send back to Odroid to check it's OK
    delay(200);
    //move !
    custom(gosteps);
    Alt(-1,posi);
    odroid_serial = ' '; // rien
    }
 }

 if (odroid_serial =='L') {
    String steps = "";
    String message_to_odroid = "";
    while (Serial.available() == 0) {} 
    steps = Serial.readString();
    if (steps == "") {
      message_to_odroid = "steps is empty";
    }
    else {
    steps.trim(); 
    int gosteps = steps.toInt();
    message_to_odroid = "start VC+" + steps;
    delay(200);
    Serial.println(message_to_odroid);   // send back to Odroid to check it's OK
    delay(200);
    //move !
    custom(gosteps);
    Alt(1,posi);
    odroid_serial = ' '; // rien
    }
 }

//////////// slow ////////////
// if odroid requests azimut run CCW
if (odroid_serial =='X') {
          slow();
          Azimut(-1,posi);
          odroid_serial = ' '; // rien
 }

// if odroid requests azimut run CW
if (odroid_serial =='S') {
          slow();
          Azimut(1,posi);
          odroid_serial = ' ';
 }

// if odroid requests alt run CCW
if (odroid_serial =='H') {
          slow();
          Alt(-1,posi);
          odroid_serial = ' ';
 }

// if odroid requests alt run CW
if (odroid_serial =='I') {
          slow();
          Alt(1,posi);
          odroid_serial = ' ';
 } 



 
//////////// normal (default) ////////////
// if odroid requests azimut run CCW
if (odroid_serial =='A') {
          normal();
          Azimut(-1,posi);
          odroid_serial = ' '; // rien
 }

// if odroid requests azimut run CW
if (odroid_serial =='Z') {
          normal();
          Azimut(1,posi);
          odroid_serial = ' ';
 }

// if odroid requests alt run CCW
if (odroid_serial =='E') {
          normal();
          Alt(-1,posi);
          odroid_serial = ' ';
 }

// if odroid requests alt run CW
if (odroid_serial =='D') {
          normal();
          Alt(1,posi);
          odroid_serial = ' ';
 } 


//////////// fast ////////////
// if odroid requests azimut run CCW
if (odroid_serial =='C') {
          fast();
          Azimut(-1,posi);
          delay(100);
          odroid_serial = ' ';
 }

// if odroid requests azimut run CW
if (odroid_serial =='V') {
          fast();
          Azimut(1,posi);
          delay(100);
          odroid_serial = ' ';
 }

// if odroid requests alt run CCW
if (odroid_serial =='J') {
          fast();
          Alt(-1,posi);
          delay(100);
          odroid_serial = ' ';
 }

// if odroid requests alt run CW
if (odroid_serial =='U') {
          fast();
          Alt(1,posi);
          delay(100);
          odroid_serial = ' ';
 } 
 

// fine FOCUS (direction, position, speed)
if (odroid_serial =='F') {
          Focus(1,500,500);
          odroid_serial = ' ';
}

if (odroid_serial =='G') {
          Focus(-1,500,500);
          odroid_serial = ' ';
}

// fast FOCUS (direction, position, speed)
if (odroid_serial =='R') {
          Focus(1,3000,900);
          odroid_serial = ' ';
}

if (odroid_serial =='T') {
          Focus(-1,3000,900);
          odroid_serial = ' ';
}

/////////////////////////////
// IR from remote //////////
////////////////////////////

    if (IrReceiver.decode()) {
    //Serial.print("Code: ");
   // Serial.println(IrReceiver.decodedIRData.decodedRawData);
    IrReceiver.resume();
    FocusStepper.setCurrentPosition(0);
    AzimutStepper.setCurrentPosition(0);
    AltStepper.setCurrentPosition(0);


   switch (IrReceiver.decodedIRData.decodedRawData) {

// step for AZ et ALT

      //1
     case KEY_1: 
            slow();
            if (IrReceiver.decode()) {
            IrReceiver.resume();         
            } 
      break;

      //2
     case KEY_2:
            normal();
            if (IrReceiver.decode()) {
            IrReceiver.resume();         
            } 
      break;

      //3
       case KEY_3:
            fast();
            if (IrReceiver.decode()) {
            IrReceiver.resume();         
            } 
      break;


// focus
// v plus/moins = pas trop vite
// p plus/moins = fast
// direction, position, speed

     case KEY_vmoins:
          Focus(-1,500,500);
            if (IrReceiver.decode()) {;
            IrReceiver.resume();  
            }
     break;

     case KEY_vplus:
          Focus(1,500,500);
            if (IrReceiver.decode()) {;
            IrReceiver.resume();  
            }
     break;

     case KEY_pmoins:
          Focus(-1,3000,900);
            if (IrReceiver.decode()) {;
            IrReceiver.resume();  
            }
     break;

     case KEY_pplus:
          Focus(1,3000,900);
            if (IrReceiver.decode()) {;
            IrReceiver.resume();  
            }
     break;

// end IR sensor section for focus

// IR sensor section for stepper azimut

     case KEY_L:
          Azimut(-1,posi);
            if (IrReceiver.decode()) {;
            IrReceiver.resume();  
            } 
      break;

      case KEY_R:
          Azimut(1,posi);
            if (IrReceiver.decode()) {
            IrReceiver.resume();        
            } 
      break;

// IR sensor section for stepper alt

 case KEY_U:
          Alt(-1,posi);
            if (IrReceiver.decode()) {
            IrReceiver.resume();  
            } 
      break;

 case KEY_D:
          Alt(1,posi);
            if (IrReceiver.decode()) {
            IrReceiver.resume();          
            } 
      break;

     }  //end switch


  } //end IR read signal

  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(PIN_azimut_Sleep, LOW);
  digitalWrite(PIN_alt_Sleep, LOW);
  digitalWrite(7, LOW);
  digitalWrite(8, LOW);
  digitalWrite(9, LOW);
  digitalWrite(10, LOW);



  
  
}
