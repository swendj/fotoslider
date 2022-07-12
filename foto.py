#!/usr/bin/env python -*- coding: utf-8 -*-

#*****************************************************************************
#
# This is the "foto slider" script for our motor driven camera slider.
#
# Module        : main module, foto.py
# Author        : Swen Hopfe (dj)
# Design        : 2019-12-17
# Last modified : 2020-01-10
#
# The python script works on Raspberry Pi 2/3/4/B/+
# with TFT display and keyboard and was tested on a Pi 3B .
#
#*****************************************************************************

from __future__ import print_function

import time
import sys
import os
import subprocess
import signal
import RPi.GPIO as GPIO
import smbus
import logging
import gphoto2 as gp
import datetime
from random import randint

#-----------------------------------------------------------------------------
# Aktuelle Hardware-Konfiguration

# Motor MX (mot=0) - 1/8 -Step
# Motor MY (mot=1) - 1/16-Step
# Motor MZ (mot=2) - 1/2 -Step
# Motor MA (mot=3) - 1/1 -Step

#i2c bus address

I2C_ADDR = 0x20

# pin defs for x,y,z steppers
# control pins
# gpio bcm numbers 5,6,12,13 means board pins 29,31,32,33 (violett,grau,braun,schwarz)
# direction pins
# gpio bcm numbers 16,26,20,21 means board pins 36,37,38,40 (gruen,orange,gelb,weiss)
# ENABLE is pin 19 (rot)
# GND is pin 30 (blau)

xa = 5
ya = 6
za = 12
aa = 13
xd = 16
yd = 26
zd = 20
ad = 21
en = 19

#-----------------------------------------------------------------------------
# graphical interface or terminal mode

ge = True
if os.environ.get('DISPLAY','') == '':
    ge = False
else:
    from Tkinter import *

#-----------------------------------------------------------------------------
# global picture counter
pc = 0
# global (random) picture directory
sr = "00000000"
# camera enable flag
cfl = False

#-----------------------------------------------------------------------------
# the stepper routine
# stepper(mot,dir,numsteps,force)
# motors (mot) 0:x 1:y 2:z 3:a , directions (dir) 0:left 1:right
# numsteps - number of steps
# speed - 1-voll 2-halb 3-drittel etc.
# force = 0/1 - do/not look at right stop contact

def stepper(mot, dir, numsteps, speed, force):
    global xa, ya, za, aa, xd, yd, zd, ad, en

    if mot == 0:
        #print "Fahre X-Motor."
        cpin = xa
    elif mot == 1:
        #print "Fahre Y-Motor."
        cpin = ya
    elif mot == 2:
        #print "Fahre Z-Motor."
        cpin = za
    elif mot == 3:
        #print "Fahre A-Motor."
        cpin = aa

    if cpin == xa:
        if dir == 0:
            #print "X-Richtung Links."
            GPIO.output(xd, False)
        elif dir == 1:
            #print "X-Richtung Rechts."
            GPIO.output(xd, True)
    elif cpin == ya:
        if dir == 0:
            #print "Y-Richtung Links."
            GPIO.output(yd, False)
        elif dir == 1:
            #print "Y-Richtung Rechts."
            GPIO.output(yd, True)
    elif cpin == za:
        if dir == 0:
            #print "Z-Richtung Rechts."
            GPIO.output(zd, False)
        elif dir == 1:
            #print "Z-Richtung Links."
            GPIO.output(zd, True)
    elif cpin == aa:
        if dir == 0:
            #print "A-Richtung Links."
            GPIO.output(ad, False)
        elif dir == 1:
            #print "A-Richtung Rechts."
            GPIO.output(ad, True)

    GPIO.output(en, False)

    for i in range(numsteps):

      if force == 0:
        pins = i2c.read_byte(I2C_ADDR)
        if (pins & 0x04)/4 == 0 :
            GPIO.output(cpin, True)
            time.sleep(0.0004)
            time.sleep(0.0001*speed)
            GPIO.output(cpin, False)
            time.sleep(0.0001*speed)

      if force == 1:
            GPIO.output(cpin, True)
            time.sleep(0.0001*speed)
            GPIO.output(cpin, False)
            time.sleep(0.0001*speed)

    GPIO.output(en, True)

#-----------------------------------------------------------------------------
# the stepper2 routine, control two motors same time
# stepper2(mot1,dir1,numsteps1,mot2,dir2,numsteps2,speed)
# motors (mot) 0:x 1:y 2:z 3:a , directions (dir) 0:left 1:right
# numsteps - number of steps
# speed - 1-voll 2-halb 3-drittel etc.

# Es wird das Verhaeltnis numsteps1 / numsteps2 berechnet
# mot2 wird nur soviel gesteppt, dass auf den Fahrweg mot1 genau der Fahrweg mot2 gemacht wird
# numsteps2 muss dabei kleiner oder gleich numsteps1 sein 
# mot1 == mot2 ist verboten

def stepper2(mot1, dir1, numsteps1, mot2, dir2, numsteps2, speed):
  global xa, ya, za, aa, xd, yd, zd, ad, en

  if mot1 == mot2:
    print("Verbotene Motor-Angabe (Beide Motoren gleich).")
  else:
   if numsteps2 > numsteps1:
     print("Verbotene Stepper-Angabe (numsteps2 darf keinen groesseren Wert als numsteps1 haben).")
   else:

    if mot1 == 0:
        #print "Fahre X-Motor."
        cpin1 = xa
    elif mot1 == 1:
        #print "Fahre Y-Motor."
        cpin1 = ya
    elif mot1 == 2:
        #print "Fahre Z-Motor."
        cpin1 = za
    elif mot1 == 3:
        #print "Fahre A-Motor."
        cpin1 = aa

    if mot2 == 0:
        #print "Fahre X-Motor."
        cpin2 = xa
    elif mot2 == 1:
        #print "Fahre Y-Motor."
        cpin2 = ya
    elif mot2 == 2:
        #print "Fahre Z-Motor."
        cpin2 = za
    elif mot2 == 3:
        #print "Fahre A-Motor."
        cpin2 = aa

    if cpin1 == xa:
        if dir1 == 0:
            #print "X-Richtung Links."
            GPIO.output(xd, False)
        elif dir1 == 1:
            #print "X-Richtung Rechts."
            GPIO.output(xd, True)
    elif cpin1 == ya:
        if dir1 == 0:
            #print "Y-Richtung Links."
            GPIO.output(yd, False)
        elif dir1 == 1:
            #print "Y-Richtung Rechts."
            GPIO.output(yd, True)
    elif cpin1 == za:
        if dir1 == 0:
            #print "Z-Richtung Rechts."
            GPIO.output(zd, False)
        elif dir1 == 1:
            #print "Z-Richtung Links."
            GPIO.output(zd, True)
    elif cpin1 == aa:
        if dir1 == 0:
            #print "A-Richtung Links."
            GPIO.output(ad, False)
        elif dir1 == 1:
            #print "A-Richtung Rechts."
            GPIO.output(ad, True)

    if cpin2 == xa:
        if dir2 == 0:
            #print "X-Richtung Links."
            GPIO.output(xd, False)
        elif dir2 == 1:
            #print "X-Richtung Rechts."
            GPIO.output(xd, True)
    elif cpin2 == ya:
        if dir2 == 0:
            #print "Y-Richtung Links."
            GPIO.output(yd, False)
        elif dir2 == 1:
            #print "Y-Richtung Rechts."
            GPIO.output(yd, True)
    elif cpin2 == za:
        if dir2 == 0:
            #print "Z-Richtung Rechts."
            GPIO.output(zd, False)
        elif dir2 == 1:
            #print "Z-Richtung Links."
            GPIO.output(zd, True)
    elif cpin2 == aa:
        if dir2 == 0:
            #print "A-Richtung Links."
            GPIO.output(ad, False)
        elif dir2 == 1:
            #print "A-Richtung Rechts."
            GPIO.output(ad, True)

    GPIO.output(en, False)

    dsteps = numsteps1 / numsteps2
    dstepc = 1

    for i in range(numsteps1):

        pins = i2c.read_byte(I2C_ADDR)
        if (pins & 0x04)/4 == 0 :

            dstepc = dstepc + 1
            GPIO.output(cpin1, True)
            if dstepc > dsteps :
                GPIO.output(cpin2, True)
            time.sleep(0.0004)
            time.sleep(0.0001*speed)
            GPIO.output(cpin1, False)
            if dstepc > dsteps :
                GPIO.output(cpin2, False)
                dstepc = 1
            time.sleep(0.0001*speed)

    GPIO.output(en, True)

