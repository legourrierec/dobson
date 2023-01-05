# INTRODUCTION

The code presented in this project has the following objectives:

  * drive the equatorial table in order to compensate the Earth rotation and follow a target in the sky
  * drive the telescope ALT-AZ axis using either an Infra-Red remote or a Python-based interface
  * display sensor values (temperature and humidity)
  * assist the observer in reaching the target by offering a goto solution

The telescope is home-made, starting from a blank disk of glass, all the way to fitting a camera for astrophotography. The whole project is being documented on instructables.com (link to be published later).


![Alt text](img/dobson300-1500.jpg)


# HARDWARE COMPONENTS

**equatorial table** 

* arduino Uno
* 1 bigeasydriver
* powersupply
* LM35 temperature sensor
* DHT22 temperature and humidity sensor
* 2 30x30mm fans (IN and OUT)
* polyimide heating element
* RGB LED, connectors, switches
* 1 Nema 17 stepper motor
 
**rocker**

* arduino Mega
* Odroid N2+ (Ubuntu Mate) with WiFi dongle
* 2 bigeasydriver
* split-ring
* LM35 temperature sensor
* 2 DHT22 temperature and humidity sensor (air IN and air OUT)
* 2 30x30mm fans (IN and OUT)
* polyimide heating element
* IR sensor
* LEDs, connectors, switches
* 2 Nema 17 stepper motors

# ODROID CONFIGURATION

The Odroid N2+ (4Gb RAM) runs Ubuntu Mate with Python3. Additional packages include:

* astap (for plate solving) [https://www.hnsky.org/astap.htm](URL)
* lm-sensors (read Odroid heat sensors)
* kstars (image acquisitions with EKOS) [https://edu.kde.org/kstars/](URL)
* python3-tk (GUI)
* python3-serial (USB communication with Arduino)
* arduino IDE
* camera-zwo-asi python [https://pypi.org/project/camera-zwo-asi/](URL)


# EQUATORIAL TABLE: ARDUINO CODE



# ROCKER: ALT-AZ ARDUINO CODE



# ROCKER: MOTOR AND SENSORS PYTHON CODE


# ROCKER: SOLVE AND GOTO PYTHON CODE
