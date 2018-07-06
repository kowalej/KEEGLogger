from time import time, sleep
from pylsl import StreamInfo, StreamOutlet
import pygatt
import subprocess
from sys import platform
from muselsl import helper
from muselsl.muse import Muse
from muselsl.constants import MUSE_NB_CHANNELS, MUSE_SAMPLING_RATE, MUSE_SCAN_TIMEOUT, LSL_CHUNK, AUTO_DISCONNECT_DELAY
from muselsl.stream import list_muses, find_muse

# Begins an LSL stream containing EEG data from a Muse with a given address
def stream(address, backend='auto', interface=None, name=None, unmanaged=False):
    bluemuse = backend == 'bluemuse'
    if not bluemuse:
        if not address:
            found_muse = find_muse(name)
            if not found_muse:
                return
            else:
                address = found_muse['address']
                name = found_muse['name']

        info = StreamInfo('Muse', 'EEG', MUSE_NB_CHANNELS, MUSE_SAMPLING_RATE, 'float32',
                          'Muse%s' % address)

        info.desc().append_child_value("manufacturer", "Muse")
        channels = info.desc().append_child("channels")

        for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
            channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "EEG")

        outlet = StreamOutlet(info, LSL_CHUNK)

        def push_eeg(data, timestamps):
            for ii in range(LSL_CHUNK):
                outlet.push_sample(data[:, ii], timestamps[ii])

        muse = Muse(address=address, callback_eeg=push_eeg,
                    backend=backend, interface=interface, name=name)

    # Barebones version for BlueMuse.
    else:
        muse = Muse(address=address, callback_eeg=None,
                    backend=backend, interface=interface, name=name)

    if(bluemuse):
        muse.connect()
        if not address and not name:
            print('Targeting first device BlueMuse discovers...')
        else:
            print('Targeting device: ' + ':'.join(filter(None, [name, address])) + '...')
        print('\n*BlueMuse will auto connect and stream when the device is found. \n*You can also use the BlueMuse interface to manage your stream(s).')
        muse.start()
        return muse # BlueMuse can always just return muse object.

    didConnect = muse.connect()

    if(didConnect):
        print('Connected.')
        muse.start()
        print('Streaming...')
        if(unmanaged):
            return muse
        
        while time() - muse.last_timestamp < AUTO_DISCONNECT_DELAY:
            try:
                sleep(1)
            except KeyboardInterrupt:
                muse.stop()
                muse.disconnect()
                break

        print('Disconnected.')