#-----------------------------------------------------------------------------
# reboot

def press_r(event):
    clicked1()

def clicked1():
    print("Reboot...")
    print("----------------------------------------------------------")
    global ge
    if(ge):
       txt.insert(END,"Reboot...\n")
       txt.see(END)
       frm.update()
    countr(5)

def countr(count):
    global ge
    if(ge):
       if count > 0:
           btn1["text"] = count
           frm.after(1000, countr, count -1)
       elif count == 0:
           GPIO.cleanup()
           subprocess.call(["sudo","reboot"])
    else:
       time.sleep(count)
       GPIO.cleanup()
       subprocess.call(["sudo","reboot"])

#-----------------------------------------------------------------------------
# shutdown

def press_s(event):
    clicked2()

def clicked2():
    print("Fahre Fotoslider herunter...")
    print("----------------------------------------------------------")
    global ge
    if(ge):
       txt.insert(END,"Fahre Fotoslider herunter...\n")
       txt.see(END)
       frm.update()
    counts(5)

def counts(count):
    global ge
    if(ge):
       if count > 0:
           btn2["text"] = count
           frm.after(1000, counts, count -1)
       elif count == 0:
           GPIO.cleanup()
           subprocess.call(["sudo","shutdown","now"])
    else:
       time.sleep(count)
       GPIO.cleanup()
       subprocess.call(["sudo","shutdown","now"])

#-----------------------------------------------------------------------------
# close program

def press_x(event):
    clicked3()

def clicked3():
    print("Beende Programm...")
    print("----------------------------------------------------------")
    global ge
    if(ge):
       txt.insert(END,"Beende Programm...\n")
       txt.see(END)
       frm.update()
    countb(5)

def countb(count):
    global ge
    if(ge):
       if count > 0:
           btn3["text"] = count
           frm.after(1000, countb, count -1)
       elif count == 0:
           GPIO.cleanup()
           subprocess.call(["sudo","killall","python"])
    else:
       #time.sleep(count)
       GPIO.cleanup()
       subprocess.call(["sudo","killall","python"])

#-----------------------------------------------------------------------------
# stepper test

def press_t(event):
    clicked4()

def clicked4():
    global ge
    print("Stepper-Test...")
    if(ge):
       txt.insert(END,"Stepper-Test...\n")
       txt.see(END)
       frm.update()

    # Motortest - eine Umdrehung aller Motoren

    # stepper(mot,dir,steps)
    # mot: 0:x 1:y 2:z , dir 0:left 1:right
    # 200 fullsteps (1.8 deg) full rotation
    # is equal to  400 1/2 step
    # is equal to 1600 1/8 step
    # is equal to 3200 1/16 step

    clupd("st", "st")

    #MX
    time.sleep(10)
    stepper(0, 0, 1600, 1, 0)  #mx rechts schiebend, links drehend
    time.sleep(2)
    stepper(0, 1, 1600, 1, 0)  #mx links schiebend, rechts drehend
    #MY
    time.sleep(2)
    stepper(1, 0, 3200, 1, 0)  #my links drehend
    time.sleep(2)
    stepper(1, 1, 3200, 1, 0)  #my rechts drehend
    #MZ
    time.sleep(2)
    stepper(2, 0, 400, 1, 0)   #mz rechts drehend (Richtung zum Rest invertiert)
    time.sleep(2)
    stepper(2, 1, 400, 1, 0)   #mz linkss drehend (Richtung zum Rest invertiert)
    #MA
    time.sleep(2)
    stepper(3, 0, 200, 1, 0)   #ma links drehend
    time.sleep(2)
    stepper(3, 1, 200, 1, 0)   #ma rechtss drehend

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)

#-----------------------------------------------------------------------------
# input test

def press_i(event):
    clicked14()

def clicked14():
    global ge
    print("Input-Test...")
    if(ge):
       txt.insert(END,"Input-Test...\n")
       txt.see(END)
       frm.update()

    clupd("it", "it")

    # Test der Eingaenge und Ausgaenge des I2C-Expanders
    pins = i2c.read_byte(I2C_ADDR)
    print("%02x" % pins)
    print("Eingaenge P0-P3:")
    print((pins & 0x01), ((pins & 0x02)/2), ((pins & 0x04)/4), ((pins & 0x08)/8))
    print("Ausgaenge P4-P7:")
    print(((pins & 0x10)/16), ((pins & 0x20)/32), ((pins & 0x40)/64), ((pins & 0x80)/128))

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Nullung

def press_n(event):
    clicked11()

def clicked11():
    global ge
    print("Nullung...")
    if(ge):
       txt.insert(END,"Nullung...\n")
       txt.see(END)
       frm.update()

    clupd("n", "n")

    time.sleep(2)
    clupd(">", ">")
    stepper(0, 0, 27000, 1, 0)  #Nullung
    clupd("<", "<")
    time.sleep(2)

    stepper(0, 1, 400, 1, 1)  #Ausgangsposition
    clupd("0", "0")

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Volle Fahrt nach links ohne Nullung

def press_a(event):
    clicked5()

def clicked5():
    global ge
    print("Fahrt nach links ohne Nullung...")
    if(ge):
       txt.insert(END,"Fahrt nach links ohne Nullung...\n")
       txt.see(END)
       frm.update()

    clupd("<!", "<!")
    time.sleep(2)
    #MX
    #Es werden 24600 Achtelschritte benoetigt
    stepper(0, 1, 24600, 1, 0)  #mx (mot=0) links schiebend, links drehend (dir=1)
    clupd(".", ".")

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Volle Fahrt nach links mit Nullung

def press_1(event):
    clicked12()

def clicked12():
    global ge
    print("Fahrt nach links mit Nullung...")
    if(ge):
       txt.insert(END,"Fahrt nach links mit Nullung...\n")
       txt.see(END)
       frm.update()

    time.sleep(2)
    clupd(">", ">")
    stepper(0, 0, 27000, 1, 0)  #Nullung
    clupd("<", "<")
    time.sleep(2)
    stepper(0, 1, 400, 1, 1)  #mx links schiebend bis rechte Ausgangs/Null-Position, Endstop ignorieren
    clupd("0", "0")
    time.sleep(5)
    clupd("<<", "<<")
    stepper(0, 1, 24600, 1, 0)  #mx links schiebend wie gewuenscht
    clupd(".", ".")

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Volle Fahrt nach rechts ohne Nullung

def press_b(event):
    clicked6()

def clicked6():
    global ge
    print("Fahrt nach rechts ohne Nullung...")
    if(ge):
       txt.insert(END,"Fahrt nach rechts ohne Nullung...\n")
       txt.see(END)
       frm.update()

    #MX
    #Es werden 24600 Achtelschritte benoetigt
    clupd("!>", "!>")
    time.sleep(2)
    stepper(0, 0, 24600, 1, 0)  #mx (mot=0) rechts schiebend, rechts drehend (dir=0)
    clupd(".", ".")

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Volle Fahrt nach rechts mit Nullung

