import numpy as np
import pygame

import gymnasium as gym
from gymnasium import spaces

import utils_rs
import map_w


class ShooterEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(self, render_mode=None, start_model=None):
        self.selfplay = start_model
        self.window_size = 500
        self.utils = utils_rs.Utils(map_w.MAP)
        self.iters = 0

        self.observation_space = spaces.Box(-np.inf, np.inf, (386,))
        self.action_space = spaces.Box(-np.inf, np.inf, (12,))

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

        self.window = None
        self.clock = None

    def _get_obs(self):
        obs = []
        ray_data = self.utils.ray_fov(90, 180)
        for ray in ray_data:
            obs.extend([ray[0], ray[1]])
        obs.extend(
            [
                self.utils.players[self.utils.turn].rotation,
                self.utils.players[self.utils.turn].ammo,
            ]
        )
        for i in range(10):
            if i < len(self.utils.players[self.utils.turn].memory_keys):
                obs.extend(
                    [
                        self.utils.players[self.utils.turn].memory_keys[i],
                        self.utils.players[self.utils.turn].memory_values[i],
                    ]
                )
            else:
                obs.extend(
                    [
                        0,
                        0,
                    ]
                )
        obs.extend(
            [
                self.utils.players[self.utils.turn].sound,
                self.utils.players[self.utils.turn].smokes,
                self.utils.players[self.utils.turn].flashes,
                self.utils.players[self.utils.turn].flashed,
            ]
        )

        return obs

    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        self.iters = 0
        self.utils = utils_rs.Utils(map_w.MAP)

        observation = self._get_obs()

        if self.render_mode == "human":
            self._render_frame()

        return observation, {}

    def process_action(self, action):
        self.utils.bullet_tick()
        self.utils.smoke_tick()
        self.utils.flash_tick()

        if action[2] > 0:  # should i move
            self.utils.player_move(action[0], action[1])
        if action[3] > 0:
            self.utils.fire_bullet()
        if action[5] > 0:
            self.utils.set_rotation(
                (self.utils.players[self.utils.turn].rotation + action[4]) % 360
            )
        if action[7] > 0:
            mem_values = self.utils.players[self.utils.turn].memory_values
            mem_keys = self.utils.players[self.utils.turn].memory_keys
            mem_values.insert(0, action[9])
            mem_keys.insert(0, action[8])
            if len(mem_values) > 10:
                mem_values.pop()
                mem_keys.pop()
            self.utils.set_memory_values(mem_values)
            self.utils.set_memory_keys(mem_keys)
        if action[10] > 0:
            self.utils.fire_smoke()
        if action[11] > 0:
            self.utils.fire_flash()

    def step(self, action):
        self.iters += 1
        self.process_action(action)

        reward = 0

        hits = self.utils.get_players_hit_by_bullet()
        done = len(hits) > 0

        if not done:
            self.utils.next_turn()
            if self.selfplay is None:
                self.process_action(self.action_space.sample())
            else:
                self.process_action(self.selfplay.predict(self._get_obs()))
            hits = self.utils.get_players_hit_by_bullet()
            done = len(hits) > 0

            if done:
                if 0 in hits:
                    reward -= 100
                else:
                    reward += 100
            self.utils.next_turn()
        else:
            if 0 in hits:
                reward -= 100
            else:
                reward += 100

        observation = self._get_obs()

        if self.iters > 1000:
            done = True

        if self.render_mode == "human":
            self._render_frame()

        return observation, reward, done, False, {}

    def render(self):
        if self.render_mode == "rgb_array":
            return self._render_frame()

    def _render_frame(self):
        width_tile = round(self.window_size / len(map_w.MAP[0]) / self.utils.wall_width)
        height_tile = round(self.window_size / len(map_w.MAP) / self.utils.wall_height)

        if self.window is None and self.render_mode == "human":
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.window_size, self.window_size))
        if self.clock is None and self.render_mode == "human":
            self.clock = pygame.time.Clock()

        screen = pygame.Surface((self.window_size, self.window_size))
        screen.fill((0, 0, 0))

        for i, row in enumerate(map_w.MAP):
            for j, col in enumerate(row):
                if col == 1:
                    pygame.draw.rect(
                        screen,
                        (255, 255, 255),
                        pygame.Rect(
                            j * width_tile * self.utils.wall_width,
                            i * height_tile * self.utils.wall_height,
                            width_tile * self.utils.wall_width,
                            height_tile * self.utils.wall_height,
                        ),
                    )

        for player in self.utils.players:
            pygame.draw.rect(
                screen,
                (255, 0, 0) if not player.flashed else (0, 255, 0),
                pygame.Rect(
                    player.x * width_tile * self.utils.player_width,
                    player.y * height_tile * self.utils.player_height,
                    width_tile * self.utils.player_width,
                    height_tile * self.utils.player_height,
                ),
            )
            forward = self.utils.forward(player.rotation)
            pygame.draw.line(
                screen,
                (255, 0, 0),
                (
                    player.x * width_tile * self.utils.player_width,
                    player.y * height_tile * self.utils.player_height,
                ),
                (
                    (player.x + forward[0] * 1.5)
                    * width_tile
                    * self.utils.player_width,
                    (player.y + forward[1] * 1.5)
                    * height_tile
                    * self.utils.player_height,
                ),
            )

        for smoke in self.utils.smokes:
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

        for bullet in self.utils.bullets:
            pygame.draw.circle(
                screen,
                (0, 0, 255),
                (
                    bullet.x * width_tile,
                    bullet.y * height_tile,
                ),
                1,
            )

        for flash in self.utils.flashes:
            pygame.draw.circle(
                screen,
                (0, 255, 0),
                (
                    flash.x * width_tile,
                    flash.y * height_tile,
                ),
                1,
            )

        if self.render_mode == "human":
            # The following line copies our drawings from `canvas` to the visible window
            self.window.blit(screen, screen.get_rect())
            pygame.event.pump()
            pygame.display.update()

            # We need to ensure that human-rendering occurs at the predefined framerate.
            # The following line will automatically add self.utils delay to keep the framerate stable.
            self.clock.tick(self.metadata["render_fps"])
        else:  # rgb_array
            return np.transpose(
                np.array(pygame.surfarray.pixels3d(screen)), axes=(1, 0, 2)
            )


'''env = ShooterEnv(render_mode="human")
while True:
    obs, rew, done, _, _ = env.step(env.action_space.sample())
    if done:
        if rew == 0:
            env.reset()
        else:
            print(rew)
            break'''
