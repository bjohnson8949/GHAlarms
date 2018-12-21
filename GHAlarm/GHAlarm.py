# This is all based off the API info found below
# https://rithvikvibhu.github.io/GHLocalApi/#top
#

import datetime
import urllib.request
import json
from collections import namedtuple
import time
import threading


class GHAlarmInterface:
    TargetIP = ""

    def __init__(self, ip):
        self.TargetIP = ip

    """Pull current alarms from the home"""
    def get_alarms(self):
        current_alarms = set({})
        print('Getting Alarms')
        default_port = "8008"
        api_path = "/setup/assistant/alarms"
        url = "http://{}:{}{}".format(self.TargetIP, default_port, api_path)

        # Grab alarms from google home
        data = urllib.request.urlopen(url).read()
        x = json.loads(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

        # Loading new
        for alarm in x.alarm:
            # Fire time is in milliseconds
            converted_alarm_time = int(alarm.fire_time / 1000)
            current_alarms.add(converted_alarm_time)

        print("Got {} Alarms".format(len(current_alarms)))
        return current_alarms

    """Validate alarm is still on the home"""
    def alarm_exist(self, fire_time):
        found = False

        for alarm in self.get_alarms():
            if alarm == fire_time:
                found = True
                break
        return found


class AlarmClock:

    def __init__(self, ip):
        self.gh = GHAlarmInterface(ip)

    """This is used once alarm is found to wait to trigger it"""
    def active_watcher(self, fire_time):
        precheck_time = (fire_time - 10) - datetime.datetime.now().timestamp()

        # Possible less then 10 seconds to sound when detected
        if precheck_time > 0:
            time.sleep(precheck_time)

        if self.gh.alarm_exist(fire_time):
            time_till_alarm = int(fire_time - datetime.datetime.now().timestamp())

            """ Currently sounding alarm maybe a late pickup """
            if time_till_alarm > 0:
                time.sleep(time_till_alarm)
            print("Alarm")

    """Main loop for interacting with google home and starting watcher threads"""
    def watcher(self):
        check_frequency = 30
        active_alarms = []

        while True:
            current_alarms = self.gh.get_alarms()

            """Look for new alarms"""
            for alarm in current_alarms:
                if alarm not in active_alarms:
                    print('Adding alarm')
                    active_alarms.append(alarm)
                    t = threading.Thread(target=self.active_watcher, args=(alarm,))
                    t.start()

            """ Clear old alarms """
            for alarm in active_alarms:
                if alarm not in current_alarms:
                    active_alarms.remove(alarm)

            time.sleep(check_frequency)


def main():
    ac = AlarmClock("127.0.0.1")
    ac.watcher()


main()


