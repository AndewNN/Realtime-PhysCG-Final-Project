import pygame as pg
import numpy as np
from ui import UI, get_screen_resolution
import time

# pygame setup
pg.init()
# screen = pg.display.set_mode((1280, 720), pg.SCALED)
flags = pg.SCALED
screen = pg.display.set_mode((1800, 1000), flags)
pg.display.set_caption("Cloth Simulation")

background = pg.Surface(screen.get_size())
background = background.convert()
background.fill((0, 0, 0))

mainUI = UI(screen)

clock = pg.time.Clock()
running = True
dt = 0

st = time.time()

while running:
    # poll for events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
            if event.key == pg.K_SPACE:
                # cloth.toggle_pause()
                pass
            if event.key == pg.K_r:
                # cloth.reset()
                pass
            if event.key == pg.K_u:
                mainUI.toggle_parameters()
        mainUI.handle_event(event)

    # fill the screen with a color to wipe away anything from last frame
    screen.blit(background, (0, 0))

    mainUI.update()
    mainUI.draw()

    pg.display.flip()

    tt = time.time()
    print("FPS: ", 1 / (tt - st))
    st = tt

    # Limit framerate
    # clock.tick(100)

pg.quit()