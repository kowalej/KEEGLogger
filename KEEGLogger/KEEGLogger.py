import sys
import getopt
import argparse
import re
import getpass
import configparser
import os
import helpers
import platform
import subprocess
import time
from experiment import Experiment
from password_types import PasswordTypes
from constants import Constants

class Program:
    def __init__(self):
        self.load_default_config()
        parser = argparse.ArgumentParser(
            description='KEEGLogger is a demostration of password cracking that uses your brainwave data to infer keystrokes.',
            usage='''KEEGLogger.py <command> [<args>]
    These are the commands:
    startfresh     Starts a new instance with step by step instructions.
    createuser     Creates a new user. Must run this before activateuser, if user doesn't yet exist.
    activateuser   Sets the active user.
    activatemode   Sets the active mode (i.e. password type).
    setpass        Records a new password (note: this is optional and used only for display during prediction).
    train          Train the model. You will type in passwords while your EEG data is recorded.
    predict        You will type a password and the model will predict it based soley on EEG data.

    Upon first use just run "startfresh" and follow the step by step instructions.

    Password modes: 
        Mode 1:  4-digit pin number.
        Mode 2: 8 character password.
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

    def load_default_config(self):
        if not os.path.isfile(Constants.CONFIG_FILE_NAME):
            config = configparser.ConfigParser()
            config.read(Constants.DEFAULT_CONFIG_FILE_NAME)
            cfgfile = open(Constants.CONFIG_FILE_NAME,'w')
            config.write(cfgfile)
            cfgfile.close()

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

    def train(self):
        parser = argparse.ArgumentParser(description='Train the model. You will type in passwords while your EEG data is recorded.')
        parser.add_argument('-mid', '--museid', type=int, required=False, help='Muse MAC Address. If ommitted, the first available device is used.')
        args = parser.parse_args(sys.argv[2:])
        if args.museid:
            self.museID = args.museid
        else:
           self.museID = None
        self.begin_experiment()

    def validate_username(self, username):
        pattern = '^\w{{{0},{1}}}\Z'.format(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)
        passRegex = re.compile(pattern)
        return passRegex.match(username)

    def create_user(self, username):
        self.write_config(Constants.CONFIG_USERNAME_PREFIX + username)

    def read_config(self, file = Constants.CONFIG_FILE_NAME):
        config = configparser.ConfigParser()
        config.read(file)
        return config

    def write_config(self, section, option = None, value = None, file = Constants.CONFIG_FILE_NAME):
        config = configparser.ConfigParser()
        config.read(file)
        if not config.has_section(section):
            config.add_section(section)
        if not option == None and not value == None:
            config.set(section, option, str(value))
        cfgfile = open(Constants.CONFIG_FILE_NAME,'w')
        config.write(cfgfile)
        cfgfile.close()

    def check_user_exists(self, username):
        return self.read_config().has_section(Constants.CONFIG_USERNAME_PREFIX + username)

    def get_user_list(self):
        users = list(filter(lambda x: Constants.CONFIG_USERNAME_PREFIX in x, self.read_config().sections()))
        return list(map(lambda x: x.replace(Constants.CONFIG_USERNAME_PREFIX,''), users))

    def get_active_user(self):
        return self.read_config().get(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_USER)

    def set_active_user(self, username):
        self.write_config(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_USER, username)

    def get_active_mode(self):
        return PasswordTypes(int(self.read_config().get(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_MODE)))

    def set_active_mode(self, mode):
        self.write_config(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_MODE, mode.value)

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
        self.write_config(Constants.CONFIG_USERNAME_PREFIX + username, Constants.CONFIG_PASSWORD_PREFIX + str(mode), password)
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
        self.begin_experiment()

    def begin_experiment(self):
        user = self.get_active_user()
        mode = self.get_active_mode()
        print('''You are ready to start training {0}. In this session you will be presented with {1} automatically generated passwords.
Your task is simpy to type each password as it is presented. If you make a mistake do not worry, just keep typing until you hit the correct key. Take  your time and remember to concentrate!'''.format(user, Constants.SESSION_ITERATIONS))        
        
        print('\nThe system will now launch muse-lsl (Linux) or BlueMuse (Windows) to stream data.')
        
        os = platform.platform()
        if os == "linux" or os == "linux2":
            if self.museID:
                subprocess.call('muse-lsl.py -a={0}'.format(self.museID), shell=True)
            else:
                subprocess.call('muse-lsl.py', shell=True)
        else:
            if self.museID:
                subprocess.call('start bluemuse://start?addresses='.format(self.museID), shell=True)
            else:
                subprocess.call('start bluemuse://start?streamfirst=true'.format(self.museID), shell=True)

        input('\nPress any key to begin...')
        Experiment(user, mode, Constants.SESSION_ITERATIONS)

if __name__ == '__main__':
    Program()

