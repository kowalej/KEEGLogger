#!/usr/bin/python

import sys
import getopt
import argparse
import re
import getpass
import os
import helpers
import platform
import subprocess
import time
import configparser
from data_collection import DataCollection
from password_types import PasswordTypes
from constants import Constants
from prediction import Prediction

class Program:
    def __init__(self):
        helpers.load_default_config()
        parser = argparse.ArgumentParser(
            description='KEEGLogger is a demostration of password cracking that uses your brainwave data to infer keystrokes.',
            usage='''KEEGLogger.py <command> [<args>]
    These are the commands:
    startfresh     Starts a new instance with step by step instructions.
    createuser     Creates a new user. Must run this before activateuser, if user doesn't yet exist.
    activateuser   Sets the active user.
    activatemode   Sets the active mode (i.e. password type).
    setpass        Records a new password (note: this is optional and used only for display during prediction).
    collect        Collect data for the model. You will type in passwords while your EEG data is recorded.
    predict        You will enter your password and the model will predict it based soley on EEG data.

    Upon first use just run "startfresh" and follow the step by step instructions.

    Password modes: 
        Mode 1:  4-digit pin number.
        Mode 2: 8 character password (case insensitive).
        ''')

        parser.add_argument('command', help='Command to run.')

        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Incorrect usage. See help below.')
            parser.print_help()
            exit(1)

        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def startfresh(self):
        parser = argparse.ArgumentParser(description='Runs fresh instance from the start.')
        parser.add_argument('-mid', '--museid', nargs=1, required=False, help='Muse MAC address.')
        args = parser.parse_args(sys.argv[2:])
        if args.museid:
            self.museID = args.museid
        else:
           self.museID = None
        self.start_fresh_instance()

    def createuser(self):
        parser = argparse.ArgumentParser(description='Create a new user profile.')
        parser.add_argument('username', type=str, help='Valid username, It must contain only letters and numbers and {0}.'.format(self.length_msg(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)))
        parser.add_argument('-a', '--activate', action='store_true', default=True, required=False, help='Set as active user after creation.')
        args = parser.parse_args(sys.argv[2:])
        if not self.validate_username(args.username):
            self.print_cannot_create_user()
            return
        elif self.check_user_exists(args.username):
            print('User already exists, will activate if -a or --activate was provided.')
        else: 
            self.create_user(args.username)
            print('User {0} created.'.format(args.username))
        if not args.activate == None:
            self.set_active_user(args.username)
            print('Active user set to: {0}.'.format(args.username))

    def activateuser(self):
        parser = argparse.ArgumentParser(description='Set active user.')
        parser.add_argument('username', type=str, help='Username to activate.')
        args = parser.parse_args(sys.argv[2:])
        if not self.check_user_exists(args.username):
            print('Cannot set active user, user does not exist. Try running "createuser" first or see users below:')
            self.print_users()
        else: 
            self.set_active_user(args.username)
            self.print_active_user()

    def activatemode(self):
        parser = argparse.ArgumentParser(description='Set active mode.')
        parser.add_argument('mode', type=int, help='Password mode number to activate.')
        args = parser.parse_args(sys.argv[2:])
        if not PasswordTypes.has_value(args.mode):
            self.print_invalid_mode()
        else: 
            self.set_active_mode(PasswordTypes(args.mode))
            print('Active mode set to {0}.'.format(args.mode))

    def setpass(self):
        parser = argparse.ArgumentParser(description='Set a new password for active user.')
        parser.add_argument('-u', '--username', type=str, help='Specific username to set password for. Command defaults to active user.')
        parser.add_argument('-m', '--mode', type=int, help='Password integer mode number.')
        args = parser.parse_args(sys.argv[2:])
        if not args.username == None and not self.check_user_exists(args.username):
            print("Cannot set password, user does not exist. See users below:")
            self.print_users()
        elif not args.mode == None and not PasswordTypes.has_value(helpers.safe_cast(args.mode, int)):
            self.print_invalid_mode()
        else:
            username = args.username if not args.username == None else self.get_active_user()
            mode = PasswordTypes(args.mode) if not args.mode == None else self.get_active_mode()
            print('Setting password for user: {0}, password mode: {1}...'.format(username, mode))
            password = self.get_password(mode)
            self.write_password(username, password, mode)

    def collect(self):
        parser = argparse.ArgumentParser(description='Collect data for the model. You will type in passwords while your EEG data is recorded.')
        parser.add_argument('-mid', '--museid', type=int, required=False, help='Muse MAC Address. If ommitted, the first available device is used.')
        args = parser.parse_args(sys.argv[2:])
        if args.museid:
            self.museID = args.museid
        else:
           self.museID = None
        self.begin_collection()

    def predict(self):
        parser = argparse.ArgumentParser(description='You will enter your password and the model will predict it based soley on EEG data.')
        parser.add_argument('-mid', '--museid', type=int, required=False, help='Muse MAC Address. If ommitted, the first available device is used.')
        args = parser.parse_args(sys.argv[2:])
        if args.museid:
            self.museID = args.museid
        else:
           self.museID = None
        self.begin_prediction()

    def validate_username(self, username):
        pattern = '^\w{{{0},{1}}}\Z'.format(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)
        passRegex = re.compile(pattern)
        return passRegex.match(username)

    def create_user(self, username):
        helpers.write_config(Constants.CONFIG_USERNAME_PREFIX + username)

    def check_user_exists(self, username):
        return helpers.read_config().has_section(Constants.CONFIG_USERNAME_PREFIX + username)

    def get_user_list(self):
        users = list(filter(lambda x: Constants.CONFIG_USERNAME_PREFIX in x, helpers.read_config().sections()))
        return list(map(lambda x: x.replace(Constants.CONFIG_USERNAME_PREFIX,''), users))

    def get_active_user(self):
        return helpers.read_config().get(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_USER)

    def set_active_user(self, username):
        helpers.write_config(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_USER, username)

    def get_active_mode(self):
        return PasswordTypes(int(helpers.read_config().get(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_MODE)))

    def set_active_mode(self, mode):
        helpers.write_config(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_MODE, mode.value)

    def get_user_password(self, user, mode):
        return helpers.read_config().get(Constants.CONFIG_USERNAME_PREFIX + user, Constants.CONFIG_OPTION_PASSWORD_PREFIX + str(mode))

    def print_users(self):
        users = self.get_user_list()
        print('Total users: {0}'.format(len(users)))
        print(*self.get_user_list(), sep='\n')

    def print_active_user(self):
        print('Active user set to: {0}.'.format(self.get_active_user()))

    def print_active_mode(self):
        print('Active mode set to: {0}.'.format(self.get_active_mode()))

    def print_cannot_create_user(self):
        print('Cannot create user.')
        print('Username has incorrect format. It must contain only letters and numbers and {0}.'.format(self.length_msg(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)))

    def print_invalid_mode(self):
        print("Invalid mode specified. See available modes below:")
        for mode in PasswordTypes:
            print("Mode: {0} ({1})".format(mode.value, mode))

    def write_password(self, username, password, mode):
        helpers.write_config(Constants.CONFIG_USERNAME_PREFIX + username, Constants.CONFIG_OPTION_PASSWORD_PREFIX + str(mode), password)
        print("Wrote password for user: {0}.".format(username))

    def length_msg(self, passMinLength, passMaxLength):
        if passMinLength == passMaxLength: return 'have a length of exactly {0}'.format(passMaxLength)
        else: return 'have a length of {0} - {1}'.format(passMinLength, passMaxLength)
            
    def get_password(self, passType):
        passOriginal = ''
        passConfirm = ''

        if not passType in PasswordTypes:
            raise ValueError("Invalid password type specified to request from user.")
            exit(1)

        if passType == PasswordTypes.PIN_FIXED_4:
            passMinLength = 4
            passMaxLength = 4
            msgOriginal = 'Enter a 4 digit pin code (contains only numbers 0 - 9): '
            msgConfirm = 'Re-enter your 4 digit pin code to confirm: '
            pattern = '^\d{{{0},{1}}}\Z'.format(passMinLength, passMaxLength)
            passRegex = re.compile(pattern)
            formatError = 'Password has incorrect format. It must contain only numbers and {0}.'.format(self.length_msg(passMinLength, passMinLength))
        elif passType == PasswordTypes.MIXED_FIXED_8:
            passMinLength = 8
            passMaxLength = 8
            msgOriginal = 'Enter an 8 character password (contains letters and numbers, case ignored): '
            msgConfirm = 'Re-enter your 8 character password to confirm: '
            pattern = '^\w{{{0},{1}}}\Z'.format(passMinLength, passMaxLength)
            passRegex = re.compile(pattern)
            formatError = 'Password has incorrect format. It must contain only letters and numbers and {0}.'.format(length_msg(passMinLength, passMinLength))

        while True:
            passOriginal = getpass.getpass(msgOriginal)

            if(passRegex.match(passOriginal)):
                passReady = False
                passConfirm = getpass.getpass(msgConfirm)

                if passOriginal == passConfirm: 
                    print('Password OK.')
                    return passOriginal
                else: print('Confirmation does not match, try again.')
            else: print(formatError)

    def start_fresh_instance(self):
        helpers.print_dashes()
        print('Welcome to KEEGLogger! This is a demostration of password cracking that uses your brainwave data to infer keystrokes.\nTo begin you will need to create a username and choose a password mode.')    
        helpers.print_dashes()

        print('\nStep 1:')
        helpers.print_dashes()
        print('Enter a username (may contain only letters and numbers and {0}).'.format(self.length_msg(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)) + ' Note: if you don\'t want to have your data saved, press ENTER to skip this step and use the default profile. Your data will not be kept.')
        while True:
            username = input('Enter username: ').strip()
            if not self.validate_username(username):
                self.print_cannot_create_user()
            elif self.check_user_exists(username):
                ok = input('User: {0} already exists, type "OK" to activate this profile: '.format(username)).strip()
                if ok.upper() == 'OK': break
                else: print('OK not entered, please enter a new username.')
            else: 
                self.create_user(username)
                print('User: {0} created.'.format(username))
                break
        self.set_active_user(username)
        self.print_active_user()

        print('\nStep 2:')
        helpers.print_dashes()
        print('Enter a mode number: Enter "1" for Mode 1: cracking 4-digit pin number. Enter "2" for Mode 2: 8 character password (case insensitive).')
        while True:
            modeNumber = input('Enter mode number: ').strip()
            if PasswordTypes.has_value(helpers.safe_cast(modeNumber, int)):
               break
            else: 
                self.print_invalid_mode()

        modeNumber = PasswordTypes(int(modeNumber))
        self.set_active_mode(modeNumber)
        self.print_active_mode()
        password = self.get_password(modeNumber)
        self.write_password(username, password, modeNumber)

        print('\nStep 3:')
        helpers.print_dashes()
        self.begin_collection()

        print('\nStep 4:')
        helpers.print_dashes()
        print('''Congratulations, you have finished your data collection session. You can now let the learning model train on your data.
If you have done many session this process may take a bit of time.''')
        input('\nPress any key to start...')
        # Train

    def start_stream(self):
        os = platform.platform()
        pro = None
        if os == "linux" or os == "linux2":
            if self.museID:
                pro = subprocess.Popen('muse-lsl.py -a={0}'.format(self.museID), shell=True)
            else:
                pro = subprocess.Popen('muse-lsl.py', shell=True)
            programText = 'muse-lsl'
        else:
            if self.museID:
                subprocess.call('start bluemuse://start?addresses='.format(self.museID), shell=True)
            else:
                subprocess.call('start bluemuse://start?streamfirst=true'.format(self.museID), shell=True)
            programText = 'Blue Muse'
        print('\nThe system will now launch {0} to stream your EEG data.'.format(programText))
        return pro

    def stop_stream(self, process):
        os = platform.platform()
        if os == "linux" or os == "linux2":
            if pro:
                os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
        else:
            if self.museID:
                subprocess.call('start bluemuse://stop?addresses='.format(self.museID), shell=True)
            else:
                subprocess.call('start bluemuse://stop?stopall=true'.format(self.museID), shell=True)

    def begin_collection(self):
        user = self.get_active_user()
        mode = self.get_active_mode()
        print('''You are ready to start a data collection session {0}. 
\nIn this session you will be presented with {1} automatically generated "password(s)".
\nYour task is to simpy type each password as it is presented. If you make a mistake do not worry, just keep typing until you hit the correct key. Take  your time and remember to concentrate!'''.format(user, Constants.SESSION_ITERATIONS))        
        streamProcess = self.start_stream()
        input('\nPress any key to begin...')
        datacollection = DataCollection(user, mode, Constants.SESSION_ITERATIONS)
        datacollection.start()
        self.stop_stream(streamProcess)

    def begin_prediction(self):
        try:
            user, mode = self.get_active_user(), self.get_active_mode()
            password = self.get_user_password(self.get_active_user(), PasswordTypes(mode))
        except configparser.NoOptionError:
            print('Cannot begin prediction, password not set! User: {0}, Mode: {1}'.format(user, mode))
            exit(2)
        print('''You are ready for the prediction {0}. 
\nIn this session you will simply "login" by entering the password you set earlier.'''.format(user))
        streamProcess = self.start_stream()
        input('\nPress any key to begin...')
        prediction = Prediction(user, mode, password)
        prediction.start()
        self.stop_stream(streamProcess)
        
if __name__ == '__main__':
    Program()

