import os
import configparser
import pandas as pd
import glob
import ntpath
from datetime import datetime
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

def load_all_users_data(passwordType, rootFolder = 'session_data', startDateTime = datetime.min, endDateTime = datetime.max):
    load_user_data('**', passwordType, rootFolder, startDateTime, endDateTime)

def load_user_data(username, passwordType, rootFolder = 'session_data', startDateTime = datetime.min, endDateTime = datetime.max):
    if(type(passwordType) is int):
        passwordTypeStr = PasswordTypes(passwordType).name
    else: 
        passwordTypeStr = passwordType.name
    folder = '{0}/{1}/{2}'.format(rootFolder, username, passwordTypeStr)
    print('Searching folder {0} for sessions date/time range Start: {1} - End: {2}'.format(folder, startDateTime, endDateTime))
    for filePath in glob.iglob(folder + '/*_MRK.csv', recursive=False):
        fileName = ntpath.basename(filePath)
        timestampsStr = fileName.replace(username + '_' + passwordTypeStr + '_', '').replace('_MRK.csv', '').split('_')
        timestamps = [datetime.strptime(timestampsStr[0], Constants.SESSION_FILE_DATETIME_FORMAT), datetime.strptime(timestampsStr[1], Constants.SESSION_FILE_DATETIME_FORMAT)]
        dfMrk = None
        dfEEG = None
        if(timestamps[0] >= startDateTime and timestamps[1] <= endDateTime):
            print('[Found session] Start: {0} - End: {1}'.format(str(timestamps[0]), str(timestamps[1])))
            mrkFile = filePath
            eegFile = filePath.replace('_MRK.csv', '_EEG.csv')
            dfMrkn = pd.read_csv(mrkFile, float_precision='round_trip')
            dfEEGn = pd.read_csv(eegFile, float_precision='round_trip')
            if dfMrk: dfMrk.append(dfMrkn)
            else: dfMrk = dfMrkn
            
            if dfEEG: dfEEG.append(dfEEGn)
            else: dfEEG = dfEEGn



