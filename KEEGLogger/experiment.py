import pygame
import random
from passwordtypes import PasswordTypes

class Experiment:
    def __init__(self, user, mode, iterations):
        pygame.init()
        self.width = 600
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.totalIterations = iterations
        self.currentIteration = 0
        self.passwords = self.generate_passwords(mode, iterations)
        for i in range(iterations):
            print(self.passwords[i])
        self.currentPasswordIndex = 0
        self.currentCharIndex = 0

        running = True

        while running:
            self.screen.fill((255,255,255))
            self.draw_ui()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        print('Forward')
                    elif event.key == pygame.K_s:
                        print('Backward')
                elif event.type == pygame.QUIT:
                    pygame.quit()
            pygame.display.flip()

    def generate_passwords(self, mode, iterations):
        passwords = [''] * iterations
        if mode == PasswordTypes.PIN_FIXED_4:
            length = 4
            pool = '0123456789'
        elif mode == PasswordTypes.MIXED_FIXED_8:
            length = 8
            pool = 'abcdefghijklmnopqrstuvwxyz'
        for i in range(iterations):
            for j in range(length):
                passwords[i] += random.choice(pool)
        return passwords

    def draw_ui(self):
        font = pygame.font.Font(None, 40)
        passEnt = 'Passwords Entered: '
        passEntS = font.render(passEnt, 1, (0,0,0))
        iter = str(self.currentIteration) + ' / ' + str(self.totalIterations)
        iterS = font.render(iter, 1, (0,0,0))
        iterOffsetX = font.size(iter)[0] + 10
        self.screen.blit(passEntS, (self.width - iterOffsetX - font.size(passEnt)[0] - 10, 10))
        self.screen.blit(iterS, (self.width - iterOffsetX, 10))
