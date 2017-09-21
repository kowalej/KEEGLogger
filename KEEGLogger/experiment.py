import pygame

class Experiment:
    def __init__(self, user, mode, iterations):
        pygame.init()
        width = 300
        height = 300
        screen = pygame.display.set_mode((width, height))
        screen.fill((255,255,255))
        
        font = pygame.font.Font(None, 30)
        text = '''Password: '''
        textImg = font.render(text, 1, (255,0,0))
        screen.blit(textImg, (width - 50, 10))

        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        print('Forward')
                    elif event.key == pygame.K_s:
                        print('Backward')
