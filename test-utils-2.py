import utils_rs
import map_w
import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 500, 500
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Ray Casting")

a = utils_rs.Utils(map_w.MAP)

# Set up the clock to control the frame rate
clock = pygame.time.Clock()

width_tile = round(width / len(map_w.MAP[0]) / a.wall_width)
height_tile = round(height / len(map_w.MAP) / a.wall_height)

speed = 0.1

while True:
    a.bullet_tick()
    a.smoke_tick()
    a.flash_tick()
    ray_data = a.ray_fov(90, 180)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                a.fire_smoke()
            if event.key == pygame.K_e:
                a.fire_bullet()
            if event.key == pygame.K_q:
                a.fire_flash()

    changed = False
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        a.player_move(0, -speed)
        speed += 0.005
        speed = min(speed, 0.3)
        changed = True
    if keys[pygame.K_s]:
        a.player_move(0, speed)
        speed += 0.005
        speed = min(speed, 0.3)
        changed = True
    if keys[pygame.K_d]:
        a.player_move(speed, 0)
        speed += 0.005
        speed = min(speed, 0.3)
        changed = True
    if keys[pygame.K_a]:
        a.player_move(-speed, 0)
        speed += 0.005
        speed = min(speed, 0.3)
        changed = True
    if keys[pygame.K_LEFT]:
        a.set_rotation(a.players[a.turn].rotation + 20 % 360)
    if keys[pygame.K_RIGHT]:
        a.set_rotation(a.players[a.turn].rotation - 20 % 360)
    if not changed:
        speed = 0.1

    screen.fill((0, 0, 0))

    for i, row in enumerate(map_w.MAP):
        for j, col in enumerate(row):
            if col == 1:
                pygame.draw.rect(
                    screen,
                    (255, 255, 255),
                    pygame.Rect(
                        j * width_tile * a.wall_width,
                        i * height_tile * a.wall_height,
                        width_tile * a.wall_width,
                        height_tile * a.wall_height,
                    ),
                )

    for player in a.players:
        pygame.draw.rect(
            screen,
            (255, 0, 0) if not player.flashed else (0, 255, 0),
            pygame.Rect(
                player.x * width_tile * a.player_width,
                player.y * height_tile * a.player_height,
                width_tile * a.player_width,
                height_tile * a.player_height,
            ),
        )
        forward = a.forward(player.rotation)
        pygame.draw.line(
            screen,
            (255, 0, 0),
            (
                player.x * width_tile * a.player_width,
                player.y * height_tile * a.player_height,
            ),
            (
                (player.x + forward[0] * 1.5) * width_tile * a.player_width,
                (player.y + forward[1] * 1.5) * height_tile * a.player_height,
            ),
        )

    for smoke in a.smokes:
        if smoke.opened:
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (
                    smoke.x * width_tile,
                    smoke.y * height_tile,
                ),
                smoke.radius * width_tile,
            )
        else:
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (
                    smoke.x * width_tile,
                    smoke.y * height_tile,
                ),
                1,
            )

    for bullet in a.bullets:
        pygame.draw.circle(
            screen,
            (0, 0, 255),
            (
                bullet.x * width_tile,
                bullet.y * height_tile,
            ),
            1,
        )

    for flash in a.flashes:
        pygame.draw.circle(
            screen,
            (0, 255, 0),
            (
                flash.x * width_tile,
                flash.y * height_tile,
            ),
            1,
        )

    hits = a.get_players_hit_by_bullet()
    if len(hits) > 0:
        a = utils_rs.Utils(map_w.MAP)

    pygame.display.flip()

    clock.tick(15)
