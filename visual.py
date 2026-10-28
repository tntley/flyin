import pygame
import sys

pygame.init()

screen = pygame.display.set_mode((1500, 800), pygame.RESIZABLE)
pygame.display.set_caption("Trying")

color = (200, 10, 255)

background = pygame.image.load('background.png')

screen.blit(background)
pygame.draw.line(screen, color, (200+100/2, 350+150/2), (1000, 200), 5)
pygame.draw.rect(screen, color, (200, 350, 100, 150))
pygame.draw.circle(screen, (0,0,250), (1000, 200), 100)
pygame.display.flip()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                sys.exit()
pygame.quit()
