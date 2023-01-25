#!/usr/bin/env python3

## about this script
# 1. point telescope as near as possible to target
# 2. enter target name (Messier or NGC)
# 3. button "take image" => script takes image and saves it as calibration_image.png
# 4. select image 
# 5. button "find coordinates" : 
#   queries Sac72.txt local file to find target coord.
#   runs astap_cli to find image coordinates
# 6. button "calibrate" (disabled if cam not detected)
#       moves dobson 3x azimut +++ then ---, followed by 3x vertical +++ then --- (arduino "fast")
#       each time, it takes an image and solves it
#       displays az and vc coordinates of target and image
#       it works out:
#           angle with astronomical ra/dec coordinates plane 
#           displacement az and vc each time a motor moves
# 7. button "compare" (disabled until calibration has been done)
#       displays difference between target and image (az and vc)
#       display how many steps the motors should move
# 8. button "go to target" (disabled until comparison done)
#       triggers move az and vc
#       takes image and solves it
#       display difference with target coordinates and number of steps required

# this version: v11:
  # lines zwo_image() are enabled instead of simulation with use_set_of_image
  # it finds the line "Solution found" in the output of astap_cli instead of by index
  # works well (except when azimut struggles to move)

## variables:

# plan dobson:      AZ= azimut              ALT= altitude
# plan astro:       RA= right ascension     DEC= declination    spd=south pole declination (+90)
# direction:        p= positive             n= negative
# object:           target= target          img = image

## functions:

# hms_dms_dd            converts coordinates from hh mm ss to degrees,decimal
# zwo_image             takes image and save as png
# get_target_coord      get target coordinates from file Sac72.txt  
# get_image_coord       get image coordinates using astap
# solve_single_img      calls in sequence get_target_coord and get_image_coord
# angle                 returns angle between astro and dobson axis
# convert_coord         convert astronomical ra/dec to dobson az/alt
# browse_image          browse to get and solve single image
# calibrate             work out angle between astro and dobson axis, and displacement per move, returns position to target on dobson axis
#                           calls get_target_coord, zwo_image, get_image_coord then, compare_coord 
# go_to                 confirm and trigger motors, re-evaluate if target not reached
# azimut,alt,focus    arduino stepper requests
# wait_for_arduino      allows for feedback as to when action has been completed


######################
## import modules ####
######################
                  
import subprocess                       # used to run bash "astap" command ('os' cannot save output to variable)
                                            # and also for "grep" command to search target in text file Sac72.txt
import tkinter as tk                    # used for gui
from tkinter import ttk                 # used for gui tkinter widgets
from tkinter import filedialog          # used for "select image file" dialog box
from pathlib import Path                # used in zwo asi image capture config file selection
import camera_zwo_asi                   # used for zwo asi image capture
from statistics import mean,stdev       # used in calibration in go_to function
import serial                           # communicate with arduino
from math import atan2,cos,sin,degrees  # calculate image coordinates in Dobson reference
from time import sleep                  # delay sleep
import datetime                         # display time of events
from shutil import copyfile             # used in function use_set_of_image to copy as image as calibration_image.png - disable when not needed


######################
### GUI parameters ###
######################
root = tk.Tk()
root.title('SOLVE AND GOTO')
tk_bkgd='#cbc9cc'

# . means default style all root elements
s = ttk.Style()
s.configure('.', background=tk_bkgd) 

# background main window
root['bg']=tk_bkgd

# dimension and position
window_width = 360
window_height = 1000

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

position_x = int(screen_width - window_width - 400)
position_y = 0

root.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')


######################
####  functions  #####
######################

def hw_check():
    """
    kill and relaunch window
    """
    root.destroy()
    subprocess.run(['python3','solve_and_goto.py'])
    

# stepper action

def wait_for_arduino():
    """
    when python sends command to arduino, it waits until arduino says it's done
    python does not check the actual response but it could do
    """
    ## check buffer, if 0 wait (pass = do nothing)
    while (ser.inWaiting() == 0):             # wait for arduino response
      #print("nothing received")
      pass
    ## read line of data
    serial = ser.readline()
    ## decode (removes \r\n )
    output_string=serial.decode('utf-8')
    ## removes extra characters like line return
    output_string=output_string.strip()
    print(output_string)
    # calibration move
    if (output_string == "ARDUINO-DONE"):
        info = (datetime.datetime.now()).strftime("%X") + " => arduino: stepper move done"
        done_label.configure(text=str(info))
        done_label.update()
        sleep(1) 
    ser.flushInput()
    # goto move
    # check if output_string contains a digit (in which case it's Arduino confirming nb of steps
    if output_string[-1].isdigit():
        info = (datetime.datetime.now()).strftime("%X") + " => arduino " + output_string + " steps"
        done_label.configure(text=str(info))
        done_label.update()


def azimut_plus_1():
    doing_label.config(text="requested moving az+", background=tk_bkgd)
    ser.write(bytes('S','UTF-8'))
    done_label.config(text="done moving az+", background=tk_bkgd)

def azimut_moins_1():
    ser.write(bytes('X','UTF-8'))

def azimut_plus_2():
    ser.write(bytes('Z','UTF-8'))

def azimut_moins_2():
    ser.write(bytes('A','UTF-8'))

def azimut_plus_3():
    info = (datetime.datetime.now()).strftime("%X") + " => moving AZ +++"
    done_label.configure(text=str(info))
    done_label.update()
    ser.write(bytes('V','UTF-8'))
    sleep(0.5) 
    wait_for_arduino()
    #sleep(5)         # just to make sure Dobson is stable before image
    #info_label.config(text="done moving az+++", background=tk_bkgd)


def azimut_moins_3():
    info = (datetime.datetime.now()).strftime("%X") + " => moving AZ ---"
    done_label.configure(text=str(info))
    done_label.update()
    ser.write(bytes('C','UTF-8'))
    sleep(0.5) 
    wait_for_arduino()
    #sleep(5)         # just to make sure Dobson is stable before image
    #info_label.config(text="done moving az---", background=tk_bkgd)


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
    info = (datetime.datetime.now()).strftime("%X") + " => moving D +++"
    done_label.configure(text=str(info))
    done_label.update()
    ser.write(bytes('U','UTF-8'))
    sleep(0.5)  
    wait_for_arduino()
    #sleep(5)         # just to make sure Dobson is stable before image
    #info_label.config(text="done moving alt+++", background=tk_bkgd)

