import os
import configparser
import pandas
from constants import Constants
from password_types import PasswordTypes

def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default

def print_dashes(dashes = 40, rows = 1):
    dashText = ''
    for i in range(dashes): dashText += '-'
    for i in range(rows):
        print(dashText)
        
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_default_config(cfgFileName = Constants.CONFIG_FILE_NAME, defaultCfgFileName = Constants.DEFAULT_CONFIG_FILE_NAME):
    if not os.path.isfile(cfgFileName):
        config = configparser.ConfigParser()
        config.read(defaultCfgFileName)
        cfgfile = open(cfgFileName,'w')
        config.write(cfgfile)
        cfgfile.close()

def read_config(cfgFileName = Constants.CONFIG_FILE_NAME):
    config = configparser.ConfigParser()
    config.read(cfgFileName)
    return config

def write_config(section, option = None, value = None, cfgFileName = Constants.CONFIG_FILE_NAME):
    config = configparser.ConfigParser()
    config.read(cfgFileName)
    if not config.has_section(section):
        config.add_section(section)
    if not option == None and not value == None:
        config.set(section, option, str(value))
    cfgfile = open(cfgFileName, 'w')
    config.write(cfgfile)
    cfgfile.close()

def load_user_data(username, passwordType, rootFolder = 'session_data', use_legacy = False):
    if legacy:
        rootFolder += '/legacy-eeg-timestamps-utc-is-est'

    folder = '{0}/{1}/{2}'.format(rootFolder, username, str(passwordType))