def press_2(event):
    clicked13()

def clicked13():
    global ge
    print("Fahrt nach rechts mit Nullung...")
    if(ge):
       txt.insert(END,"Fahrt nach rechts mit Nullung...\n")
       txt.see(END)
       frm.update()

    time.sleep(2)
    clupd(">", ">")
    stepper(0, 0, 27000, 1, 0)  #Nullung
    clupd("<", "<")
    time.sleep(2)
    stepper(0, 1, 400, 1, 1)  #mx links schiebend bis rechte Ausgangs/Null-Position, Endstop ignorieren
    clupd("0", "0")
    time.sleep(2)
    clupd("<<", "<<")
    stepper(0, 1, 24600, 1, 0)  #mx nach links schieben bis auf linke Ausgangsposition
    time.sleep(5)
    clupd(">>", ">>")
    stepper(0, 0, 24600, 1, 0)  #mx nach rechts schieben wie gewuenscht
    clupd(".", ".")

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Linksschwenk 180 Grad

def press_3(event):
    clicked7()

def clicked7():
    global ge
    print("Linksschwenk 180 Grad...")
    if(ge):
       txt.insert(END,"Linksschwenk 180 Grad...\n")
       txt.see(END)
       frm.update()

    clupd("o", "o")
    time.sleep(2)
    #MY
    #Es werden 1600 1/16-Schritte benoetigt
    stepper(1, 1, 1600, 4, 0)  #my (mot=1) links drehend (dir=1)

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Rechtsschwenk 180 Grad

def press_4(event):
    clicked8()

def clicked8():
    global ge
    print("Rechtsschwenk 180 Grad...")
    if(ge):
       txt.insert(END,"Rechtsschwenk 180 Grad...\n")
       txt.see(END)
       frm.update()

    clupd("o", "o")
    time.sleep(2)
    #MY
    #Es werden 1600 1/16-schritte benoetigt
    stepper(1, 0, 1600, 4, 0)  #my (mot=1) rechtss drehend (dir=0)

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Programm 5

# Movie-Programm keine Shots

def press_5(event):
    clicked9()

def clicked9():
    global ge
    print("Programm 5...")
    if(ge):
       txt.insert(END,"Programm 5...\n")
       txt.see(END)
       frm.update()

    time.sleep(2)
    clupd(">", ">")
    stepper(0, 0, 27000, 1, 0)  #Nullung
    clupd("<", "<")
    time.sleep(2)
    stepper(0, 1, 400, 1, 1)  #Ausgangsposition
    clupd("0", "0")
    time.sleep(5)
    clupd("<o", "<o")
    #MX Fahrt nach links = (0,1)
    #MY Es werden 1600 1/16-Schritte fuer 180 Grad benoetigt, 800 fuer 90 Grad
    stepper2(0, 1, 24600,  1, 1, 800,  1) #my (mot=1) links drehend (dir=1)
    #12300, 600 halbe Schiene Fahrt nach linkss, 90 Grad Drehung nach links
    clupd("1", "618")

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Programm 6

# Movie-Programm keine Shots

def press_6(event):
    clicked10()

def clicked10():
    global ge
    print("Programm 6...")
    if(ge):
       txt.insert(END,"Programm 6...\n")
       txt.see(END)
       frm.update()

    time.sleep(2)
    clupd(">", ">")
    stepper(0, 0, 27000, 1, 0)  #Nullung
    clupd("<", "<")
    time.sleep(2)
    stepper(0, 1, 400, 1, 1)  #Ausgangsposition
    clupd("0", "0")
    time.sleep(2)
    clupd("<<", "<<")
    stepper(0, 1, 24600, 1, 0)  #nach links durchfahren
    clupd("1", "618")
    time.sleep(5)
    clupd("o>", "o>")
    #MX Fahrt nach rechts = (0,0)
    #MY Es werden 1600 1/16-Schritte fuer 180 Grad benoetigt, 800 fuer 90 Grad
    stepper2(0, 0, 24600,   1, 0, 800,  1)  #my (mot=1) rechts drehend (dir=0)
    #12300, 600 halbe Schiene Fahrt nach rechts, 90 Grad Drehung nach rechts
    clupd("2", "0")

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Programm 7

# Drei Bilder gerade nach links aufnehmen

# 12300 Steps (MX: Achtelschritt) entsprechen 309 Millimeter Fahrweg
# 24600 Steps (MX: Achtelschritt) entsprechen 618 Millimeter Fahrweg

def press_7(event):
    clicked16()

def clicked16():
    global ge
    print("Programm 7...")
    if(ge):
       txt.insert(END,"Programm 7...\n")
       txt.see(END)
       frm.update()

    time.sleep(2)
    clupd(">", ">")
    stepper(0, 0, 27000, 1, 0)  #Nullung
    clupd("<", "<")
    time.sleep(2)
    stepper(0, 1, 400, 1, 1)    #Pos 1 (Ausgangsposition)
    clupd("0", "0")
    time.sleep(2)
    shot("07","00")
    time.sleep(2)

    clupd("<<", "<<")
    stepper(0, 1, 12300, 1, 1)  #Pos 2
    clupd("1", "309")
    time.sleep(2)
    shot("07","01")
    time.sleep(2)

    clupd("<<", "<<")
    stepper(0, 1, 12300, 1, 1)  #Pos 3
    clupd("2", "618")
    time.sleep(2)
    shot("07","02")


    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Programm 8

# 90 Grad in 5 Schritten zu 18 Grad abtasten

# 360 Grad: 200 Vollschritte oder 3200 1/16-Schritte (wir haben 1/16-Step eingestellt)
#  18 Grad:  10 Vollschritte oder  160 1/16-Schritte

def press_8(event):
    clicked17()

def clicked17():
    global ge
    print("Programm 8...")
    if(ge):
       txt.insert(END,"Programm 8...\n")
       txt.see(END)
       frm.update()

    clupd("0", "0")
    time.sleep(2)
    shot("08","00")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("1", "18")
    time.sleep(2)
    shot("08","01")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("2", "36")
    time.sleep(2)
    shot("08","02")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("3", "54")
    time.sleep(2)
    shot("08","03")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("4", "72")
    time.sleep(2)
    shot("08","04")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("5", "90")
    time.sleep(2)
    shot("08","05")


    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Programm 9

# 360 Grad in 20 Schritten zu 18 Grad abtasten

# 360 Grad: 200 Vollschritte oder 3200 1/16-Schritte (wir haben 1/16-Step eingestellt)
#  18 Grad:  10 Vollschritte oder  160 1/16-Schritte

def press_9(event):
    clicked18()