def alt_moins_3():
    info = (datetime.datetime.now()).strftime("%X") + " => moving D ---"
    done_label.configure(text=str(info))
    done_label.update()
    ser.write(bytes('J','UTF-8'))
    sleep(0.5) 
    wait_for_arduino()
    #sleep(5)         # just to make sure Dobson is stable before image
    #info_label.config(text="done moving alt---", background=tk_bkgd)


# focus

def focusplus():
    ser.write(bytes('F','UTF-8'))

def focusplusplus():
    ser.write(bytes('R','UTF-8'))

def focusmoins():
    ser.write(bytes('G','UTF-8'))

def focusmoinsmoins():
    ser.write(bytes('T','UTF-8'))



def hms_dms_dd(ra, dec, delimiter=" "):
    """Convert from HMS; DMS to DD.
    # source: https://gist.github.com/Sunmish/08df2cb5ed7cd34ef786218ac727d86c
    Examples:
    >>> ra, dec = hms_dms_dd("00h59m59.3s", "-00d00m01.01s")
    >>> ra, dec
    (14.997083333333332, -0.00028055555555555554)
    >>> ra, dec = hms_dms_dd("23 59 59", "+56 00 00")
    >>> ra, dec
    (359.99583333333334, 56.0)
    >>> ra, dec = hms_dms_dd("24:30:00", "+90:00:00")
    >>> ra, dec
    (7.5, 90.0)
    """
    try: 
        ra_dd, dec_dd = float(ra), float(dec)

    except ValueError:

        if ":" in ra:
            delimiter = ":"
        elif "h" in ra:
            ra  = ra.replace("h", " ").replace("m", " ").replace("s", " ")
            dec = dec.replace("d", " ").replace("m", " ").replace("s", " ")

        ra, dec = ra.split(delimiter), dec.split(delimiter)
        
        # RA:
        ra_hours_dd = float(ra[0]) * 15.
        ra_minutes_dd = float(ra[1]) * 15. / 60.
        ra_seconds_dd = float(ra[2]) * 15. / 3600.
        ra_dd = ra_hours_dd + ra_minutes_dd + ra_seconds_dd
        if ra_dd >= 360.:
            ra_dd = abs(ra_dd  - 360.)

        # DEC:
        if "-" in dec[0]:
            dec_dd = float(dec[0]) - (float(dec[1]) / 60.) - (float(dec[2]) / 3600.)
        else:
            dec_dd = float(dec[0]) + (float(dec[1]) / 60.) + (float(dec[2]) / 3600.)
    
    return ra_dd, dec_dd
    
    
def zwo_image():
    """ takes image and saves it as calibration_image.png
    credits: https://pypi.org/project/camera-zwo-asi/#description
    """
    info = (datetime.datetime.now()).strftime("%X") + " => image requested"
    done_label.configure(text=str(info))
    done_label.update()                            # see https://stackoverflow.com/questions/45647366/changing-tkinter-label-text-dynamically-using-label-configure
    take_image_button.configure(text="processing...")
    take_image_button.update()
    global filepath
    # just one camera = index 0
    camera = camera_zwo_asi.Camera(0)

    # use configuration in file (exposure 100000 pour 10, gain 100, binning 4, size half/full)
    conf_path = Path("/home/dlg/Documents/python") / "zwo_asi.toml" 
    camera.configure_from_toml(conf_path)

    # take image
    filepath = Path("/home/dlg/Documents/python") / "calibration_image.png" 
    show = False
    
    image = camera.capture(filepath=filepath,show=show)
  
    take_image_button.configure(text="take image")
    take_image_button.update()
    info = (datetime.datetime.now()).strftime("%X") + " => image acquisition done"
    done_label.configure(text=str(info))
    done_label.update()

def browse_image():
    """
    function to get path/image from dialog box, used when solving single image
    """
    global filename
    image_name.delete(0,'end')          # clear field from character 0 to end
    filename = tk.filedialog.askopenfilename(initialdir="/home/dlg/ekos/",filetypes=[("png files","*.png"),("fits files","*.fits"),("fit files","*.fit")])
    image_name.insert(tk.END, filename) # fails without this line

    ref = reference.get()
    
    # use this select action to validate that a number is provided as object reference. If so, enable button
    if ref.isdigit():
        find_coord_button.configure(state='enabled')
        error_label.config(text="           ", background=tk_bkgd)  
    else:
        find_coord_button.configure(state='disabled')
        image_name.delete(0,'end')
        object_ref.delete(0,'end')  
        error_label.config(text="target must be a number", background=tk_bkgd, foreground='#FF0000', font='Helvetica 14 bold') 

    
