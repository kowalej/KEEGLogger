#!/usr/bin/python

import sys
import getopt
import argparse
import re
import getpass
import configparser
import os
import helpers
from enum import Enum

class Constants(object):
    CONFIG_FILE_NAME = 'config.ini'
    DEFAULT_CONFIG_FILE_NAME = 'default_config.ini'
    CONFIG_SECTION_GLOBAL = 'Global'
    CONFIG_OPTION_ACTIVE_USER = 'ActiveUser'
    CONFIG_OPTION_ACTIVE_MODE = 'ActiveMode'
    CONFIG_USERNAME_PREFIX = 'User_'
    CONFIG_PASSWORD_PREFIX = 'Password_'
    USERNAME_MIN_LENGTH = 1
    USERNAME_MAX_LENGTH = 10

class PasswordTypes(Enum):
    PIN_FIXED_4 = 1
    MIXED_FIXED_8 = 2
    
    @classmethod
    def has_value(self, value):
        return (any(value == item.value for item in self))

class Program():
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
    train          Train the model. You will type in words while your data EEG is recorded.
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
        self.start_fresh_instance()

    def createuser(self):
        parser = argparse.ArgumentParser(description='Create a new user profile.')
        parser.add_argument('username', type=str, help='Valid username, It must contain only letters and numbers and {0}.'.format(self.length_msg(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)))
        parser.add_argument('-a', '--activate', action='store_true', default=True, required=False, help='Set as active user after creation.')
        args = parser.parse_args(sys.argv[2:])
        if not self.validate_username(args.username):
            print('Cannot create user.')
            print('Username has incorrect format. It must contain only letters and numbers and {0}.'.format(self.length_msg(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)))
            return
        elif self.check_user_exists(args.username):
            print('User already exists, will activate if -a/--activate was provided.')
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
            print('Active user set to: {0}.'.format(args.username))

    def activatemode(self):
        parser = argparse.ArgumentParser(description='Set active mode.')
        parser.add_argument('mode', type=int, help='Password mode number to activate.')
        args = parser.parse_args(sys.argv[2:])
        if not PasswordTypes.has_value(args.mode):
            self.print_invalid_mode()
        else: 
            self.set_active_mode(args.mode)
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
        self.write_config(Constants.CONFIG_SECTION_GLOBAL, Constants.CONFIG_OPTION_ACTIVE_MODE, mode)

    def print_users(self):
        users = self.get_user_list()
        print('Total users: {0}'.format(len(users)))
        print(*self.get_user_list(), sep='\n')

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
        print('--------------------------------')
        print('Enter a username (may contain only letters and numbers and {0}).'.format(self.length_msg(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)) + ' Note: if you don\'t want to have your data saved, press enter to skip this step and use the default profile. Your data will not be kept.')
        while True:
            username = input('Enter username: ').strip()
            if not self.validate_username(username):
                print('Cannot create user.')
                print('Username has incorrect format. It must contain only letters and numbers and {0}.'.format(self.length_msg(Constants.USERNAME_MIN_LENGTH, Constants.USERNAME_MAX_LENGTH)))
            elif self.check_user_exists(username):
                ok = input('User: {0} already exists, type "OK" to activate this profile: '.format(username)).strip()
                if ok.upper() == 'OK': break
                else: print('OK not entered, please enter a new username.')
            else: 
                self.create_user(username)
                print('User: {0} created.'.format(username))
                break
        self.set_active_user(username)
        print('User: {0} activated.'.format(username))

        print('\nStep 2:')
        print('--------------------------------')
        print('Enter a mode number: Type "1" for Mode 1 - cracking 4-digit pin number. Type "2" for Mode 2 - 8 character password.')
        while True:
            modeNumber = input('Enter mode number: ').strip()
            if PasswordTypes.has_value(helpers.safe_cast(modeNumber, int)):
               self.begin_mode(modeNumber)
               break
            else: 
                self.print_invalid_mode()

    def begin_mode(self, passType):
        password = self.get_password(PasswordTypes.PIN)
        #begin_training(30)

if __name__ == '__main__':
    Program()

