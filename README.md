# INTRODUCTION

The code presented in this project has the following objectives:

  * drive the equatorial table in order to compensate the Earth rotation and follow a target in the sky
  * drive the telescope ALT-AZ axis using either an Infra-Red remote or a Python-based interface
  * display sensor values (temperature and humidity)
  * assist the observer in reaching the target by offering a goto solution

The telescope is home-made starting from a blank disk of glass, all the way to fitting a camera for astrophotography. The whole project is being documented on instructables.com (link to be published later).


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

**rocker**

* arduino Mega
* Odroid N2+ (Ubuntu Mate) with WiFi dongle
* 2 bigeasydriver
* splitring
* LM35 temperature sensor
* 2 DHT22 temperature and humidity sensor (air IN and air OUT)
* 2 30x30mm fans (IN and OUT)
* polyimide heating element
* IR sensor
* LEDs, connectors, switches

# ODROID CONFIGURATION



# EQUATORIAL TABLE: ARDUINO CODE



# ROCKER: ALT-AZ ARDUINO CODE



# ROCKER: MOTOR AND SENSORS PYTHON CODE


# ROCKER: SOLVE AND GOTO PYTHON CODE