def get_target_coord():
    """
    static file Sac72.txt
    source https://www.saguaroastro.org/sac-downloads/
    """
    target_ra_value.config(text=" ", background=tk_bkgd)
    target_dec_value.config(text=" ", background=tk_bkgd)
    print("getting target coordinates")
    cat = catalog.get()     # tkinter variables
    ref = reference.get()
    
    find_coord_button.configure(state='enabled')
    global ra_target_hrs
    global spd_target
    global ra_target
    global dec_target
    
    # clear error label    
    error_label.config(text="               ", background=tk_bkgd)
    # build skyobject variable with spaces as in the data file
    if ( cat == "M" and len(ref) == 1 ):
        skyobject = "M   " + ref
    if ( cat == "M" and len(ref) == 2 ):
        skyobject = "M  " + ref
    if ( cat == "M" and len(ref) == 3 ):
        skyobject = "M " + ref

    if ( cat == "NGC" and len(ref) == 1 ):
        skyobject = "NGC    " + ref
    if ( cat == "NGC" and len(ref) == 2 ):
        skyobject = "NGC   " + ref
    if ( cat == "NGC" and len(ref) == 3 ):
        skyobject = "NGC  " + ref
    if ( cat == "NGC" and len(ref) == 4 ):
        skyobject = "NGC " + ref  
    #print(skyobject)
    # get skyobject coordinates
    file = "sac72/Sac72.txt"
    try:
        line = subprocess.check_output(['grep',skyobject,file])
        #print(line)
        list = str(line).split(",")
        ra_target_raw = list[4].replace('"','')
        dec_target_raw = list[5].replace('"','')
        
        # add ss at 00 since Sat72 only has hh mm
        seconds = "00"
        dec_target_raw = " ".join([str(dec_target_raw), str(seconds)])
        ra_target_raw = " ".join([str(ra_target_raw), str(seconds)])
        
        ra_target_hrs = ra_target_raw.split(' ')[0]   ## this is for the astap line which needs just hrs
        spd_target = dec_target_raw.split(' ')[0]     ## this is for astap, it needs decl in degrees in south pole reference, so +90 deg
        #print(ra_target_hrs,spd_target)
        
        # astap uses south pole declination so we add 90 degres
        #if "-" in spd_target:
        #    spd_target = 90 - float(spd_target.replace('-','',1))
        #if "+" in spd_target:
        #    spd_target = 90 + float(spd_target.replace('+','',1))
        spd_target = 90 + float(spd_target)

        print("ra_target_hrs= ", ra_target_hrs)
        print("spd_target= ", spd_target)
        
        # call funtion hms_dms_dd to convert to decimal and keep two decimals
        ra_target,dec_target = hms_dms_dd(ra_target_raw, dec_target_raw)
        ra_target = "{:.2f}".format(ra_target)
        dec_target = "{:.2f}".format(dec_target)
        #print(ra_target,dec_target)
        # update GUI with result
        target_ra_value.config(text=str(ra_target),background=tk_bkgd)
        target_dec_value.config(text=str(dec_target),background=tk_bkgd)
        
        return ra_target,dec_target
        
    except:
        # print("not found or error")
        target_ra_value.config(text=str("not found"),background=tk_bkgd)
        target_dec_value.config(text=str("not found"),background=tk_bkgd)
        error_label.config(text="target not found", background=tk_bkgd, foreground='#FF0000', font='Helvetica 14 bold') 
        error = "yes"
        return error
    
    # update GUI with result
    target_ra_value.config(text=str(ra_target),background=tk_bkgd)
    target_dec_value.config(text=str(dec_target),background=tk_bkgd)    


def get_image_coord(filename):
    """
    get image coordinates (solving)
    example from bash for M15: astap -f '/home/dlg/ekos/DONE/M15/Light_011.fits' -ra 21 -spd 102 -r 10 -fov 0.5
    to make it faster, use astap_cli and give it the target coordinates, a 10 degrees search radius and a field of view 0.5 d.
    astap can take png as well as fits
    could not get astap to resolve on odroid, so use astap_cli (supposed to be even faster with the right parameters)
    source: https://www.hnsky.org/astap.htm#astap_command_line
    """
    try:       
        print("ici",filename)
        img_ra_value.config(text=" ", background=tk_bkgd)
        img_dec_value.config(text=" ", background=tk_bkgd)
        info = (datetime.datetime.now()).strftime("%X") + " => coordinates requested"
        done_label.configure(text=str(info))
        done_label.update()
        find_coord_button.configure(text="processing...")
        find_coord_button.update()
                    
        # solve using bash command
        print("start solving using ", ra_target_hrs," and ",spd_target)
        answer = subprocess.check_output(f"astap_cli -f \"{filename}\" -ra {ra_target_hrs} -spd {spd_target} -r 15 -d /opt/astap -fov 0.5", shell=True, encoding="utf8")
        print("solving done")
        print("answer",answer)
        # solution is on the 2nd or 3rd line from last, so splitline by index does not always work
        # solution = answer.splitlines()[-3]
        # best find the line that contains "Solution found"
        for coord in answer.split('\n'):
    	    if 'Solution found' in coord:
                solution = coord
        
        # it looks like this: "Solution found: 00: 42  49.4 +41d 19  13". Remove Solution found, extra spaces, : and d   
        solution = solution.replace('Solution found','')
        solution = " ".join(solution.split())
        solution = solution.replace(':','')
        solution = solution.replace('d','')
        
        # solution is now a string like " 00 42 49.4 +41 19 13", we can apply split method to convert to a list and extract ra and dec
        solution = solution.split(' ')

        # start at 1 because for some reason the first item in the list is a space
        ra_img_raw = str(solution[1]) + " " + str(solution[2]) + " " + str(solution[3])
        dec_img_raw = str(solution[4]) + " " + str(solution[5]) + " " + str(solution[6])

        # convert to decimal and keep just two decimals
        ra_img,dec_img = hms_dms_dd(ra_img_raw, dec_img_raw)
        ra_img = "{:.2f}".format(ra_img)
        dec_img = "{:.2f}".format(dec_img)
    
        # update GUI with result
        img_ra_value.config(text=str(ra_img),background=tk_bkgd)
        img_dec_value.config(text=str(dec_img),background=tk_bkgd)
        
        info = (datetime.datetime.now()).strftime("%X") + " => coordinates found"
        done_label.configure(text=str(info))
        done_label.update()
        find_coord_button.configure(text="find coord.")
        find_coord_button.update()
        error_label.config(text="            ")
        error_label.update()
        #print(ra_img,dec_img)
        return ra_img,dec_img
        
    except:
        img_ra_value.config(text=str("not found"),background=tk_bkgd)
        img_dec_value.config(text=str("not found"),background=tk_bkgd) 
        error_label.config(text="could not solve image")
        error_label.update()
        find_coord_button.configure(text="find coord.")
        find_coord_button.update()
    

def solve_single_img():
    """
    in the case of a single image to solve, do this:
    """
    global ra_img
    global dec_img
    print("solving single image")
    get_target_coord()
    ra_img,dec_img = get_image_coord(filename)

def calculate_angle(x,y):
    """
    get angle of rotation between astromical and dobson axis
    source: https://www.geeksforgeeks.org/atan2-function-python/
    """
    # calculate angle of rotation (result in rad): 
    angle_result = atan2(x, y)
    return angle_result
    
