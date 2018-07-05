import glob
import pandas as pd

# EEG timestamps are in Unix epoch millisecond format and incorrectly use EST timezone, but we need to normalize to GMT.

est_to_gmt_shift = 3600*1000*4 # 3600 seconds in an hour, 1000 ms in a second, and we shift 4 hours to get from EST to GMT

def shift_timezone(timestamp, shift = est_to_gmt_shift):
    return timestamp + shift

def ms_to_sec(timestamp):
    return timestamp / 1000.

#for filename in glob.iglob('session_data/**/*_EEG.csv', recursive=True):
#     print('Fixing timestamps (ms -> s) converting: ' + filename)

#     df = pd.read_csv(filename, float_precision='round_trip')
#     df['timestamp'] = df['timestamp'].apply(ms_to_sec, 1)
#     df.to_csv(filename, index=False)

#for filename in glob.iglob('session_data/**/*_EEG.csv', recursive=True):
#     print('fixing timestamps converting: ' + filename)

#     df = pd.read_csv(filename, float_precision='round_trip')
#     df['timestamp'] = df['timestamp'].apply(shift_timezone, 1)
#     df.to_csv(filename, index=False)

#for filename in glob.iglob('session_data/**/*_MRK.csv', recursive=True):
#     print('Remove extra line: ' + filename)
#     df = pd.read_csv(filename, float_precision='round_trip')
#     df.to_csv(filename, index=False)

c = input('Press any key to exit...')