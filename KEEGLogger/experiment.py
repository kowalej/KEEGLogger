import pygame
import random
import math
from password_types import PasswordTypes
from textbox import TextBox
from time import time, strftime, gmtime
import uuid
import asyncio
import threading
from pylsl import StreamInfo, StreamOutlet
from enum import Enum
from pylsl import StreamInlet, resolve_byprop

class ExperimentState(Enum):
    MUSE_DISCONNECTED = 0
    RUNNING = 1
    FINISHED = 2

class Experiment:
    def __init__(self, user, mode, iterations, museID = 'Default'):
        self.user = user
        self.museID = museID
        pygame.init()
        self.width = 600
        self.height = 600
        pygame.display.set_caption(user + ' Training Session')
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.totalIterations = iterations
        self.passwords = self.generate_passwords(mode, iterations)
        self.currentPassIndex = 0
        self.currentCharIndex = 0
        self.donePass = False
        self.inputSize = (300, 60)
        self.inputPosition = (self.width/2 - self.inputSize[0]/2, self.height/2 - self.inputSize[1]/2)
        font = pygame.font.Font(None, 50)
        inputRect = pygame.Rect(self.inputPosition[0], self.inputPosition[1], self.inputSize[0], self.inputSize[1])
        self.input = TextBox(inputRect, clear_on_enter=True, inactive_on_enter=False, font=font)
        self.gameRunning = False
        self.state = ExperimentState.MUSE_DISCONNECTED # 0 = Muse Disconnected, 1 = Session Running, 2 = Finished 
        self.setup_streaming()
        self.get_eeg_stream(0.5)
        self.finishTime = 0
        self.start()

    def setup_streaming(self):
        # Setup LSL marker stream
        streamName = self.user + ' Training Session Markers'
        self.info = StreamInfo(streamName, 'Keystroke Markers', 1, 0, 'string', str(uuid.uuid1()))
        self.marker_outlet = StreamOutlet(self.info)

        marker_inlet_streams : StreamInlet = resolve_byprop('name', streamName, timeout=0.5)
        if marker_inlet_streams:
            self.marker_inlet = StreamInlet(marker_inlet_streams[0])
            self.marker_time_correction = self.marker_inlet.time_correction()
        else:
            raise(RuntimeError, "Cant find EEG marker stream!")

    def get_eeg_stream(self, timeout):
        eeg_inlet_streams : StreamInlet = resolve_byprop('type', 'EEG', timeout=timeout)
        for stream in eeg_inlet_streams:
            if self.museID == 'Default' or not stream.name().find(self.museID) == -1:
                self.eeg_inlet = StreamInlet(stream)
                self.eeg_time_correction = self.eeg_inlet.time_correction()
                self.state = ExperimentState.RUNNING
        self.done_check_eeg = True

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

        if self.state == ExperimentState.RUNNING:
            instruct = 'Type the password below, press ENTER when done:'
        elif self.state == ExperimentState.MUSE_DISCONNECTED:
            instruct = 'A Muse LSL stream must be active to continue (Muse ID: {0})'.format(self.museID)
        else:
            instruct = 'Finished session. This window will close in a moment.'
        
        fontInstruct = pygame.font.Font(None, 24)
        instructS = fontInstruct.render(instruct, 1, (0,0,0))
        instructSize = fontInstruct.size(instruct)
        self.screen.blit(instructS, (self.width/2 - instructSize[0]/2, self.height/4 - instructSize[1]/2))

    def process_input(self):
        for event in pygame.event.get():
            if self.state == ExperimentState.RUNNING:
                currentPass = self.passwords[self.currentPassIndex]
                currentChar = currentPass[self.currentCharIndex]
                if event.type == pygame.KEYDOWN:
                    if (event.key == ord(currentChar) or event.key == ord(currentChar.lower())) and not self.donePass:
                        newEvent = pygame.event.Event(pygame.KEYDOWN, {'unicode': currentChar.upper(),'key': ord(currentChar.upper()), 'mod': None})
                        self.input.get_event(newEvent)
                        if self.currentCharIndex < len(currentPass) - 1:
                            self.marker_outlet.push_sample(currentChar, float(time())) # Push key with timestamp.
                            self.currentCharIndex += 1
                        else: self.donePass = True
                    elif event.key == pygame.K_RETURN and self.donePass:
                        self.currentCharIndex = 0
                        self.currentPassIndex += 1
                        if self.currentPassIndex == self.totalIterations:
                            self.state = ExperimentState.FINISHED
                        self.input.get_event(event)
                        self.donePass = False
            if event.type == pygame.QUIT: 
                pygame.quit()
          
    def process_logic(self):
        if self.state == ExperimentState.MUSE_DISCONNECTED:
            if self.done_check_eeg == True:
                self.done_check_eeg = False
                threading.Thread(target = self.get_eeg_stream,  kwargs={'timeout' : 5}).start()
        #elif self.state == ExperimentState.RUNNING:

        elif self.state == ExperimentState.FINISHED:
            if self.finishTime == 0:
                self.finishTime = time()
            if time() - self.finishTime >= 3:
                exit()
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
        if self.state == ExperimentState.RUNNING:
            self.draw_password()
            self.input.draw(self.screen)
        pygame.display.flip()
    
    def start(self):
        self.gameRunning = True
        while self.gameRunning:
            self.process_input()
            self.process_logic()
            self.draw()