def convert_coord(ra,dec,angle_av):
    """
    convert coordinates from astronomical ra/dec to dobson azimut/vertical (az/vc)
    source: https://doubleroot.in/lessons/coordinate-geometry-basics/rotation-of-axes/
    """    
    #calculate references with respect to motor instead of astro (angle in rad)
    az = ra*cos(angle_av) + dec*sin(angle_av)
    vc = dec*cos(angle_av) - ra*sin(angle_av)
    return az,vc
    

def use_set_of_image(move):
    """
    this function is used for testing purposes with a set of image
    in store: M45 done with the same stepper moves as required for calibration
    the function copies the correct image as calibration_image.png
    """
    image_file = "/home/dlg/ekos/M45png/M45-" + str(move) + ".png"
    print("copy ",image_file," as calibration_image.png")
    copyfile(image_file,'/home/dlg/Documents/python/calibration_image.png')

def calibrate():
    """
    move 3 times in each direction, saves image coordinates in two lists for ra and dec
    before each time, triggers motor to ensure there's not backlash
    we keep two decimals using {:.2f} but this produces a str so we convert to float
    """
    global step_az
    global step_vc
    global angle_av
    global ra_img
    global dec_img
    
    # set progress bar at 0
    calibrate_progress['value'] = 0
    
    # check if target was correctly provided. If not return None goes back to main
    ref = reference.get()
    if ref.isdigit():
        error_label.config(text="           ", background=tk_bkgd)  
    else:
        object_ref.delete(0,'end')  
        error_label.config(text="target must be a number", background=tk_bkgd, foreground='#FF0000', font='Helvetica 14 bold') 
        return None
    
    # clear all fields except ra_target and dec_target
    img_az_value.configure(text="     ")
    img_vc_value.configure(text="     ")
    target_az_value.configure(text="     ")
    target_vc_value.configure(text="     ")
    diff_az_value.configure(text="     ")
    diff_vc_value.configure(text="     ")
    diff_ra_value.configure(text="     ")
    diff_dec_value.configure(text="     ")
    stepper_az_value.configure(text="     ")
    stepper_vc_value.configure(text="     ")
    step_az_value.configure(text="     ")
    step_vc_value.configure(text="     ")
    angle_value.configure(text="     ")
    
    done_label.configure(text="                     ")
    done_label.update()
    info = (datetime.datetime.now()).strftime("%X") + " => calibration started"
    doing_label.configure(text=str(info))
    doing_label.update()
    calibrate_button.configure(text="processing...")
    calibrate_button.update()

    error = get_target_coord()
    if ( error == "yes" ):
        doing_label.configure(text="            ")
        calibrate_button.configure(text="calibrate")
        calibrate_button.update()
        return None

    ra_img_list = []
    dec_img_list = []
    ref_img = []            # reference of moves for troubleshooting
    diff_AZ_RA = []         # trigger AZ, difference in RA coordinates
    diff_AZ_DEC = []        # trigger AZ, difference in DEC coordinates
    diff_ALT_RA = []         # trigger ALT, difference in RA coordinates 
    diff_ALT_DEC = []        # trigger ALT, difference in RA coordinates
    filepath = "/home/dlg/Documents/python/calibration_image.png"

    info = (datetime.datetime.now()).strftime("%X") + " => one move A- for backlash"
    done_label.configure(text=str(info))
    done_label.update()
    azimut_moins_3()       # make sure catch up backlash    
    
    for move in range(0,4):
        print("az- ",move)
        azimut_moins_3()
        #testing
        #use_set_of_image(move)
        zwo_image()
        sleep(1)
        ra_img_tmp,dec_img_tmp = get_image_coord(filepath)  
        ref_img.append(" a-  ")
        ra_img_list.append(ra_img_tmp)
        dec_img_list.append(dec_img_tmp)
        if (move != 0):
            diff_temp = float("{:.2f}".format(abs(float(ra_img_list[move]) - float(ra_img_list[move - 1]))))
            diff_AZ_RA.append(diff_temp)
            diff_temp = float("{:.2f}".format(abs(float(dec_img_list[move]) - float(dec_img_list[move - 1]))))
            diff_AZ_DEC.append(diff_temp)
        #print(ra_img,dec_img)   
        calibrate_progress['value'] += 6.66667
        
    info = (datetime.datetime.now()).strftime("%X") + " => one move D- for backlash"
    done_label.configure(text=str(info))
    done_label.update()        
    alt_moins_3()       # make sure catch up backlash             
        
    for move in range(4,8):
        print("d- ",move)
        alt_moins_3()
        #testing
        #use_set_of_image(move)
        zwo_image()
        sleep(1)
        ra_img_tmp,dec_img_tmp = get_image_coord(filepath)  
        ref_img.append(" d-  ")
        ra_img_list.append(ra_img_tmp)
        dec_img_list.append(dec_img_tmp)
        if (move != 4):
            diff_temp = float("{:.2f}".format(abs(float(ra_img_list[move]) - float(ra_img_list[move - 1]))))
            diff_ALT_RA.append(diff_temp)
            diff_temp = float("{:.2f}".format(abs(float(dec_img_list[move]) - float(dec_img_list[move - 1]))))
            diff_ALT_DEC.append(diff_temp)
        #print(ra_img,dec_img)  
        calibrate_progress['value'] += 6.66667      
        
        
    info = (datetime.datetime.now()).strftime("%X") + " => one move D+ for backlash"
    done_label.configure(text=str(info))
    done_label.update()
    sleep(2)
    alt_plus_3()       # make sure catch up backlash       
        
    for move in range(8,12):
        print("d+ ",move)
        alt_plus_3()
        #testing
        #use_set_of_image(move)
        zwo_image()
        sleep(1)
        ra_img_tmp,dec_img_tmp = get_image_coord(filepath)  
        ref_img.append(" d+  ")
        ra_img_list.append(ra_img_tmp)
        dec_img_list.append(dec_img_tmp)
        if (move != 8):
            diff_temp = float("{:.2f}".format(abs(float(ra_img_list[move]) - float(ra_img_list[move - 1]))))
            diff_ALT_RA.append(diff_temp)
            diff_temp = float("{:.2f}".format(abs(float(dec_img_list[move]) - float(dec_img_list[move - 1]))))
            diff_ALT_DEC.append(diff_temp)
        #print(ra_img,dec_img)     
        calibrate_progress['value'] += 6.66667

    info = (datetime.datetime.now()).strftime("%X") + " => one move A- for backlash"
    done_label.configure(text=str(info))
    done_label.update()
    azimut_plus_3()       # make sure catch up backlash            

    for move in range(12,16):
        print("az+ ",move)
        azimut_plus_3()
        #testing
        #use_set_of_image(move)
        zwo_image()
        sleep(1)
        ra_img_tmp,dec_img_tmp = get_image_coord(filepath)  
        ref_img.append(" a+  ")
        ra_img_list.append(ra_img_tmp)
        dec_img_list.append(dec_img_tmp)
        if (move != 12):
            previous = move - 1
            diff_temp = float("{:.2f}".format(abs(float(ra_img_list[move]) - float(ra_img_list[previous]))))
            diff_AZ_RA.append(diff_temp)
            diff_temp = float("{:.2f}".format(abs(float(dec_img_list[move]) - float(dec_img_list[previous]))))
            diff_AZ_DEC.append(diff_temp)
        #print(ra_img,dec_img)
        calibrate_progress['value'] += 6.66667

        
    #print(ref_img) 
    #print(ra_img)
    #print(dec_img)
    #print("diff AZ_RA",diff_AZ_RA)
    #print("diff AZ_DEC",diff_AZ_DEC)
    #print("diff ALT_RA",diff_ALT_RA)
    #print("diff ALT_DEC",diff_ALT_DEC)     
    
    # each of those diffs looks like this   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]    
    # we want an average of the absolute values 
    
    diff_AZ_RA = float("{:.2f}".format(mean(diff_AZ_RA)))
    diff_AZ_DEC = float("{:.2f}".format(mean(diff_AZ_DEC)))
    diff_ALT_RA = float("{:.2f}".format(mean(diff_ALT_RA)))
    diff_ALT_DEC = float("{:.2f}".format(mean(diff_ALT_DEC)))
    
    #print("diff AZ_RA",diff_AZ_RA)
    #print("diff AZ_DEC",diff_AZ_DEC)
    #print("diff ALT_RA",diff_ALT_RA)
    #print("diff ALT_DEC",diff_ALT_DEC)
    
    angle1 = calculate_angle(diff_AZ_RA,diff_AZ_DEC) 
    angle2 = calculate_angle(diff_ALT_RA,diff_ALT_DEC)
    
    angle_av = float("{:.2f}".format((angle1 + angle2) / 2))
    angle_degrees = "{:.1f}".format(degrees(angle_av))
    #print("angle results: ",angle1,angle2,"radians => ",angle_degrees," degrees")
    
    info = " <-- " + angle_degrees + " º -->"
    angle_value.configure(text=str(info))
    angle_value.update()
    
    step_az_tuple = convert_coord(diff_AZ_RA,diff_AZ_DEC,angle_av)
    step_vc_tuple = convert_coord(diff_ALT_RA,diff_ALT_DEC,angle_av)
    
    #print(step_az) 
    #print(step_vc)
    
    # these get returned as tuples (value1,value2) where value1 is the step, value2 is 0
    # second value in tupple is 0 because it's on the axis, we store it in useless variable called zero
    # those values are the az and vc distances in degree when moving +++ or --- (fast) which is 3200 steps
    
    
    (step_az,zero) = step_az_tuple
    (step_vc,zero) = step_vc_tuple
    
    step_az = float("{:.2f}".format(step_az))
    step_vc = float("{:.2f}".format(step_vc))
    
    step_az_value.config(text=str(step_az),background=tk_bkgd)
    step_vc_value.config(text=str(step_vc),background=tk_bkgd)
    
    info = (datetime.datetime.now()).strftime("%X") + " => calibration done"
    done_label.configure(text=str(info))
    done_label.update()
    calibrate_button.configure(text="calibrate")
    calibrate_button.update()
    
    compare_button.configure(state='enabled')
    compare_button.update()

    ############# end calibration
    
    ## no need to take image, coordinates are from latest position
    ra_img = ra_img_list[15]
    dec_img = dec_img_list[15]
    
    ## button so user can also manually clicks on compare ?
    
    