def clicked18():
    global ge
    print("Programm 9...")
    if(ge):
       txt.insert(END,"Programm 9...\n")
       txt.see(END)
       frm.update()

    clupd("0", "0")
    time.sleep(2)
    shot("09","00")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("1", "18")
    time.sleep(2)
    shot("09","01")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("2", "36")
    time.sleep(2)
    shot("09","02")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("3", "54")
    time.sleep(2)
    shot("09","03")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("4", "72")
    time.sleep(2)
    shot("09","04")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("5", "90")
    time.sleep(2)
    shot("09","05")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("6", "108")
    time.sleep(2)
    shot("09","06")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("7", "126")
    time.sleep(2)
    shot("09","07")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("8", "144")
    time.sleep(2)
    shot("09","08")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("9", "162")
    time.sleep(2)
    shot("09","09")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("10", "180")
    time.sleep(2)
    shot("09","10")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("11", "198")
    time.sleep(2)
    shot("09","11")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("12", "216")
    time.sleep(2)
    shot("09","12")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("13", "234")
    time.sleep(2)
    shot("09","13")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("14", "252")
    time.sleep(2)
    shot("09","14")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("15", "270")
    time.sleep(2)
    shot("09","15")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("16", "288")
    time.sleep(2)
    shot("09","16")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("17", "306")
    time.sleep(2)
    shot("09","17")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("18", "324")
    time.sleep(2)
    shot("09","18")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("19", "342")
    time.sleep(2)
    shot("09","19")
    time.sleep(2)

    stepper(1, 0, 160, 1, 1)
    clupd("20", "360")
    time.sleep(2)
    shot("09","20")

    print("...fertig.")
    print("----------------------------------------------------------")
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Hilfe (X-Modus)

def press_h(event):
    clicked19()

def clicked19():
    global ge
    if (ge):
       txt.insert(END,"r/s - Reboot/Shutdown\n")
       txt.insert(END,"x/h - Programm beenden/Hilfe\n")
       txt.insert(END,"n   - Nullung\n")
       txt.insert(END,"1/2 - Volle Fahrt l/r mit Nullung\n")
       txt.insert(END,"3/4 - L/R-Schwenk 180 Grad\n")
       txt.insert(END,"5/6 - P5/P6 - 2M-Slide r-l/l-r\n")
       txt.insert(END,"7   - P7 -  3 Fotos linear\n")
       txt.insert(END,"8   - P8 -  5 Fotos  90 Grad\n")
       txt.insert(END,"9   - P9 - 20 Fotos 360 Grad\n")
       txt.insert(END,"c   - Kamera ausloesen\n")
       txt.see(END)
       frm.update()

#-----------------------------------------------------------------------------
# Kamera ausloesen

def press_c(event):
    clicked20()

def clicked20():
    global ge, cfl

    subprocess.call(["sudo","killall","/usr/lib/gvfs/gvfs-gphoto2-volume-monitor"])
    subprocess.call(["sudo","killall","/usr/lib/gvfs/gvfsd-gphoto2"])

    if cfl:
       print("Aufnahme...")
       if(ge):
          txt.insert(END,"Aufnahme...\n")
          txt.see(END)
          frm.update()

       shot("99","00")

       print("...fertig.")
       print("----------------------------------------------------------")
       if(ge):
          txt.insert(END,"...fertig.\n")
          txt.see(END)
          frm.update()
    else:
       cfl = True

       print("...Kamera eingeschalten.")
       print("----------------------------------------------------------")
       if(ge):
          txt.insert(END,"...Kamera eingeschalten.\n")
          txt.see(END)
          txt3.delete(1.0, END)
          txt3.insert(END,"Kamera ein.")
          frm.update()

def shot(pr,pn):
    global ge, pc, sr, cfl

    pc = pc + 1
    if pc > 9999:
       pc = 1

    pcstr = str(pc)
    if len(pcstr) < 4:
       pcstr = "0" + pcstr
    if len(pcstr) < 4:
       pcstr = "0" + pcstr
    if len(pcstr) < 4:
       pcstr = "0" + pcstr

    #logging.basicConfig(format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    #callback_obj = gp.check_result(gp.use_python_logging())

    if cfl:
       camera = gp.Camera()
       camera.init()
       file_path = camera.capture(gp.GP_CAPTURE_IMAGE)

       dfile = pcstr + "_" + pr + pn + ".jpg"
       target = os.path.join('/media/pi/STICK/images/' + sr,dfile)
       fupd(dfile)

       camera_file = camera.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
       camera_file.save(target)
       camera.exit()
    else:
       fupd("Kamera aus.")

#-----------------------------------------------------------------------------
# Textboxen updaten

def clupd(str1, str2):
    global ge
    if(ge):
       txt1.delete(1.0, END)
       txt1.insert(END,str1)
       txt2.delete(1.0, END)
       txt2.insert(END,str2)
       frm.update()
    print(str1)
    print(str2)

#-----------------------------------------------------------------------------
# Fotobox updaten

def fupd(str1):
    global ge
    if(ge):
       txt3.delete(1.0, END)
       txt3.insert(END,str1)
       frm.update()
    print(str1)

#-----------------------------------------------------------------------------
# Hilfe (Textmodus)

def help():
  print(" ")
  print("r   -  Reboot")
  print("s   -  Shutdown")
  print("x   -  Programm beenden")
  print("t/i -  Stepper-Test / Input-Test")
  print("n   -  Nullung")
  print("1/a -  Fahrt nach links / ohne Endstop!")
  print("2/b -  Fahrt nach rechts / ohne Nullung")
  print("3   -  Linksschwenk 180 Grad")
  print("4   -  Rechtsschwenk 180 Grad")
  print("5   -  Programm 5 (2M-Slide r-l)")
  print("6   -  Programm 6 (2M-Slide l-r)")
  print("7   -  Programm 7 (3 Aufnahmen linear)")
  print("8   -  Programm 8 (90 Grad in 5 Aufnahmen)")
  print("9   -  Programm 9 (360 Grad in 20 Aufnahmen)")
  print("h   -  Hilfe (diese Ausgabe)")
  print("c   -  Kamera ausloesen")
  print(" ")
  print( "Warte auf Eingabe...")
  print( "----------------------------------------------------------")

#-----------------------------------------------------------------------------
# main entry point

# stoerende Prozesse killen

subprocess.call(["sudo","killall","/usr/lib/gvfs/gvfs-gphoto2-volume-monitor"])
subprocess.call(["sudo","killall","/usr/lib/gvfs/gvfsd-gphoto2"])

# zufaellige Zeichenfolge zur Bildspeicherung erzeugen

sr = str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))
srdir = "/media/pi/STICK/images/" + sr
subprocess.call(["mkdir",srdir])


print(" ")
print("----------------------------------------------------------")
print("-----   foto slider R1 10.01.20                      -----")
print("----------------------------------------------------------")
print(" ")
print("Bildverzeichnis ist " + srdir + "...")
print("Kamera aus.")

help()

# initializing i2c bus

i2c = smbus.SMBus(1)

# 0F
# all inputs  (P0-P3) high level
# all outputs (P4-P7) low  level

i2c.write_byte(I2C_ADDR, 0xF0)

# preparing GPIOs

GPIO.setmode(GPIO.BCM)

control_pins = [xa,ya,za,aa]
for pin in control_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)

dir_pins = [xd,yd,zd,ad]
for pin in dir_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)

GPIO.setup(en, GPIO.OUT)
GPIO.output(en, True)


#-----------------------------------------------------------------------------
# when in X mode

