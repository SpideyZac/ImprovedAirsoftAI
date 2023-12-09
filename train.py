from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecVideoRecorder
import wandb
from wandb.integration.sb3 import WandbCallback
import time

import env as e

config = {
    "policy_type": "MlpPolicy",
    "total_timesteps": 5000,
    "env_name": "Airsoft",
}

run = wandb.init(
    project="AirsoftAI",
    config=config,
    sync_tensorboard=True,
    monitor_gym=True,
    save_code=True
)

import random
from collections import deque
import os

models_dir = "models/PPO"

if not os.path.exists(models_dir):
    os.makedirs(models_dir)

TIMESTEPS = 50_000

def make_env():
    env = e.ShooterEnv(render_mode="rgb_array")
    env = Monitor(env)
    return env

env = DummyVecEnv([make_env])
env = VecVideoRecorder(
    env,
    f"videos/{run.id}",
    record_video_trigger=lambda x: x % 10000 == 0,
    video_length=300,
)

model = PPO('MlpPolicy', env, verbose=2, tensorboard_log=f"runs/${run.id}")
'''custom = {
    "tensorboard_log": f"runs/${run.id}"
}
model = PPO.load("models\\u3jcd8tv\\model.zip", env, custom_objects=custom)'''

models = deque([], 10)

for i in range(25):
    model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, callback=
        WandbCallback(
            gradient_save_freq=100,
            model_save_path=f"models/{run.id}",
            verbose=2,
        ),
    )
    t = time.time()
    model.save(f"{models_dir}/{t}")
    print("SAVED")
    models.append(PPO.load(f"{models_dir}/{t}", env))

    if random.random() <= 0.5:
        env.selfplay = models[-1]
    else:
        env.selfplay = random.choice(models)

    print(env.selfplay, models)

run.finish()