def compare():
    """
    requires as global: ra_target, dec_target, angle_av, ra_img, dec_img
    calculates global stepper_az and stepper_vc used by go_to
    """
    global stepper_az 
    global stepper_vc
    
    print("image coord: ",ra_img, dec_img)
    
    az_target_d,vc_target_d = convert_coord(float(ra_target),float(dec_target),angle_av) 
    az_img_d,vc_img_d = convert_coord(float(ra_img),float(dec_img),angle_av) 
    
    img_az_value.config(text="{:.2f}".format(az_img_d),background=tk_bkgd)
    img_vc_value.config(text="{:.2f}".format(vc_img_d),background=tk_bkgd)
    target_az_value.config(text="{:.2f}".format(az_target_d),background=tk_bkgd)
    target_vc_value.config(text="{:.2f}".format(vc_target_d),background=tk_bkgd)
    
    #print("az_img_d= ",az_img_d, "az_target_d= ",az_target_d)   
    #print("vc_img_d= ",vc_img_d, "vc_target_d= ",vc_target_d)  

    AZ_diff_image_target = float(az_img_d) - float(az_target_d)
    ALT_diff_image_target = float(vc_img_d) - float(vc_target_d)
    
    RA_diff_image_target = float(ra_img) - float(ra_target)
    DEC_diff_image_target = float(dec_img) - float(dec_target)
    

    
    # and this is by how much steppers should move to go to target
    
    stepper_az = int(( AZ_diff_image_target / step_az ) * 3200 * -1)
    stepper_vc = int(( ALT_diff_image_target / step_vc ) * 3200 * -1)
    
    diff_az_value.config(text="{:.2f}".format(AZ_diff_image_target),background=tk_bkgd)
    diff_vc_value.config(text="{:.2f}".format(ALT_diff_image_target),background=tk_bkgd)
    diff_ra_value.config(text="{:.2f}".format(RA_diff_image_target),background=tk_bkgd)
    diff_dec_value.config(text="{:.2f}".format(DEC_diff_image_target),background=tk_bkgd)

    stepper_az_value.config(text=str(stepper_az),background=tk_bkgd)
    stepper_vc_value.config(text=str(stepper_vc),background=tk_bkgd)
    
    goto_button.configure(state='enabled')
    goto_button.update()
    
    
