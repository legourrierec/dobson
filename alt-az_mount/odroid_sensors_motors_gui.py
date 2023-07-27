#!/usr/bin/env python3

## about this script
# manual control of the Dobson : 
#       focus, 
#       steppers Az and Alt
#       sensors

## functions:
# hw_check                 verify if arduino is connected
# get_sensors              send command to arduino and collect measurements
# azimut and alt         send commands to arduino for stepper action           

######################
### import modules ###
######################
import serial               # arduino communication
import subprocess           # run bash command from python
import json                 # handle ardiuno data
#import time                 # look it's not used ??? check
import tkinter as tk        # GUI
from tkinter import ttk     # GUI
from pathlib import Path    # check if file exist


######################
### GUI parameters ###
######################
root = tk.Tk()
root.title('DOBSON CONTROL')
tk_bkgd='#cbc9cc'

# . means default style all root elements
s = ttk.Style()
s.configure('.', background=tk_bkgd) 

# background main window
root['bg']=tk_bkgd

# dimension and position
window_width = 400
window_height = 1000

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

position_x = int(screen_width - window_width)
position_y = 0

root.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

######################
### functions      ###
######################

def hw_check():
    """
    kill and relaunch window
    """
    root.destroy()
    subprocess.run(['python3','odroid_sensors_motors_gui.py'])
    

def get_sensors():
    """
    request and receive arduino sensor measurements
    update GUI with values when button 'refresh' is pressed
    """
    ser.write(bytes('Y','UTF-8'))
    # check buffer, if 0 wait (pass = do nothing)
    while (ser.inWaiting() == 0):
      pass
    # read line of data
    serial = ser.readline()
    # decode (removes \r\n )
    output_string=serial.decode('utf-8')
    # removes extra characters like line return
    output_string=output_string.strip()
    # append curly brackets so we can use the ouput as a dictionary
    output_string="{" + output_string + "}"
    # convert string to dictionary
    output_dic=json.loads(output_string)

    # color for h_intake according to value
    if output_dic["h_intake"] < 80:
      colorfont = "#20A904"
    if output_dic["h_intake"] > 80 and output_dic["h_intake"] < 90:
      colorfont = "#D78000"
    if output_dic["h_intake"] > 90:
      colorfont = "#C21200"
 
    if output_dic["h_eq_table"] < 80:
      colorfont = "#20A904"
    if output_dic["h_eq_table"] > 80 and output_dic["h_eq_table"] < 90:
      colorfont = "#D78000"
    if output_dic["h_eq_table"] > 90:
      colorfont = "#C21200"

    # parse data into tkinter grid
    LM35_sensor.config(text=str(output_dic["temp"]) + " °C",background=tk_bkgd)
    in_temp_sensor.config(text=str(output_dic["t_intake"]) + " °C",background=tk_bkgd)
    out_temp_sensor.config(text=str(output_dic["t_outflow"]) + " °C",background=tk_bkgd)
    in_humi_sensor.config(text=str(output_dic["h_intake"]) + " %",background=tk_bkgd, font='helvetica 15 bold', foreground=colorfont)
    out_humi_sensor.config(text=str(output_dic["h_outflow"]) + " %",background=tk_bkgd)
    
    eq_table_temp_sensor.config(text=str(output_dic["t_eq_table"]) + " °C",background=tk_bkgd)
    eq_table_humi_sensor.config(text=str(output_dic["h_eq_table"]) + " %",background=tk_bkgd, font='helvetica 15 bold', foreground=colorfont)

    # get odroid own temperature value (soc=system on chip, skip ddr)
    odroid_sensors = subprocess.getoutput("sensors -j")
    odroid_sensors_json = json.loads(odroid_sensors)
    odroid_soc_temp = odroid_sensors_json['soc_thermal-virtual-0']['temp1']['temp1_input']
    odroid_temp_sensor.config(text=str(odroid_soc_temp) + " °C",background=tk_bkgd)


# stepper action

def azimut_plus_1():
    ser.write(bytes('S','UTF-8'))

def azimut_moins_1():
    ser.write(bytes('X','UTF-8'))

def azimut_plus_2():
    ser.write(bytes('Z','UTF-8'))

def azimut_moins_2():
    ser.write(bytes('A','UTF-8'))

def azimut_plus_3():
    ser.write(bytes('V','UTF-8'))

