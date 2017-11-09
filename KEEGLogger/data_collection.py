import pygame
import random
import math
from password_types import PasswordTypes
from textbox import TextBox
from time import time, strftime, gmtime, sleep, mktime
import datetime
import uuid
import asyncio
import threading
import csv
import helpers
import os
from pylsl import StreamInfo, StreamOutlet, LostError
from enum import Enum
from pylsl import StreamInlet, resolve_byprop

class DataCollectionState(Enum):
    MUSE_DISCONNECTED = 0
    RUNNING = 1
    FINISHED = 2

class DataCollection:
    def __init__(self, user, mode, iterations, museID = None):
        self.user = user
        self.museID = museID
        pygame.init()
        self.width = 600
        self.height = 600
        pygame.display.set_caption(user + ' Data Collection Session')
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.totalIterations = iterations
        self.passwords = self.generate_passwords(mode, iterations)
        self.mode = mode
        self.currentPassIndex = 0
        self.currentCharIndex = 0
        self.donePass = False
        self.inputSize = (300, 60)
        self.inputPosition = (self.width/2 - self.inputSize[0]/2, self.height/2 - self.inputSize[1]/2)
        font = pygame.font.Font(None, 50)
        inputRect = pygame.Rect(self.inputPosition[0], self.inputPosition[1], self.inputSize[0], self.inputSize[1])
        self.input = TextBox(inputRect, clear_on_enter=True, inactive_on_enter=False, font=font)
        self.gameRunning = False
        self.state = DataCollectionState.MUSE_DISCONNECTED # 0 = Muse Disconnected, 1 = Session Running, 2 = Finished 
        self.setup_marker_streaming()
        self.markers = [[]] # Each item is array of 2 items - timestamp + the key which was pressed.
        self.eegData = [[]] # Each item is array of timestamp + data for each channel.
        self.get_eeg_stream(0.5)
        self.startTime = time() # Timestamp of experiment start.
        self.finishTime = 0 # Timestamp of experiment finish.
        self.lastEEGSampleTime = self.startTime

    def setup_marker_streaming(self):
        streamName = self.user + ' Training Session Markers'
        self.markerInfo = StreamInfo(streamName, 'Keystroke Markers', 1, 0, 'string', str(uuid.uuid1()))
        self.markerOutlet = StreamOutlet(self.markerInfo)

    def get_eeg_stream(self, timeout):
        eeg_inlet_streams : StreamInlet = resolve_byprop('type', 'EEG', timeout=timeout)
        for stream in eeg_inlet_streams:
            if self.museID == None or not stream.name().find(self.museID) == -1:
                self.eegInlet = StreamInlet(stream)
                self.eegTimeCorrection = self.eegInlet.time_correction()
                self.state = DataCollectionState.RUNNING
        self.doneCheckEEG = True

    def push_marker(self, timestamp, currentChar):
        self.markerOutlet.push_sample(currentChar, timestamp) # Push key marker with timestamp via LSL for other programs.
        self.markers.append([timestamp, currentChar])

    def pull_eeg_data(self, timeout = 0.0, max_samples = 360):
        samples, timestamps = self.eegInlet.pull_chunk(timeout, max_samples) # Pull samples.
        timestampCount = len(timestamps)
        if(timestampCount > 0):
            print('Number of samples: {0} | Time since last: {1}'.format(timestampCount, time() - self.lastEEGSampleTime))
            self.lastEEGSampleTime = time()
            for i in range(0, len(timestamps)):
                self.eegData.append([timestamps[i]] + samples[i])

    def save_data(self):
        info = self.eegInlet.info()
        desc = info.desc()
        chanNum = info.channel_count()

        channels = desc.child('channels').first_child()
        channelNames = [channels.child_value('label')]
        for i in range(1, chanNum):
            channels = channels.next_sibling()
            channelNames.append(channels.child_value('label'))
                
        startTime = datetime.datetime.fromtimestamp(self.startTime).strftime('%Y-%m-%d-%H-%M-%S')
        finishTime = datetime.datetime.fromtimestamp(self.finishTime).strftime('%Y-%m-%d-%H-%M-%S')

        # Save EEG Data
        fileBase = os.path.join('session_data', self.user, self.mode.name, self.user + '_' + self.mode.name + '_' + startTime + '_' + finishTime)
        file = fileBase + '_EEG.csv'
        helpers.ensure_dir(file)
        with open(file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['timestamp'] + channelNames)
            for data in self.eegData:
                writer.writerow(data)
        print('Saved EEG data to: ' + file)

        # Save Marker Data
        file = os.path.join('session_data', self.user, self.mode.name, self.user + '_' + self.mode.name + '_' + startTime + '_' + finishTime).replace(':','\ua789')
        file = fileBase + '_MRK.csv'
        helpers.ensure_dir(file)
        with open(file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['timestamp','key marker'])
            for data in self.markers:
                writer.writerow(data)
        print('Saved Marker data to: ' + file)

    def generate_passwords(self, mode, iterations):
        passwords = [''] * iterations
        if mode == PasswordTypes.PIN_FIXED_4:
            length = 4
            poolInit = '0123456789'
        elif mode == PasswordTypes.MIXED_FIXED_8:
            length = 8
            poolInit = 'abcdefghijklmnopqrstuvwxyz'

        pool = poolInit

        # Calculate number of each character required for even distribution.
        freq = math.floor(iterations * length / len(pool))
        poolTrack = [freq] * len(pool) # Keeps track of how many of each letter has been  used.

        for i in range(iterations):
            for j in range(length):
                if len(poolTrack) != 0:
                    index = random.randint(0, len(poolTrack) - 1)
                    char = pool[index]
                    poolTrack[index] -= 1
                    if poolTrack[index] == 0:
                        poolTrack.pop(index)
                        pool = pool.replace(char,'')
                # Once we've used the minimum required "freq" of each character, we simply do a random choice from the initial pool.
                else: char = random.choice(poolInit) 
                passwords[i] += char.upper()
        return passwords

    def draw_static_ui(self):
        fontPassEnt = pygame.font.Font(None, 40)
        passEnt = 'Passwords Entered: '
        passEntS = fontPassEnt.render(passEnt, 1, (0,0,0))
        iter = str(self.currentPassIndex) + ' / ' + str(self.totalIterations)
        iterS = fontPassEnt.render(iter, 1, (0,0,0))
        iterOffsetX = fontPassEnt.size(iter)[0] + 10
        self.screen.blit(passEntS, (self.width - iterOffsetX - fontPassEnt.size(passEnt)[0] - 10, 10))
        self.screen.blit(iterS, (self.width - iterOffsetX, 10))

        if self.state == DataCollectionState.RUNNING:
            instruct = 'Type the password below, press ENTER when done:'
        elif self.state == DataCollectionState.MUSE_DISCONNECTED:
            instruct = 'Error: a Muse LSL stream must be active to continue (Muse ID: {0})'.format(self.museID)
        else:
            instruct = 'Finished session. This window will close in a moment.'
        
        fontInstruct = pygame.font.Font(None, 24)
        instructS = fontInstruct.render(instruct, 1, (0,0,0))
        instructSize = fontInstruct.size(instruct)
        self.screen.blit(instructS, (self.width/2 - instructSize[0]/2, self.height/4 - instructSize[1]/2))

    def process_input(self):
        for event in pygame.event.get():
            if self.state == DataCollectionState.RUNNING:
                currentPass = self.passwords[self.currentPassIndex]
                currentChar = currentPass[self.currentCharIndex]
                if event.type == pygame.KEYDOWN:
                    if (event.key == ord(currentChar) or event.key == ord(currentChar.lower())) and not self.donePass:
                        newEvent = pygame.event.Event(pygame.KEYDOWN, {'unicode': currentChar.upper(),'key': ord(currentChar.upper()), 'mod': None})
                        self.input.get_event(newEvent)
                        self.push_marker(float(time()), currentChar)
                        if self.currentCharIndex < len(currentPass) - 1:
                            self.currentCharIndex += 1
                        else: self.donePass = True
                    elif event.key == pygame.K_RETURN and self.donePass:
                        self.currentCharIndex = 0
                        self.currentPassIndex += 1
                        if self.currentPassIndex == self.totalIterations:
                            self.state = DataCollectionState.FINISHED
                        self.input.get_event(event)
                        self.donePass = False
            if event.type == pygame.QUIT: 
                pygame.quit()
          
    def process_logic(self):
        if self.state == DataCollectionState.MUSE_DISCONNECTED:
            if self.doneCheckEEG == True:
                self.doneCheckEEG = False
                threading.Thread(target = self.get_eeg_stream,  kwargs={'timeout' : 5}).start()
        elif self.state == DataCollectionState.RUNNING:
            self.pull_eeg_data()
        elif self.state == DataCollectionState.FINISHED:
            if self.finishTime == 0:
                self.finishTime = time()
                self.save_data()
            if time() - self.finishTime >= 3:
                self.gameRunning = False
        self.input.update()

    def draw_password(self):
        font = pygame.font.Font(None, 50)
        password = self.passwords[self.currentPassIndex]
        passwordS = font.render(password, 1, (0,0,0))
        passwordSize = font.size(password)
        self.screen.blit(passwordS, (self.inputPosition[0], self.height/2 - passwordSize[1]/2 - self.inputSize[1]))

    def draw(self):
        self.screen.fill((255,255,255))
        self.draw_static_ui()
        if self.state == DataCollectionState.RUNNING:
            self.draw_password()
            self.input.draw(self.screen)
        pygame.display.flip()
    
    def start(self):
        self.gameRunning = True
        while self.gameRunning:
            self.process_input()
            self.process_logic()
            self.draw()
        pygame.quit()