def go_to():
    """
    send stepper_az and stepper_vc to arduino
    set ram_img and dec_img as global so that compare can use these updated variables
    at the end of goto, it takes a new image and solves it, then calls compare 
    """
    global ra_img
    global dec_img
    
    info = (datetime.datetime.now()).strftime("%X") + " => goto requested"
    doing_label.configure(text=str(info))
    doing_label.update()
    
    goto_button.configure(text="processing...")
    goto_button.update()
    
    info = "           "
    done_label.configure(text=str(info))
    done_label.update()
    print("goto: ",stepper_az,stepper_vc)
    if (stepper_az < 0):
        print("az < 0")
        ser.write(bytes('P','UTF-8'))
        sleep(0.1) 
        ser.write(bytes(str(abs(stepper_az)),'UTF-8'))
        sleep(1.3) 
        #ser.write(bytes('M','UTF-8'))
        
        wait_for_arduino() # confirms stepper start moving
        wait_for_arduino() # confirms stepper finished
        
    if (stepper_az > 0):
        print("az > 0")
        ser.write(bytes('O','UTF-8'))
        sleep(0.1) 
        ser.write(bytes(str(abs(stepper_az)),'UTF-8'))
        sleep(1.3) 
        #ser.write(bytes('M','UTF-8'))
        
        wait_for_arduino() # confirms stepper start moving
        wait_for_arduino() # confirms stepper finished    
    
    if (stepper_vc < 0):
        print("vc < 0")
        ser.write(bytes('L','UTF-8'))
        sleep(0.1) 
        ser.write(bytes(str(abs(stepper_vc)),'UTF-8'))
        sleep(1.3) 
        #ser.write(bytes('M','UTF-8'))
        
        wait_for_arduino() # confirms stepper start moving
        wait_for_arduino() # confirms stepper finished  
        
    if (stepper_vc > 0):
        print("vc > 0")
        ser.write(bytes('K','UTF-8'))
        sleep(0.1) 
        ser.write(bytes(str(abs(stepper_vc)),'UTF-8'))
        sleep(1.3) 
        #ser.write(bytes('M','UTF-8'))
        
        wait_for_arduino() # confirms stepper start moving
        wait_for_arduino() # confirms stepper finished          

        
    zwo_image()
    #filename = "/home/dlg/ekos/M45png/M45-30.png"
    ra_img,dec_img = get_image_coord(filename)
    compare()    
        
    goto_button.configure(text="go to target")
    goto_button.update()    
        
    info = (datetime.datetime.now()).strftime("%X") + " => goto finished, check results"
    done_label.configure(text=str(info))
    done_label.update()
    
    
        
    ## take new image, solve it and update diff and steps
        
    
######################
######  main  ########
######################


# variables
catalog = tk.StringVar()
reference = tk.StringVar()
filename = tk.StringVar()

root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)
root.columnconfigure(3, weight=1)

# frame target
frame_target = ttk.LabelFrame(root,width=360, height=20, borderwidth=0, relief="flat")
frame_target.grid(column=0, row=0, padx=20, pady=15, columnspan=4)

frame_target.columnconfigure(0, weight=1)
frame_target.columnconfigure(1, weight=1)
frame_target.columnconfigure(2, weight=1)
frame_target.columnconfigure(3, weight=1)

target_label = ttk.Label(frame_target, text="TARGET =>",anchor="w",width=18)
target_label.grid(column=0, row=1, sticky=tk.W, padx=5, pady=15)
target_label.configure(background=tk_bkgd)

messier_radio_button = ttk.Radiobutton(frame_target, text="Messier", value="M", variable=catalog, width=12)
messier_radio_button.grid(column=1, row=1, sticky=tk.E, padx=5, pady=5, ipadx=5,ipady=5)
messier_radio_button.invoke()

ngc_radio_button = ttk.Radiobutton(frame_target, text="NGC",value="NGC", variable=catalog, width=10)
ngc_radio_button.grid(column=2, row=1, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)

object_ref = ttk.Entry(frame_target,textvariable=reference,width=10)
object_ref.grid(column=3, row=1, sticky=tk.W, padx=5, pady=5, ipadx=5,ipady=5)


# frame single image
frame_single_image = ttk.LabelFrame(root,width=360, height=200, borderwidth=1, relief="groove", labelanchor='n', text=" SINGLE IMAGE ")
frame_single_image.grid(column=0, row=4, padx=20, pady=15, columnspan=4)

image_name = ttk.Entry(frame_single_image,textvariable=filename,width=20)
image_name.grid(column=0, row=0,  columnspan=3, sticky=tk.E, padx=5, pady=5, ipadx=5,ipady=5)

browse_image_button = ttk.Button(frame_single_image, text="select", command=browse_image)
browse_image_button.grid(column=3, row=0, sticky=tk.N, padx=5, pady=5, ipadx=5,ipady=5)

take_image_button = ttk.Button(frame_single_image, text="take image", command=zwo_image, width=14)
take_image_button.grid(column=0, row=1, columnspan=2, sticky=tk.N, padx=5, pady=15, ipadx=5,ipady=5)

find_coord_button = ttk.Button(frame_single_image, text="find coord.", command=solve_single_img, width=14)
find_coord_button.grid(column=2, row=1, columnspan=2, sticky=tk.N, padx=5, pady=15, ipadx=5,ipady=5)
find_coord_button.configure(state='disabled')


# frame calibrate, compare and goto
frame_goto = ttk.LabelFrame(root,width=360, height=300, borderwidth=1, relief="groove", labelanchor='n', text=" GO TO ")
frame_goto.grid(column=0, row=5, padx=20, pady=15, columnspan=4)

calibrate_button = ttk.Button(frame_goto, text="calibrate", command=calibrate, width=14)
calibrate_button.grid(column=0, row=0, columnspan=2, sticky=tk.E, padx=5, pady=10, ipadx=5,ipady=5)

compare_button = ttk.Button(frame_goto, text="compare", command=compare, width=14)
compare_button.grid(column=2, row=0, columnspan=2, sticky=tk.E, padx=5, pady=10, ipadx=5,ipady=5)
compare_button.configure(state='disabled')

