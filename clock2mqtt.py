#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# clock2mqtt
#
#    Provides real time clock data
#
#   Data items provided:
#       year
#       month
#       day
#       hour
#       minute
#
#       utc-year
#       utc-month
#       utc-day
#       utc-hour
#       utc-minute
#
#       tz
#       dst
#       
#       dow
#       doy
#
#       moonrise
#       moonphase
#       sunrise
#       sunrise-civil
#       sunrise-astronautical
#       


__author__ = "Dennis Sell"
__copyright__ = "Copyright (C) Dennis Sell"


APPNAME = "clock2mqtt"
VERSION = "0.10"


import sys
import os
import mosquitto
import socket
import time
import subprocess
import logging
import signal
import threading
import pymetar
import commands
import datetime
import ephem
from daemon import Daemon
from mqttcore import MQTTClientCore
from mqttcore import main


class MyMQTTClientCore(MQTTClientCore):
    def __init__(self, appname, clienttype):
        MQTTClientCore.__init__(self, appname, clienttype)
        self.clientversion = VERSION
        self.interval = self.cfg.INTERVAL
        self.clientversion = VERSION
        self.observer = ephem.Observer()
        self.observer.lat = '38'
        self.observer.lon = '-93'
        self.sun = ephem.Sun()
        self.moon = ephem.Moon()
        self.year=""
        self.month=""
        self.day=""
        self.dow=""
        self.doy=""
        self.hour=""
        self.mil_hour=""
        self.ampm=""
        self.minute=""
        self.sunrise=""
        self.utc_sunrise=""
        self.sunset=""
        self.utc_sunset=""
        self.moonrise=""
        self.utc_moonrise=""
        self.moonset=""
        self.utc_moonset=""
        self.sunstate=""
        self.moonstate=""
        self.t = threading.Thread(target=self.do_thread_loop)
        self.t.start()

    def do_thread_loop(self):
        while(self.running):
            if ( self.mqtt_connected ):    
                nowtime=datetime.datetime.now()
                if(nowtime.year != self.year):
                    self.year = nowtime.year
                    self.mqttc.publish("/raw/clock/year", self.year, retain=True)
                if(nowtime.month != self.month):
                    self.month = nowtime.month
                    self.mqttc.publish("/raw/clock/month", self.month, retain=True)
                if(nowtime.day != self.day):
                    self.day = nowtime.day
                    self.mqttc.publish("/raw/clock/day", self.day, retain=True)
                    self.utc_sunrise=self.observer.next_rising(self.sun)
#                    self.mqttc.publish("/raw/clock/utc_sunrise", str(self.utc_sunrise), retain=True)
                    self.sunrise=ephem.localtime(self.observer.next_rising(self.sun))
                    self.mqttc.publish("/raw/clock/sunrise", str(self.sunrise), retain=True)
                    self.utc_sunset=self.observer.next_setting(self.sun)
#                    self.mqttc.publish("/raw/clock/utc_sunset", str(self.utc_sunset), retain=True)
                    self.sunset=ephem.localtime(self.observer.next_setting(self.sun))
                    self.mqttc.publish("/raw/clock/sunset", str(self.sunset), retain=True)
                    self.utc_moonrise=self.observer.next_rising(self.moon)
#                    self.mqttc.publish("/raw/clock/utc_moonrise", str(self.utc_moonrise), retain=True)
                    self.moonrise=ephem.localtime(self.observer.next_rising(self.moon))
                    self.mqttc.publish("/raw/clock/moonrise", str(self.moonrise), retain=True)
                    self.utc_moonset=self.observer.next_setting(self.moon)
#                    self.mqttc.publish("/raw/clock/utc_moonset", str(self.utc_moonset), retain=True)
                    self.moonset=ephem.localtime(self.observer.next_setting(self.moon))
                    self.mqttc.publish("/raw/clock/moonset", str(self.moonset), retain=True)
                    self.nextnewmoon=ephem.next_new_moon(nowtime)
                    self.mqttc.publish("/raw/clock/nextnewmoon", str(self.nextnewmoon), retain=True) 
                    self.nextfirstquartermoon=ephem.next_first_quarter_moon(nowtime)
                    self.mqttc.publish("/raw/clock/nextfirstquartermoon", str(self.nextfirstquartermoon), retain=True)
                    self.nextlastquartermoon=ephem.next_last_quarter_moon(nowtime)
                    self.mqttc.publish("/raw/clock/nextlastquartermoon", str(self.nextlastquartermoon), retain=True)
                    self.nextfullmoon=ephem.next_full_moon(nowtime)
                    self.mqttc.publish("/raw/clock/nextfullmoon", str(self.nextfullmoon), retain=True)                   
                if(nowtime.hour != self.mil_hour):
                    self.mil_hour = nowtime.hour
                    self.hour = self.mil_hour % 12
                    if (self.hour == 0):
                        self.hour = 12
                    self.mqttc.publish("/raw/clock/hour", self.hour, retain=True)
                    self.mqttc.publish("/raw/clock/militaryhour", self.mil_hour, retain=True)
                    if(((self.mil_hour == 11) and (self.minute > 59)) or (self.mil_hour > 11)):
                        self.ampm = "PM"
                    else:
                        self.ampm = "AM"
                    self.mqttc.publish("/raw/clock/ampm", self.ampm, retain=True)
                if(nowtime.minute != self.minute):
                    self.minute = nowtime.minute
                    self.mqttc.publish("/raw/clock/minute", self.minute, retain=True)
                if(nowtime.day == self.sunrise.day):
                    temp = "set" 
                else:
                    if(nowtime.day == self.sunset.day):
                        temp="rise"
                    else:
                        temp="set"
                if(temp != self.sunstate):
                    self.sunstate=temp
                    self.mqttc.publish("/raw/clock/sunstate", self.sunstate, retain=True)
                if ( self.interval ):
                    print "Waiting ", self.interval, " seconds for next update."
                    time.sleep(self.interval)


class MyDaemon(Daemon):
    def run(self):
        mqttcore = MyMQTTClientCore(APPNAME, clienttype="type1")
        mqttcore.main_loop()


if __name__ == "__main__":
    daemon = MyDaemon('/tmp/' + APPNAME + '.pid')
    main(daemon)