def azimut_moins_3():
    ser.write(bytes('C','UTF-8'))


# alt

def alt_plus_1():
    ser.write(bytes('I','UTF-8'))

def alt_moins_1():
    ser.write(bytes('H','UTF-8'))

def alt_plus_2():
    ser.write(bytes('D','UTF-8'))

def alt_moins_2():
    ser.write(bytes('E','UTF-8'))

def alt_plus_3():
    ser.write(bytes('U','UTF-8'))

def alt_moins_3():
    ser.write(bytes('J','UTF-8'))


# focus

def focusplus():
    ser.write(bytes('F','UTF-8'))

def focusplusplus():
    ser.write(bytes('R','UTF-8'))

def focusmoins():
    ser.write(bytes('G','UTF-8'))

def focusmoinsmoins():
    ser.write(bytes('T','UTF-8'))
    
def focusmoinsfine():
    ser.write(bytes('B','UTF-8'))
    
def focusplusfine():
    ser.write(bytes('N','UTF-8'))        


    
######################
######  main  ########
######################

# define frame for focus
frame_focus = ttk.LabelFrame(root,width=360, height=300, borderwidth=1, relief="groove", labelanchor='n', text=" FOCUS ")
frame_focus.grid(column=0, row=0, padx=20, pady=20, columnspan=7)

# 5 columns
frame_focus.columnconfigure(0, weight=1)
frame_focus.columnconfigure(1, weight=1)
frame_focus.columnconfigure(2, weight=1)
frame_focus.columnconfigure(3, weight=1)
frame_focus.columnconfigure(4, weight=1)
frame_focus.columnconfigure(5, weight=1)

# widgets
focus_moinsmoins_button = ttk.Button(frame_focus, text="<<<",command=focusmoinsmoins)
focus_moinsmoins_button.grid(column=0, row=0, sticky=tk.N, padx=8, pady=15, ipadx=5,ipady=5)

focus_moins_button = ttk.Button(frame_focus, text="<<",command=focusmoins)
focus_moins_button.grid(column=1, row=0, sticky=tk.N, padx=8, pady=15, ipadx=5,ipady=5)

focus_moins_fine_button = ttk.Button(frame_focus, text="<",command=focusmoinsfine)
focus_moins_fine_button.grid(column=2, row=0, sticky=tk.N, padx=8, pady=15, ipadx=5,ipady=5)


focus_plus_fine_button = ttk.Button(frame_focus, text=">",command=focusplusfine)
focus_plus_fine_button.grid(column=3, row=0, sticky=tk.N, padx=8, pady=15, ipadx=5,ipady=5)

focus_plus_button = ttk.Button(frame_focus, text=">>",command=focusplus)
focus_plus_button.grid(column=4, row=0, sticky=tk.N, padx=8, pady=15, ipadx=5,ipady=5)

focus_plusplus_button = ttk.Button(frame_focus, text=">>>",command=focusplusplus)
focus_plusplus_button.grid(column=5, row=0, sticky=tk.N, padx=8, pady=15, ipadx=5,ipady=5)


# define frame for steppers azimut and alt 
frame_steppers = ttk.LabelFrame(root,width=360, height=300, borderwidth=1, relief="groove", labelanchor='n', text=" ALT - AZ CONTROL ")
frame_steppers.grid(column=0, row=1, padx=20, pady=20, columnspan=7)

# 7 columns
frame_steppers.columnconfigure(0, weight=1)
frame_steppers.columnconfigure(1, weight=1)
frame_steppers.columnconfigure(2, weight=1)
frame_steppers.columnconfigure(3, weight=1)
frame_steppers.columnconfigure(4, weight=1)
frame_steppers.columnconfigure(5, weight=1)
frame_steppers.columnconfigure(6, weight=1)

# widgets