goto_button = ttk.Button(frame_goto, text="go to target", command=go_to, width=14)
goto_button.grid(column=2, row=1, columnspan=2, sticky=tk.E, padx=5, pady=10, ipadx=5,ipady=5)
goto_button.configure(state='disabled')

calibrate_progress = ttk.Progressbar(frame_goto,orient='horizontal',mode='determinate',length=130)
calibrate_progress.grid(column=0, row=1, columnspan=2, padx=5, pady=10)


# frame results
frame_results = ttk.LabelFrame(root,width=360, height=250, borderwidth=1, relief="groove", labelanchor='n', text=" RESULTS ")
frame_results.grid(column=0, row=6, padx=20, pady=15, columnspan=4)
frame_results.grid_propagate(0) # forces width, which is ignored otherwise

frame_results.columnconfigure(0, weight=1)
frame_results.columnconfigure(1, weight=1)
frame_results.columnconfigure(2, weight=1)
frame_results.columnconfigure(3, weight=1)
frame_results.columnconfigure(4, weight=1)

empty_label = ttk.Label(frame_results, text=" ", anchor="e")   # one line spacing
empty_label.grid(column=0, row=0, columnspan=3, sticky=tk.E, padx=0, pady=0)

nothing_label = ttk.Label(frame_results, text="   ",anchor="e")
nothing_label.grid(column=0, row=1, sticky=tk.E, padx=5, pady=5)
nothing_label.configure(background=tk_bkgd)

ra_label = ttk.Label(frame_results, text="ra: ",anchor="e")
ra_label.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)
ra_label.configure(background=tk_bkgd)

dec_label = ttk.Label(frame_results, text="dec: ",anchor="e")
dec_label.grid(column=2, row=1, sticky=tk.W, padx=5, pady=5)
dec_label.configure(background=tk_bkgd)

az_label = ttk.Label(frame_results, text="az: ",anchor="e")
az_label.grid(column=3, row=1, sticky=tk.W, padx=5, pady=5)
az_label.configure(background=tk_bkgd)

vc_label = ttk.Label(frame_results, text="vc: ",anchor="e")
vc_label.grid(column=4, row=1, sticky=tk.W, padx=5, pady=5)
vc_label.configure(background=tk_bkgd)

target_label = ttk.Label(frame_results, text="target: ",anchor="e")
target_label.grid(column=0, row=2, sticky=tk.E, padx=5, pady=5)
target_label.configure(background=tk_bkgd)

target_ra_value = ttk.Label(frame_results, text="", anchor="w")
target_ra_value.grid(column=1, row=2, sticky=tk.W, padx=5, pady=5)
target_ra_value.config(foreground='#330a99')

target_dec_value = ttk.Label(frame_results, text="", anchor="w")
target_dec_value.grid(column=2, row=2, sticky=tk.W, padx=5, pady=5)
target_dec_value.config(foreground='#330a99')

target_az_value = ttk.Label(frame_results, text="", anchor="w")
target_az_value.grid(column=3, row=2, sticky=tk.W, padx=5, pady=5)
target_az_value.config(foreground='#330a99')

target_vc_value = ttk.Label(frame_results, text="", anchor="w")
target_vc_value.grid(column=4, row=2, sticky=tk.W, padx=5, pady=5)
target_vc_value.config(foreground='#330a99')

img_label = ttk.Label(frame_results, text="image: ",anchor="e")
img_label.grid(column=0, row=3, sticky=tk.E, padx=5, pady=5)
img_label.configure(background=tk_bkgd)

img_ra_value = ttk.Label(frame_results, text="", anchor="w")
img_ra_value.grid(column=1, row=3, sticky=tk.W, padx=5, pady=5)
img_ra_value.config(foreground='#330a99')

img_dec_value = ttk.Label(frame_results, text="", anchor="w")
img_dec_value.grid(column=2, row=3, sticky=tk.W, padx=5, pady=5)
img_dec_value.config(foreground='#330a99')

img_az_value = ttk.Label(frame_results, text="", anchor="w")
img_az_value.grid(column=3, row=3, sticky=tk.W, padx=5, pady=5)
img_az_value.config(foreground='#330a99')

img_vc_value = ttk.Label(frame_results, text="", anchor="w")
img_vc_value.grid(column=4, row=3, sticky=tk.W, padx=5, pady=5)
img_vc_value.config(foreground='#330a99')

diff_label = ttk.Label(frame_results, text="diff: ",anchor="e")
diff_label.grid(column=0, row=4, sticky=tk.E, padx=5, pady=5)
diff_label.configure(background=tk_bkgd)

diff_ra_value = ttk.Label(frame_results, text="", anchor="w")
diff_ra_value.grid(column=1, row=4, sticky=tk.W, padx=5, pady=5)
diff_ra_value.config(foreground='#330a99')

diff_dec_value = ttk.Label(frame_results, text="", anchor="w")
diff_dec_value.grid(column=2, row=4, sticky=tk.W, padx=5, pady=5)
diff_dec_value.config(foreground='#330a99')

diff_az_value = ttk.Label(frame_results, text="", anchor="w")
diff_az_value.grid(column=3, row=4, sticky=tk.W, padx=5, pady=5)
diff_az_value.config(foreground='#330a99')

diff_vc_value = ttk.Label(frame_results, text="", anchor="w")
diff_vc_value.grid(column=4, row=4, sticky=tk.W, padx=5, pady=5)
diff_vc_value.config(foreground='#330a99')


angle_label = ttk.Label(frame_results, text="angle: ",anchor="e")
angle_label.grid(column=0, row=5, sticky=tk.E, padx=5, pady=5)
angle_label.configure(background=tk_bkgd)

angle_value = ttk.Label(frame_results, text="    ", anchor="n")
angle_value.grid(column=1, row=5, sticky=tk.N, padx=5, pady=5, columnspan=4)
angle_value.config(foreground='#330a99')

step_label = ttk.Label(frame_results, text="fast: ",anchor="e")
step_label.grid(column=0, row=6, sticky=tk.E, padx=5, pady=5)
step_label.configure(background=tk_bkgd)

