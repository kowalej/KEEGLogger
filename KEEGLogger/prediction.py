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

class PredictionState(Enum):
    MUSE_DISCONNECTED = 0
    RUNNING = 1
    FINISHED = 2

class Prediction:
    def __init__(self, user, mode, password, museID = 'Default'):
        self.user = user
        self.password = password
        self.museID = museID
        pygame.init()
        self.width = 600
        self.height = 600
        pygame.display.set_caption(user + ' Prediction Session')
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.mode = mode
        self.inputSize = (300, 60)
        self.inputPosition = (self.width/2 - self.inputSize[0]/2, self.height/2 - self.inputSize[1]/2)
        font = pygame.font.Font(None, 50)
        inputRect = pygame.Rect(self.inputPosition[0], self.inputPosition[1], self.inputSize[0], self.inputSize[1])
        self.input = TextBox(inputRect, clear_on_enter=True, inactive_on_enter=False, font=font)
        self.gameRunning = False
        self.state = PredictionState.MUSE_DISCONNECTED # 0 = Muse Disconnected, 1 = Session Running, 2 = Finished 
        self.setup_marker_streaming()
        self.markers = [[]] # Each item is array of 2 items - timestamp + the key which was pressed.
        self.eegData = [[]] # Each item is array of timestamp + data for each channel.
        self.get_eeg_stream(0.5)
        self.startTime = time() # Timestamp of experiment start.
        self.finishTime = 0 # Timestamp of experiment finish.
        self.lastEEGSampleTime = self.startTime

    def setup_marker_streaming(self):
        streamName = self.user + ' Prediction Session Markers'
        self.markerInfo = StreamInfo(streamName, 'Keystroke Markers', 1, 0, 'string', str(uuid.uuid1()))
        self.markerOutlet = StreamOutlet(self.markerInfo)

    def get_eeg_stream(self, timeout):
        eeg_inlet_streams : StreamInlet = resolve_byprop('type', 'EEG', timeout=timeout)
        for stream in eeg_inlet_streams:
            if self.museID == 'Default' or not stream.name().find(self.museID) == -1:
                self.eegInlet = StreamInlet(stream)
                self.eegTimeCorrection = self.eegInlet.time_correction()
                self.state = PredictionState.RUNNING
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

    def check_password(self):
        passwordInput = ''.join(str(x) for x in self.input.buffer)
        if passwordInput == self.password:
            print('correct!')
        else: print('incorrect!')
        print(passwordInput)

    def draw_static_ui(self):
        fontPassEnt = pygame.font.Font(None, 40)
        
        if self.state == PredictionState.RUNNING:
            instruct = self.user + ' type your password below, press ENTER when done:'
        elif self.state == PredictionState.MUSE_DISCONNECTED:
            instruct = 'Error: a Muse LSL stream must be active to continue (Muse ID: {0})'.format(self.museID)
        else:
            instruct = 'Finished session. This window will close in a moment.'
        
        fontInstruct = pygame.font.Font(None, 24)
        instructS = fontInstruct.render(instruct, 1, (0,0,0))
        instructSize = fontInstruct.size(instruct)
        self.screen.blit(instructS, (self.width/2 - instructSize[0]/2, self.height/4 - instructSize[1]/2))

    def process_input(self):
        for event in pygame.event.get():
            if self.state == PredictionState.RUNNING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.check_password()
                    self.input.get_event(event)
            if event.type == pygame.QUIT: 
                pygame.quit()

    def process_logic(self):
        if self.state == PredictionState.MUSE_DISCONNECTED:
            if self.doneCheckEEG == True:
                self.doneCheckEEG = False
                threading.Thread(target = self.get_eeg_stream,  kwargs={'timeout' : 5}).start()
        elif self.state == PredictionState.RUNNING:
            self.pull_eeg_data()
        elif self.state == PredictionState.FINISHED:
            if self.finishTime == 0:
                self.finishTime = time()
                self.save_data()
            if time() - self.finishTime >= 3:
                self.gameRunning = False
        self.input.update()

    def draw(self):
        self.screen.fill((255,255,255))
        self.draw_static_ui()
        if self.state == PredictionState.RUNNING:
            self.input.draw(self.screen)
        pygame.display.flip()
    
    def start(self):
        self.gameRunning = True
        while self.gameRunning:
            self.process_input()
            self.process_logic()
            self.draw()
        pygame.quit()