alt_plus_3_button = ttk.Button(frame_steppers, text="+++",command=alt_plus_3)
alt_plus_3_button.grid(column=3, row=0, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

alt_plus_2_button = ttk.Button(frame_steppers, text="++",command=alt_plus_2)
alt_plus_2_button.grid(column=3, row=1, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

alt_plus_1_button = ttk.Button(frame_steppers, text="+",command=alt_plus_1)
alt_plus_1_button.grid(column=3, row=2, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

azimut_moins_3_button = ttk.Button(frame_steppers, text="---",command=azimut_moins_3)
azimut_moins_3_button.grid(column=0, row=3, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

azimut_moins_2_button = ttk.Button(frame_steppers, text="--",command=azimut_moins_2)
azimut_moins_2_button.grid(column=1, row=3, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

azimut_moins_1_button = ttk.Button(frame_steppers, text="-",command=azimut_moins_1)
azimut_moins_1_button.grid(column=2, row=3, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)


azimut_plus_1_button = ttk.Button(frame_steppers, text="+",command=azimut_plus_1)
azimut_plus_1_button.grid(column=4, row=3, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

azimut_plus_2_button = ttk.Button(frame_steppers, text="++",command=azimut_plus_2)
azimut_plus_2_button.grid(column=5, row=3, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

azimut_plus_3_button = ttk.Button(frame_steppers, text="+++",command=azimut_plus_3)
azimut_plus_3_button.grid(column=6, row=3, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)


alt_moins_1_button = ttk.Button(frame_steppers, text="-",command=alt_moins_1)
alt_moins_1_button.grid(column=3, row=4, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

alt_moins_2_button = ttk.Button(frame_steppers, text="--",command=alt_moins_2)
alt_moins_2_button.grid(column=3, row=5, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

alt_moins_3_button = ttk.Button(frame_steppers, text="---",command=alt_moins_3)
alt_moins_3_button.grid(column=3, row=6, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)


# define frame for sensors
frame_sensors = ttk.LabelFrame(root,width=360, height=330, borderwidth=1, relief="groove", labelanchor='n', text=" SENSORS ")
frame_sensors.grid(column=0, row=2, padx=20, pady=20, columnspan=7)
frame_sensors.grid_propagate(0) # forces width, which is ignored otherwise


# GUI 7 columns
frame_sensors.columnconfigure(0, weight=1)
frame_sensors.columnconfigure(1, weight=1)
frame_sensors.columnconfigure(2, weight=1)
frame_sensors.columnconfigure(3, weight=1)
frame_sensors.columnconfigure(4, weight=1)
frame_sensors.columnconfigure(5, weight=1)
frame_sensors.columnconfigure(6, weight=1)

# widgets (labels on column span 4, sensor values column span 3)

empty_label = ttk.Label(frame_sensors, text=" ", anchor="e")   # one line spacing
empty_label.grid(column=0, row=10, columnspan=4, sticky=tk.E, padx=0, pady=0)

LM35_label = ttk.Label(frame_sensors, text="Stepper driver temp (LM35): ", anchor="e")
LM35_label.grid(column=0, row=11, columnspan=4, sticky=tk.E, padx=5, pady=5)
LM35_label.configure(background=tk_bkgd)
LM35_sensor = ttk.Label(frame_sensors, text="", anchor="w")
LM35_sensor.grid(column=5, row=11, columnspan=2, sticky=tk.W, padx=5, pady=5)

eq_table_temp_label = ttk.Label(frame_sensors, text="Eq. table temp (DHT22): ", anchor="e")
eq_table_temp_label.grid(column=0, row=12, columnspan=4, sticky=tk.E, padx=5, pady=5)
eq_table_temp_label.configure(background=tk_bkgd)
eq_table_temp_sensor = ttk.Label(frame_sensors, text="", anchor="w")
eq_table_temp_sensor.grid(column=5, row=12, columnspan=2, sticky=tk.W, padx=5, pady=5)

in_temp_label = ttk.Label(frame_sensors, text="Intake temp (DHT22): ", anchor="e")
in_temp_label.grid(column=0, row=13, columnspan=4, sticky=tk.E, padx=5, pady=5)
in_temp_label.configure(background=tk_bkgd)
in_temp_sensor = ttk.Label(frame_sensors, text="", anchor="w")
in_temp_sensor.grid(column=5, row=13, columnspan=2, sticky=tk.W, padx=5, pady=5)

out_temp_label = ttk.Label(frame_sensors, text="Outflow temp (DHT22): ", anchor="e")
out_temp_label.grid(column=0, row=14, columnspan=4, sticky=tk.E, padx=5, pady=5)
out_temp_label.configure(background=tk_bkgd)
out_temp_sensor = ttk.Label(frame_sensors, text="", anchor="w")
out_temp_sensor.grid(column=5, row=14, columnspan=2, sticky=tk.W, padx=5, pady=5)

eq_table_humi_label = ttk.Label(frame_sensors, text="Eq. table humidity (DHT22): ", anchor="e")
eq_table_humi_label.grid(column=0, row=15, columnspan=4, sticky=tk.E, padx=5, pady=5)
eq_table_humi_label.configure(background=tk_bkgd)
eq_table_humi_sensor = ttk.Label(frame_sensors, text="", anchor="w")
eq_table_humi_sensor.grid(column=5, row=15, columnspan=2, sticky=tk.W, padx=5, pady=5)

in_humi_label = ttk.Label(frame_sensors, text="Intake humidity (DHT22): ", anchor="e")
in_humi_label.grid(column=0, row=16, columnspan=4, sticky=tk.E, padx=5, pady=5)
in_humi_label.configure(background=tk_bkgd)
in_humi_sensor = ttk.Label(frame_sensors, text="", anchor="w")
in_humi_sensor.grid(column=5, row=16, columnspan=2, sticky=tk.W, padx=5, pady=5)

out_humi_label = ttk.Label(frame_sensors, text="Outflow humidity (DHT22): ",anchor="e")
out_humi_label.grid(column=0, row=17, columnspan=4, sticky=tk.E, padx=5, pady=5)
out_humi_label.configure(background=tk_bkgd)
out_humi_sensor = ttk.Label(frame_sensors, text="", anchor="w")
out_humi_sensor.grid(column=5, row=17, columnspan=2, sticky=tk.W, padx=5, pady=5)


odroid_temp_label = ttk.Label(frame_sensors, text="Odroid temp (SOC): ",anchor="e")
odroid_temp_label.grid(column=0, row=18, columnspan=4, sticky=tk.E, padx=5, pady=5)
odroid_temp_label.configure(background=tk_bkgd)

odroid_temp_sensor = ttk.Label(frame_sensors, text="", anchor="w")
odroid_temp_sensor.grid(column=5, row=18, columnspan=2, sticky=tk.W, padx=5, pady=5)



refresh_button = ttk.Button(frame_sensors, text="refresh", command=get_sensors)
refresh_button.grid(column=5, row=19, columnspan=2, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)




# GUI 7 columns
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)
root.columnconfigure(3, weight=1)
root.columnconfigure(4, weight=1)
root.columnconfigure(5, weight=1)
root.columnconfigure(6, weight=1)

info_label = ttk.Label(root, text="", anchor="n")
info_label.grid(column=0, row=19, columnspan=7, sticky=tk.N, padx=5, pady=5, ipadx=5,ipady=5)
info_label.configure(background=tk_bkgd)



hw_check = ttk.Button(root,text="HW check",command=hw_check)
hw_check.grid(column=0, row=20, columnspan=2, sticky=tk.E, padx=5, pady=5, ipadx=5,ipady=10)

quit_button = ttk.Button(root, text="QUIT",command=exit)
quit_button.grid(column=5, row=20, columnspan=2, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=10)

arduino_is_here = subprocess.getoutput('ls /dev/ttyACM0')  #not very pythonian but path is_file returned false


if arduino_is_here == "/dev/ttyACM0":
    # initialise serial connection (device, baud rate)
    ser = serial.Serial('/dev/ttyACM0', 9600)
    # clear the serial line (optional)
    ser.flushInput()
else:
    info_label.config(text="arduino not connected", background=tk_bkgd, foreground='#FF0000', font='Helvetica 14 bold')
    refresh_button.configure(state='disabled')
    alt_moins_3_button.configure(state='disabled')
    alt_moins_2_button.configure(state='disabled')
    alt_moins_1_button.configure(state='disabled')
    alt_plus_3_button.configure(state='disabled')
    alt_plus_2_button.configure(state='disabled')
    alt_plus_1_button.configure(state='disabled')
    azimut_moins_3_button.configure(state='disabled')
    azimut_moins_2_button.configure(state='disabled')
    azimut_moins_1_button.configure(state='disabled')
    azimut_plus_3_button.configure(state='disabled')
    azimut_plus_2_button.configure(state='disabled')
    azimut_plus_1_button.configure(state='disabled')
    focus_moinsmoins_button.configure(state='disabled')
    focus_moins_button.configure(state='disabled')
    focus_plusplus_button.configure(state='disabled')
    focus_plus_button.configure(state='disabled')
    focus_plus_fine_button.configure(state='disabled')
    focus_moins_fine_button.configure(state='disabled')
   

# the main loop keeps the window open
root.mainloop()