if(ge):

    win = Tk()
    win.attributes("-fullscreen", True)
    win.title("foto slider")

    #win.geometry('480x320')
    win.geometry("%dx%d+0+0" % (480, 320))

    frm = Frame(master = win, width = 480, height = 320, bg ='grey')
    frm.pack()

    # obere Reihe

    btn1 = Button(master = frm, text="Reboot", font=("Helvetica", 11, "bold"), command=clicked1)
    btn1.place(x=16, y=14, width=60, height=30)

    btn2 = Button(master = frm, text="Down", font=("Helvetica", 11, "bold"), command=clicked2)
    btn2.place(x=88, y=14, width=60, height=30)

    btn3 = Button(master = frm, text="Exit", font=("Helvetica", 11, "bold"), command=clicked3)
    btn3.place(x=160, y=14, width=60, height=30)

    btn4 = Button(master = frm, text="Nullung", font=("Helvetica", 11, "bold"), command=clicked11)
    btn4.place(x=232, y=14, width=65, height=30)

    btn11 = Button(master = frm, text="Hilfe", font=("Helvetica", 11, "bold"), command=clicked19)
    btn11.place(x=309, y=14, width=62, height=30)

    # untere Reihe

    btn5 = Button(master = frm, text="Links", font=("Helvetica", 11, "bold"), command=clicked12)
    btn5.place(x=16, y=276, width=46, height=30)

    btn6 = Button(master = frm, text="Rechts", font=("Helvetica", 11, "bold"), command=clicked13)
    btn6.place(x=74, y=276, width=55, height=30)

    btn7 = Button(master = frm, text="L-Schw", font=("Helvetica", 11, "bold"), command=clicked7)
    btn7.place(x=141, y=276, width=63, height=30)

    btn8 = Button(master = frm, text="R-Schw", font=("Helvetica", 11, "bold"), command=clicked8)
    btn8.place(x=216, y=276, width=63, height=30)

    btn15 = Button(master = frm, text="Cam", font=("Helvetica", 11, "bold"), command=clicked20)
    btn15.place(x=291, y=276, width=48, height=30)

    # rechte Seite

    btn9 = Button(master = frm,  text="P5  2M li", font=("Helvetica", 11, "bold"), command=clicked9)
    btn9.place(x=384, y=14, width=80, height=30)

    btn10 = Button(master = frm, text="P6  2M re", font=("Helvetica", 11, "bold"), command=clicked10)
    btn10.place(x=384, y=56, width=80, height=30)

    btn12 = Button(master = frm, text="P7  3F Sl", font=("Helvetica", 11, "bold"), command=clicked16)
    btn12.place(x=384, y=98, width=80, height=30)

    btn13 = Button(master = frm, text="P8  5F Ro", font=("Helvetica", 11, "bold"), command=clicked17)
    btn13.place(x=384, y=140, width=80, height=30)

    btn14 = Button(master = frm, text="P9 20F360", font=("Helvetica", 11, "bold"), command=clicked18)
    btn14.place(x=384, y=182, width=80, height=30)

    txt1 = Text(master = frm, wrap='word', width=5, height=1, bg='#fe9', font=("Mono", 11, "bold"))
    txt1.place(x=387, y=225, width=74, height=20)

    txt2 = Text(master = frm, wrap='word', width=5, height=1, bg='#fe9', font=("Mono", 11, "bold"))
    txt2.place(x=387, y=246, width=74, height=20)

    txt3 = Text(master = frm, wrap='word', width=5, height=1, bg='#9ef', font=("Mono", 10, "bold"))
    txt3.place(x=350, y=279, width=120, height=25)


    txt = Text(master = frm, wrap='word', width=45, height=5, bg='beige', font=("Mono", 11, "bold"))
    scroll = Scrollbar(master = frm)
    scroll.config(command = txt.yview)
    txt.config(yscrollcommand = scroll.set)
    txt.place(x=20, y=58, width=340, height=203)
    scroll.place(x=360, y=58, width=10, height=203)

    clicked19() # X-Hilfe/Startscreen in der Textbox

    # Anzeige der kamera-Stati
    txt1.delete(1.0, END)
    txt1.insert(END,sr[0:4])
    txt2.delete(1.0, END)
    txt2.insert(END,sr[4:8])
    txt3.delete(1.0, END)
    txt3.insert(END,"Kamera aus.")
    frm.update()

    win.bind('r',press_r)
    win.bind('s',press_s)
    win.bind('x',press_x)
    win.bind('n',press_n)
    win.bind('1',press_1)
    win.bind('2',press_2)
    win.bind('3',press_3)
    win.bind('4',press_4)
    win.bind('5',press_5)
    win.bind('6',press_6)
    win.bind('7',press_7)
    win.bind('8',press_8)
    win.bind('9',press_9)
    win.bind('h',press_h)
    win.bind('c',press_c)

    win.mainloop()

#-----------------------------------------------------------------------------
# only in terminal mode

else:

   global done
   done = False
   key = ' '
   key2 = ' '

   while not done:

       key = raw_input()
       if key   == 'r':
           press_r(0)
       elif key   == 's':
           press_s(0)
       elif key   == 'x':
           press_x(0)
       elif key   == 't':
           print("Wirklich Motoren testen? - Slider bitte auf Mitte schieben.")
           print("j - ja / sonst - verlassen")
           key2 = raw_input()
           if key2 == 'j':
              press_t(0)
           else:
              print("Warte auf neue Eingabe...")
       elif key   == 'i':
           press_i(0)
       elif key   == 'n':
           press_n(0)
       elif key   == 'a':
           print("Wirklich nach links ohne Nullung (kein Endstop!!) fahren?")
           print("j - ja / sonst - verlassen")
           key2 = raw_input()
           if key2 == 'j':
              press_a(0)
           else:
              print("Warte auf neue Eingabe...")
       elif key   == 'b':
           print("Wirklich nach rechts ohne Nullung (etwa auf Endstop) fahren?")
           print("j - ja / sonst - verlassen")
           key2 = raw_input()
           if key2 == 'j':
              press_b(0)
           else:
              print("Warte auf neue Eingabe...")
       elif key   == '1':
           press_1(0)
       elif key   == '2':
           press_2(0)
       elif key   == '3':
           press_3(0)
       elif key   == '4':
           press_4(0)
       elif key   == '5':
           press_5(0)
       elif key   == '6':
           press_6(0)
       elif key   == '7':
           press_7(0)
       elif key   == '8':
           press_8(0)
       elif key   == '9':
           press_9(0)
       elif key   == 'h':
           help()
       elif key   == 'c':
           press_c(0)

#-----------------------------------------------------------------------------