step_az_value = ttk.Label(frame_results, text="    ", anchor="w")
step_az_value.grid(column=3, row=6, sticky=tk.W, padx=5, pady=5)
step_az_value.config(foreground='#330a99')

step_vc_value = ttk.Label(frame_results, text="    ", anchor="w")
step_vc_value.grid(column=4, row=6, sticky=tk.W, padx=5, pady=5)
step_vc_value.config(foreground='#330a99')

stepper_label = ttk.Label(frame_results, text="steps ",anchor="e")
stepper_label.grid(column=0, row=7, sticky=tk.E, padx=5, pady=5)
stepper_label.configure(background=tk_bkgd)

stepper_az_value = ttk.Label(frame_results, text="    ", anchor="w")
stepper_az_value.grid(column=3, row=7, sticky=tk.W, padx=5, pady=5)
stepper_az_value.config(foreground='#330a99')

stepper_vc_value = ttk.Label(frame_results, text="    ", anchor="w")
stepper_vc_value.grid(column=4, row=7, sticky=tk.W, padx=5, pady=5)
stepper_vc_value.config(foreground='#330a99')




doing_label = ttk.Label(root, text="                  ", anchor="e")
doing_label.grid(column=0, row=11, columnspan=4, sticky=tk.W, padx=15, pady=2, ipadx=15,ipady=2)
doing_label.configure(background=tk_bkgd) #, foreground='#d67200')

done_label = ttk.Label(root, text="                  ", anchor="e")
done_label.grid(column=0, row=12, columnspan=4, sticky=tk.W, padx=15, pady=2, ipadx=15,ipady=2)
done_label.configure(background=tk_bkgd) #, foreground='#31c908')

error_label = ttk.Label(root, text="                  ", anchor="e")
error_label.grid(column=0, row=13, columnspan=4, sticky=tk.N, padx=5, pady=2, ipadx=5,ipady=2)
error_label.configure(background=tk_bkgd, foreground='#FF0000')

hw_check = ttk.Button(root,text="HW check",command=hw_check)
hw_check.grid(column=0, row=14, columnspan=2, sticky=tk.N, padx=5, pady=5, ipadx=5,ipady=10)

quit_button = ttk.Button(root, text="QUIT",command=exit)
quit_button.grid(column=2, row=14, columnspan=2, sticky=tk.N, padx=15, pady=5, ipadx=5,ipady=10)

# check if ZWO camera is connected and if not disable buttons
cam_specs = subprocess.check_output(f"zwo-asi-print")
if not cam_specs:
    error_label.config(text="camera not connected", background=tk_bkgd, foreground='#FF0000', font='Helvetica 14 bold')
    take_image_button.configure(state='disabled')
    calibrate_button.configure(state='disabled')
    goto_button.configure(state='disabled')
    
# check if arduino is connected    
arduino_is_here = subprocess.getoutput('ls /dev/ttyACM0')  #not very pythonian but path is_file returned false
if arduino_is_here == "/dev/ttyACM0":
    # initialise serial connection (device, baud rate)
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=.5)
    # clear the serial line (optional)
    ser.flushInput()
    #done_label.config(text="arduino is connected")
else:
    error_label.config(text="arduino not connected", background=tk_bkgd, foreground='#FF0000', font='Helvetica 14 bold')    

"""
1 coup de moteur AZ+++ pour rattraper le jeu
initialise diff_AZp_RA and diff_AZp_DEC at 0
take image, solve, get coordinates as RA_start and DEC_start
start loop 3x
1 coup de moteurs AZ+++ 
take image, solve, get coordinates, save diff as diff_AZp_RA and diff_AZp_DEC
1 coup de moteurs AZ+++ 
take image, solve, get coordinates, add diff to diff_AZp_RA and diff_AZp_DEC
1 coup de moteurs AZ+++ 
take image, solve, get coordinates, add diff to diff_AZp_RA and diff_AZp_DEC
average of diff_AZp_RA and diff_AZp_DEC

1 coup de moteur AZ--- pour rattraper le jeu
initialise diff_AZn_RA and diff_AZn_DEC at 0
take image, solve, get coordinates as RA_start and DEC_start
start loop 3x
1 coup de moteurs AZ--- 
take image, solve, get coordinates, save diff as diff_AZn_RA and diff_AZn_DEC
1 coup de moteurs AZ--- 
take image, solve, get coordinates, add diff to diff_AZn_RA and diff_AZn_DEC
1 coup de moteurs AZ--- 
take image, solve, get coordinates, add diff to diff_AZn_RA and diff_AZn_DEC
average of diff_AZn_RA and diff_AZn_DEC

1 coup de moteur ALT+++ pour rattraper le jeu
initialise diff_ALTp_RA and diff_ALTp_DEC at 0
take image, solve, get coordinates as RA_start and DEC_start
start loop 3x
1 coup de moteurs ALT+++  
take image, solve, get coordinates, save diff as diff_ALTp_RA and diff_ALTp_DEC at 0
1 coup de moteurs ALT+++  
take image, solve, get coordinates, add diff to diff_ALTp_RA and diff_ALTp_DEC at 0
1 coup de moteurs ALT+++ 
take image, solve, get coordinates, add diff to diff_ALTp_RA and diff_ALTp_DEC at 0
average of diff_ALTp_RA and average of diff_ALTp_DEC

1 coup de moteur ALT--- pour rattraper le jeu
initialise diff_ALTn_RA and diff_ALTp_DEC at 0
take image, solve, get coordinates as RA_start and DEC_start
start loop 3x
1 coup de moteurs ALT---  
take image, solve, get coordinates, save diff as diff_ALTn_RA and diff_ALTn_DEC at 0
1 coup de moteurs ALT---  
take image, solve, get coordinates, add diff to diff_ALTn_RA and diff_ALTn_DEC at 0
1 coup de moteurs ALT--- 
take image, solve, get coordinates, add diff to diff_ALTn_RA and diff_ALTn_DEC at 0
average of diff_ALTn_RA and average of diff_ALTn_DEC
"""

root.mainloop()

### next: send number of steps to arduino


########### improvements #######

# validate data fields
# display graph of coordinates img vs target
# validate results of calculations (eg angle, diffs, using stats deviation)
