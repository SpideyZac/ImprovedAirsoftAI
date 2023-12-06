import utils_rs
import map_w
import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Ray Casting')

a = utils_rs.Utils(map_w.MAP)
a.fire_smoke()
a.smoke_tick()
a.smoke_tick()
a.smoke_tick()
a.smoke_tick()
a.smoke_tick()
a.smoke_tick()
a.smoke_tick()
ray_data = a.ray_fov(90, 180)
rot = a.players[a.turn].rotation

# Set up colors
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Set up the clock to control the frame rate
clock = pygame.time.Clock()

# Convert angle to radians
def to_radians(angle_degrees):
    return math.radians(angle_degrees)

# Initial position
x, y = width // 2, height // 2

# Draw each ray segment separately with its color
angle = -45
zoom_factor = 1.0
import timeit
timeit.template = """
def inner(_it, _timer{init}):
    {setup}
    _t0 = _timer()
    for _i in _it:
        retval = {stmt}
    _t1 = _timer()
    return _t1 - _t0, retval
"""

while True:
    pygame.time.wait(100)
    a.smoke_tick()
    timer = timeit.Timer("a.ray_fov(90, 180)", globals=globals())
    time, ray_data = timer.timeit(number=1)
    print(time)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Zoom in with the '+' key
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_w:
            zoom_factor *= 1.1
        # Zoom out with the '-' key
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            zoom_factor /= 1.1


    # Clear the screen
    screen.fill((255, 255, 255))
    angle = -45

    # Draw each ray segment
    for distance, ray_type in ray_data:
        angle_rad = to_radians(angle + rot)
        end_x = x + distance * math.sin(angle_rad) * zoom_factor
        end_y = y + distance * math.cos(angle_rad) * zoom_factor

        # Choose color based on ray_type
        if ray_type == 1:
            color = RED
        elif ray_type == 0:
            color = BLUE 
        else:
            color = GREEN

        # Draw the current ray segment
        pygame.draw.line(screen, color, (x, y), (end_x, end_y), 1)

        angle += 0.5  # Assuming rotation_per is defined in your code

    # Update the display
    pygame.display.flip()

    # Control the frame rate
    clock.tick(60)