"""

def main():
    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    callback_obj = gp.check_result(gp.use_python_logging())
    camera = gp.Camera()
    camera.init()
    print('Capturing image')
    file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
    print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
    target = os.path.join('/tmp', file_path.name)
    print('Copying image to', target)
    camera_file = camera.file_get(
        file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
    camera_file.save(target)
    subprocess.call(['xdg-open', target])
    camera.exit()
    return 0

if __name__ == "__main__":
    sys.exit(main())



import time
import sys
import os
import ftplib
import RPi.GPIO as GPIO
from picamera import PiCamera

#-----------------------------------------------------------------------------

from PIL import Image,ImageDraw,ImageFont,ImageColor,ImageTk

if abertc:
   from ABE_RTCPi import RTC
   from ABE_helpers import ABEHelpers
if minlcd:
   import LCD_1in44
   import LCD_Config

#-----------------------------------------------------------------------------

imgpath = "/home/pi/scripts/thumbs/pre.gif"

#-----------------------------------------------------------------------------

KEY_UP_PIN     = 6
KEY_DOWN_PIN   = 19
KEY_LEFT_PIN   = 5
KEY_RIGHT_PIN  = 26
KEY_PRESS_PIN  = 13
KEY1_PIN       = 21
KEY2_PIN       = 20
KEY3_PIN       = 16

GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY_UP_PIN,      GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY_DOWN_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY_LEFT_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY_RIGHT_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY_PRESS_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY1_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY2_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY3_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)

#-----------------------------------------------------------------------------

iso = 0  # automatic
ips = False # Infrarot-Preset

#-----------------------------------------------------------------------------

def press_i(event):
    global iso
    global ge
    global ips

    #----------------------------------
    # Infrarot Preset

    ips = True

    #----------------------------------

    if(ge):
       txt.insert(END,"Voreinstellung für Infrarot.\n")
       txt.see(END)
    print "Voreinstellung für Infrarot."
    print "----------------------------------------------------------"

#-----------------------------------------------------------------------------

def press_n(event):
    global iso
    global ge
    global ips

    #----------------------------------
    # Standard Preset

    iso = 0
    ips = False

    #----------------------------------

    if(ge):
       txt.insert(END,"Standardeinstellung.\n")
       txt.see(END)
    print "Standardeinstellung gesetzt."
    print "----------------------------------------------------------"

#-----------------------------------------------------------------------------

def press_num0(event):
    global iso
    global ge
    iso = 0
    if(ge):
       txt.insert(END,"ISO Automatik.\n")
       txt.see(END)
    print "ISO auf Automatik gesetzt."
    print "----------------------------------------------------------"

def press_num1(event):
    global iso
    global ge
    iso = 100
    if(ge):
       txt.insert(END,"ISO auf 100 gesetzt.\n")
       txt.see(END)
    print "ISO auf 100 gesetzt."
    print "----------------------------------------------------------"

def press_num2(event):
    global iso
    global ge
    iso = 200
    if(ge):
       txt.insert(END,"ISO auf 200 gesetzt.\n")
       txt.see(END)
    print "ISO auf 200 gesetzt."
    print "----------------------------------------------------------"

def press_num3(event):
    global iso
    global ge
    iso = 300
    if(ge):
       txt.insert(END,"ISO auf 300 gesetzt.\n")
       txt.see(END)
    print "ISO auf 300 gesetzt."
    print "----------------------------------------------------------"

def press_num4(event):
    global iso
    global ge
    iso = 400
    if(ge):
       txt.insert(END,"ISO auf 400 gesetzt.\n")
       txt.see(END)
    print "ISO auf 400 gesetzt."
    print "----------------------------------------------------------"

def press_num5(event):
    global iso
    global ge
    iso = 500
    if(ge):
       txt.insert(END,"ISO auf 500 gesetzt.\n")
       txt.see(END)
    print "ISO auf 500 gesetzt."
    print "----------------------------------------------------------"

def press_num6(event):
    global iso
    global ge
    iso = 600
    if(ge):
       txt.insert(END,"ISO auf 600 gesetzt.\n")
       txt.see(END)
    print "ISO auf 600 gesetzt."
    print "----------------------------------------------------------"

def press_num7(event):
    global iso
    global ge
    iso = 700
    if(ge):
       txt.insert(END,"ISO auf 700 gesetzt.\n")
       txt.see(END)
    print "ISO auf 700 gesetzt."
    print "----------------------------------------------------------"

def press_num8(event):
    global iso
    global ge
    iso = 800
    if(ge):
       txt.insert(END,"ISO auf 800 gesetzt.\n")
       txt.see(END)
    print "ISO auf 800 gesetzt."
    print "----------------------------------------------------------"

#-----------------------------------------------------------------------------

def press_u(event):
    clicked8()

def clicked8():
   print "Probiere FTP..."
   global ge
   if(ge):
      txt.insert(END,"Probiere FTP...\n")
      txt.see(END)
   if minlcd:
      image = Image.open('/home/pi/scripts/thumbs/p07.bmp')
      LCD.LCD_ShowImage(image.rotate(180),0,0)

   time.sleep(2)
   try:
     ftp = ftplib.FTP('hosting111801.a2f33.netcup.net', 'statcam', 'sw371146_AS')#
   except:
     print "...Kein FTP möglich."
     print "----------------------------------------------------------"
     if(ge):
        txt.insert(END,"...kein FTP möglich.\n")
        txt.see(END)
   else:
     print "Starte FTP-Übertragung..."
     if(ge):
        txt.insert(END,"Starte FTP-Übertragung...\n")
        txt.see(END)
     files = os.listdir(outpath)
     for f in files:
         fi =  open(f,"r")
         ftp.storbinary("STOR " + f, fi)
         fi.close
     print "...fertig."
     print "----------------------------------------------------------"
     if(ge):
        txt.insert(END,"...fertig.\n")
        txt.see(END)
   ftp.quit
   if minlcd:
      image = Image.open('/home/pi/scripts/thumbs/p00.bmp')
      LCD.LCD_ShowImage(image.rotate(180),0,0)

   #print "Kopiere Files ins Archiv..."
   #time.sleep(2)
   #os.system("bash -c \"sudo cp \" + outpath + \"/*.jpg /home/pi/scripts/archive/\"")
   #print "...fertig."

#-----------------------------------------------------------------------------

def press_f(event):
    clicked6()

def clicked6():
    global outpath
    print "Formatiere..."
    global ge
    if(ge):
       txt.insert(END,"Formatiere...\n")
       txt.see(END)
    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p05.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)

    time.sleep(2)
    os.system("bash -c \"sudo rm -r -f /home/pi/scripts/images/\"")
    time.sleep(3)
    os.mkdir("/home/pi/scripts/images")
    os.mkdir(outpath)
    os.chdir(outpath)
    print "...fertig."
    print "----------------------------------------------------------"
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p00.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)

#-----------------------------------------------------------------------------

def press_l(event):
    clicked5()

def clicked5():
    global sr
    global ge
    print "Lösche Files in " + sr + "..."
    if(ge):
       txt.insert(END,"Lösche Files in " + sr + "...\n")
       txt.see(END)
    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p04.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)

    time.sleep(2)
    os.system("bash -c \"sudo rm *.jpg\"")
    print "...fertig."
    print "----------------------------------------------------------"
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)
    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p00.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)

#-----------------------------------------------------------------------------

def press_v(event):
    clicked1()

def clicked1():
    global ge
    global lbl2
    global btn9
    global iso
    global brn
    global ips

    print "Erstelle Vorschau..."
    if(ge):
       txt.insert(END,"Erstelle Vorschau...\n")
       txt.see(END)
    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p03.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)


    if ips:
       subprocess.call(["/home/pi/scripts/vorschau_inf.sh"])
    else:
       if   iso == 0:   isostr = "auto"
       elif iso == 100: isostr = "100"
       elif iso == 200: isostr = "200"
       elif iso == 300: isostr = "300"
       elif iso == 400: isostr = "400"
       elif iso == 500: isostr = "500"
       elif iso == 600: isostr = "600"
       elif iso == 700: isostr = "700"
       elif iso == 800: isostr = "800"
       subprocess.call(["/home/pi/scripts/vorschau_nrm.sh","/home/pi/scripts/vorschau.jpg",isostr])


    path = "/home/pi/scripts/vorschau.jpg"
    print "...fertig."
    print "----------------------------------------------------------"
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)

       size = 480, 360
       newpath = "/home/pi/scripts/vorschau.gif"
       im = Image.open("/home/pi/scripts/vorschau.jpg")
       im.thumbnail(size)
       im.save(newpath)

       img_b = Image.open(newpath)
       img_c = img_b.resize((400, 300))
       img_a = ImageTk.PhotoImage(img_c)
       lbl2 = Label(master = frm, image = img_a, font=("Helvetica", 10, "bold"))
       lbl2.image = img_a
       lbl2.place(x=40, y=10, width=400, height=300)

       btn9 = Button(master = frm, text="Zurück", font=("Helvetica", 11, "bold"), command=clicked9)
       btn9.place(x=300, y=270, width=80, height=30)
    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p00.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)

#-----------------------------------------------------------------------------

def press_z(event):
    clicked9()

def clicked9():
    lbl2.destroy()
    btn9.destroy()

#-----------------------------------------------------------------------------

def press_r(event):
    print "Rebooting..."
    print "----------------------------------------------------------"
    time.sleep(5)
    subprocess.call(["sudo","reboot"])

#-----------------------------------------------------------------------------

def press_a(event):
    clicked3()

def clicked3():
    global ge
    global lbl2
    global btn9
    global iso
    global brn
    global ips

    print "Nehme Bild auf..."
    if(ge):
       txt.insert(END,"Nehme Bild auf...\n")
       txt.see(END)
    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p01.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)

    br = str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9)) + ".jpg"

    if ips:
       subprocess.call(["/home/pi/scripts/capture_inf.sh",br])
    else:
       if   iso == 0:   isostr = "auto"
       elif iso == 100: isostr = "100"
       elif iso == 200: isostr = "200"
       elif iso == 300: isostr = "300"
       elif iso == 400: isostr = "400"
       elif iso == 500: isostr = "500"
       elif iso == 600: isostr = "600"
       elif iso == 700: isostr = "700"
       elif iso == 800: isostr = "800"
       subprocess.call(["/home/pi/scripts/capture_nrm.sh",br,isostr])

    print "...fertig."
    print "----------------------------------------------------------"
    if(ge):
       txt.insert(END,"...fertig.\n")
       txt.see(END)

       size = 480, 360
       newpath = "/home/pi/scripts/vorschau.gif"
       im = Image.open(br)
       im.thumbnail(size)
       im.save(newpath)

       img_b = Image.open(newpath)
       img_c = img_b.resize((400, 300))
       img_a = ImageTk.PhotoImage(img_c)
       lbl2 = Label(master = frm, image = img_a, font=("Helvetica", 10, "bold"))
       lbl2.image = img_a
       lbl2.place(x=40, y=10, width=400, height=300)

       btn9 = Button(master = frm, text="Zurück", font=("Helvetica", 11, "bold"), command=clicked9)
       btn9.place(x=300, y=270, width=80, height=30)

    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p00.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)

    # dname = "zc" + rtc.read_date() + ".jpg"
    # subprocess.call(["sudo","raspistill","-h","1800","-w","2400","-rot","180","-t","100","-q","90","-o",dname])
    # subprocess.call(["sudo","raspistill","-rot","180","-t","100","-q","92","-o",dname])

#-----------------------------------------------------------------------------

def press_t(event):
    clicked4()

def clicked4():
    global ge
    print "Nehme Bild auf nach 10s..."
    if(ge):
       txt.insert(END,"Nehme Bild auf nach 10s...\n")
       txt.see(END)
    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p02.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)
    counta(10)

def counta(count):
  global ge
  global lbl2
  global btn9
  global brn
  if(ge):
    if count > 0:
        btn6["text"] = count
        frm.after(1000, counta, count -1)
    elif count == 0:
        br = str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9)) + ".jpg"

        if ips:
          subprocess.call(["/home/pi/scripts/capture_inf.sh",br])
        else:
          if   iso == 0:   isostr = "auto"
          elif iso == 100: isostr = "100"
          elif iso == 200: isostr = "200"
          elif iso == 300: isostr = "300"
          elif iso == 400: isostr = "400"
          elif iso == 500: isostr = "500"
          elif iso == 600: isostr = "600"
          elif iso == 700: isostr = "700"
          elif iso == 800: isostr = "800"
          subprocess.call(["/home/pi/scripts/capture_nrm.sh",br,isostr])


        subprocess.call(["sudo","raspistill",b1str,b2str,i1str,i2str,"-rot","180","-t","100","-o",br])

        print "...fertig."
        print "----------------------------------------------------------"
        txt.insert(END,"...fertig.\n") 
        txt.see(END)
        btn6.configure(text = "verzögert")

        size = 480, 360
        newpath = "/home/pi/scripts/vorschau.gif"
        im = Image.open(br)
        im.thumbnail(size)
        im.save(newpath)

        img_b = Image.open(newpath)
        img_c = img_b.resize((400, 300))
        img_a = ImageTk.PhotoImage(img_c)
        lbl2 = Label(master = frm, image = img_a, font=("Helvetica", 10, "bold"))
        lbl2.image = img_a
        lbl2.place(x=40, y=10, width=400, height=300)

        btn9 = Button(master = frm, text="Zurück", font=("Helvetica", 11, "bold"), command=clicked9)
        btn9.place(x=300, y=270, width=80, height=30)

        # dname = "zc" + rtc.read_date() + ".jpg"
        # subprocess.call(["sudo","raspistill","-h","1800","-w","2400","-rot","180","-t","100","-q","90","-o",dname])
        # subprocess.call(["sudo","raspistill","-rot","180","-t","100","-q","92","-o",dname])
  else:
        br = str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9))+str(randint(0,9)) + ".jpg"


        if ips:
          subprocess.call(["/home/pi/scripts/capture_inf.sh",br])
        else:
          if   iso == 0:   isostr = "auto"
          elif iso == 100: isostr = "100"
          elif iso == 200: isostr = "200"
          elif iso == 300: isostr = "300"
          elif iso == 400: isostr = "400"
          elif iso == 500: isostr = "500"
          elif iso == 600: isostr = "600"
          elif iso == 700: isostr = "700"
          elif iso == 800: isostr = "800"
          subprocess.call(["/home/pi/scripts/capture_nrm.sh",br,isostr])


        print "...fertig."
        print "----------------------------------------------------------"

  if minlcd:
     image = Image.open('/home/pi/scripts/thumbs/p00.bmp')
     LCD.LCD_ShowImage(image.rotate(180),0,0)

#-----------------------------------------------------------------------------

def press_h(event):
    clicked7()

def clicked7():
    global ge
    global tastmode

    if(ge):
       txt.insert(END,"Shortkeys: a t v s r l f u h 0-8 i n\n")
       txt.insert(END,"a  - Aufnahme\n")
       txt.insert(END,"t  - Timer, Aufnahme nach 10s\n")
       txt.insert(END,"v  - Vorschau ohne Speichern der Aufnahme\n")
       txt.insert(END,"s/r- Shutdown/Reboot Kamera\n")
       txt.insert(END,"l  - Löschen der Files im aktuellen Verzeichnis\n")
       txt.insert(END,"f  - Formatieren (Bildverzeichnisse löschen)\n")
       txt.insert(END,"u  - Upload des aktuellen Verzeichnis per FTP\n")
       txt.insert(END,"h  - Hilfe\n")
       txt.insert(END,"0  - ISO Einstellung 0(auto) bis 8(800)\n")
       txt.insert(END,"i  - Voreinstellung für Infrarot\n")
       txt.insert(END,"n  - Normale / Standardeinstellung\n")
       txt.see(END)
    else:
       if tastmode == False:
          tastmode = True
          print "Tastaturmode eingeschalten"
          print "----------------------------------------------------------"
          image = Image.open('/home/pi/scripts/thumbs/p06.bmp')
          if minlcd:
             LCD.LCD_ShowImage(image.rotate(180),0,0)
             LCD_Config.Driver_Delay_ms(1000)
       else:
          tastmode = False
          print "Tastaturmode ausgeschalten"
          print "----------------------------------------------------------"
          image = Image.open('/home/pi/scripts/thumbs/p09.bmp')
          if minlcd:
             LCD.LCD_ShowImage(image.rotate(180),0,0)
             LCD_Config.Driver_Delay_ms(1000)

    print "Shortkeys sind:"
    print "a - Aufnahme"
    print "t - Timer, Aufnahme nach 10s"
    print "v - Vorschau ohne Speichern der Aufnahme"
    print "s - Shutdown Kamera"
    print "r - Reboot Kamera"
    print "l - Löschen der Files im aktuellen Verzeichnis"
    print "f - Formatieren (Bildverzeichnisse löschen)"
    print "u - Upload des aktuellen Verzeichnis per FTP"
    print "h - Hilfe (Tastaturwechsel)"
    print "0 - ISO Einstellung 0(auto) bis 8(800)"
    print "i - Voreinstellung für Infrarot"
    print "n - Normale / Standardeinstellung"
    print "----------------------------------------------------------"

    if minlcd:
       image = Image.open('/home/pi/scripts/thumbs/p08.bmp')
       LCD.LCD_ShowImage(image.rotate(180),0,0)

#-----------------------------------------------------------------------------

def callback(e):
    img1 = PhotoImage(file=imgpath)
    lbl2.configure(image = img1)
    lbl2.image = img1

#-----------------------------------------------------------------------------

#i2c_helper = ABEHelpers()
#bus = i2c_helper.get_smbus()
#rtc = RTC(bus)

# set the date using ISO 8601 format - YYYY-MM-DDTHH:MM:SS
# rtc.set_date("2018-08-25T23:40:00")

print " "
print "----------------------------------------------------------"
print "-----   zerocam R4 14.09.19                          -----"
print "----------------------------------------------------------"
print " "

if minlcd:
   LCD = LCD_1in44.LCD()
   Lcd_ScanDir = LCD_1in44.SCAN_DIR_DFT
   LCD.LCD_Init(Lcd_ScanDir)
   LCD.LCD_Clear()

   image = Image.open('/home/pi/scripts/thumbs/p00.bmp')
   LCD.LCD_ShowImage(image.rotate(180),0,0)
   LCD_Config.Driver_Delay_ms(1000)


print "Kamera bereit. Shortkeys sind:"
print "a - Aufnahme"
print "t - Timer, Aufnahme nach 10s"
print "v - Vorschau ohne Speichern der Aufnahme"
print "r - Reboot Kamera"
print "l - Löschen der Files im aktuellen Verzeichnis"
print "f - Formatieren (Bildverzeichnisse löschen)"
print "u - Upload des aktuellen Verzeichnis per FTP"
print "h - Hilfe (Tastaturwechsel)"
print "0 - ISO Einstellung 0(auto) bis 8(800)"
print "i - Voreinstellung für Infrarot"
print "n - Normale / Standardeinstellung"

if(ge):


   sw = 480
   sh = 320
   bb = 90
   bh = 30
   bho = 25
   bqb = 80
   bqh = 80
   ro = 15
   rl = 15
   rms = 15
   rmw = 15
   rmwr = 25
   ru = 15

   btn1 = Button(master = frm, text="Vorschau", font=("Helvetica", 11, "bold"), command=clicked1)
   btn1.place(x=sw-rl-bqb, y=ro, width=bqb, height=bqh)

   btn3 = Button(master = frm, text="Aufnahme", font=("Helvetica", 11, "bold"), command=clicked3)
   btn3.place(x=sw-rl-bqb, y=ro+bqb+rmwr, width=bqb, height=bqh)

   btn6 = Button(master = frm, text="verzögert", font=("Helvetica", 11, "bold"), command=clicked4)
   btn6.place(x=sw-rl-bqb, y=ro+bqb+rmwr+bqb+rmwr, width=bqb, height=bqh)


   btn4 = Button(master = frm, text="Löschen", font=("Helvetica", 11, "bold"), command=clicked5)
   btn4.place(x=rl, y=sh-ru-bh, width=bb, height=bh)

   btn5 = Button(master = frm, text="Formatieren", font=("Helvetica", 11, "bold"), command=clicked6)
   btn5.place(x=rl+bb+rms, y=sh-ru-bh, width=bb+10, height=bh)

   btn8 = Button(master = frm, text="Upload", font=("Helvetica", 11, "bold"), command=clicked8)
   btn8.place(x=rl+bb+rms+bb+25+rms, y=sh-ru-bh, width=bb, height=bh)

   lbl1 = Label(master = frm, text = sr, font=("Helvetica", 10, "bold"))
   lbl1.place(x=rl, y=ro, width=bb, height=20)


   btn7 = Button(master = frm, text="Hilfe", font=("Helvetica", 11, "bold"), command=clicked7)
   btn7.place(x=rl+bb+rms+bb+rms+20, y=ro, width=bb, height=bho)

   #img_b = Image.open(imgpath)
   #img_c = img_b.resize((400, 300))
   #img_a = ImageTk.PhotoImage(img_c)
   #lbl2 = Label(master = frm, image = img_a, font=("Helvetica", 10, "bold"))
   #lbl2.image = img_a
   #lbl2.place(x=rl, y=ro, width=400, height=300)

   #txt.insert(END,rtc.read_date()+"\n")
   txt.insert(END,"Kamera bereit.\n")
   txt.insert(END,"Shortkeys: a t v s r l f u h 0-8 i n\n")
   txt.insert(END,"a  - Aufnahme\n")
   txt.insert(END,"t  - Timer, Aufnahme nach 10s\n")
   txt.insert(END,"v  - Vorschau ohne Speichern der Aufnahme\n")
   txt.insert(END,"s/r- Shutdown/Reboot Kamera\n")
   txt.insert(END,"l  - Löschen der Files im aktuellen Verzeichnis\n")
   txt.insert(END,"f  - Formatieren (Bildverzeichnisse löschen)\n")
   txt.insert(END,"u  - Upload des aktuellen Verzeichnis per FTP\n")
   txt.insert(END,"h  - Hilfe\n")
   txt.insert(END,"0  - ISO Einstellung 0(auto) bis 8(800)\n")
   txt.insert(END,"i  - Voreinstellung für Infrarot\n")
   txt.insert(END,"n  - Normale / Standardeinstellung\n")
   txt.see(END)

   # main functions
   win.bind('a',press_a)
   win.bind('t',press_t)
   win.bind('v',press_v)
   win.bind('l',press_l)
   win.bind('f',press_f)
   win.bind('u',press_u)
   win.bind('h',press_h)

   win.bind('z',press_z)

   win.bind('r',press_r)

   # iso sets
   win.bind('0',press_num0) # automatic 
   win.bind('1',press_num1) # ISO 100
   win.bind('2',press_num2)
   win.bind('3',press_num3)
   win.bind('4',press_num4)
   win.bind('5',press_num5)
   win.bind('6',press_num6)
   win.bind('7',press_num7)
   win.bind('8',press_num8) # ISO 800

   win.bind('i',press_i)    # Infrarot Preset
   win.bind('n',press_n)    # Normal / Default Preset


         elif key == 'l':
           press_l(0)
         elif key == 'f':
           press_f(0)
         elif key == 'u':
           press_u(0)
         elif key == 'h':
           press_h(0)

         elif key == 'r':
           press_r(0)

         elif key == '0':
           press_num0(0)
         elif key == '1':
           press_num1(0)
         elif key == '2':
           press_num2(0)
         elif key == '3':
           press_num3(0)
         elif key == '4':
           press_num4(0)
         elif key == '5':
           press_num5(0)
         elif key == '6':
           press_num6(0)
         elif key == '7':
           press_num7(0)
         elif key == '8':
           press_num8(0)

         elif key == 'i':
           press_i(0)
         elif key == 'n':
           press_n(0)

      else: time.sleep(1)

      if GPIO.input(KEY_UP_PIN) == 0:
        press_h(0)
      if GPIO.input(KEY_LEFT_PIN) == 0:
        press_a(0)
      if GPIO.input(KEY_RIGHT_PIN) == 0:
        press_v(0)
      if GPIO.input(KEY_DOWN_PIN) == 0:
        press_u(0)
      if GPIO.input(KEY_PRESS_PIN) == 0:
        press_t(0)
      if GPIO.input(KEY1_PIN) == 0:
        press_s(0)
      if GPIO.input(KEY2_PIN) == 0:
        press_f(0)
      if GPIO.input(KEY3_PIN) == 0:
        press_l(0)

#-----------------------------------------------------------------------------"""

