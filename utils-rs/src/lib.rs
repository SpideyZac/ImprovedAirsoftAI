use libm::{cos, fabs, pow, sin, sqrt};
use pyo3::prelude::*;

#[pyclass]
struct LoggingStdout;

#[pymethods]
impl LoggingStdout {
    fn write(&self, data: &str) {
        print!("{}", data);
    }
}

#[pyclass]
#[derive(Clone)]
struct Bullet {
    #[pyo3(get)]
    pub x: f64,
    #[pyo3(get)]
    pub y: f64,
    #[pyo3(get)]
    pub rotation: f64,
    pub fired_by: usize,
}

#[pyclass]
#[derive(Clone)]
struct Player {
    #[pyo3(get)]
    pub x: f64,
    #[pyo3(get)]
    pub y: f64,
    #[pyo3(get)]
    pub rotation: f64,
    #[pyo3(get)]
    pub ammo: u8,
    #[pyo3(get)]
    pub sound: f64,
    #[pyo3(get)]
    pub memory_values: Vec<f64>,
    #[pyo3(get)]
    pub memory_keys: Vec<f64>,
    #[pyo3(get)]
    pub smokes: u8,
}

#[pyclass]
#[derive(Clone)]
struct Smoke {
    #[pyo3(get)]
    pub x: f64,
    #[pyo3(get)]
    pub y: f64,
    #[pyo3(get)]
    pub radius: f64,
    pub rotation: f64,
    pub frames_moved: u8,
    #[pyo3(get)]
    pub opened: bool,
    pub frames_opened: u8,
}

#[pyclass]
struct Utils {
    #[pyo3(get)]
    pub walls: Vec<Vec<u8>>,
    #[pyo3(get)]
    pub wall_width: u8,
    #[pyo3(get)]
    pub wall_height: u8,
    #[pyo3(get)]
    pub bullets: Vec<Bullet>,
    #[pyo3(get)]
    pub player_width: u8,
    #[pyo3(get)]
    pub player_height: u8,
    #[pyo3(get)]
    pub ammo_total: u8,
    #[pyo3(get)]
    pub players: Vec<Player>,
    #[pyo3(get)]
    pub turn: usize,
    #[pyo3(get)]
    pub smokes: Vec<Smoke>,
    #[pyo3(get)]
    pub smokes_radius: f64,
    pub smokes_max_move: u8,
    pub smokes_max_open: u8,
}

#[pymethods]
impl Utils {
    #[new]
    fn new(walls: Vec<Vec<u8>>) -> Self {
        Self {
            walls,
            wall_width: 1,
            wall_height: 1,
            bullets: Vec::new(),
            player_width: 1,
            player_height: 1,
            ammo_total: 30,
            players: vec![
                Player {
                    x: 9.0,
                    y: 11.0,
                    rotation: 270.0,
                    ammo: 30,
                    sound: 0.0,
                    memory_values: Vec::new(),
                    memory_keys: Vec::new(),
                    smokes: 3,
                },
                Player {
                    x: 1.0,
                    y: 1.0,
                    rotation: 90.0,
                    ammo: 30,
                    sound: 0.0,
                    memory_values: Vec::new(),
                    memory_keys: Vec::new(),
                    smokes: 3,
                },
            ],
            turn: 0,
            smokes: vec![],
            smokes_radius: 4.0,
            smokes_max_move: 5,
            smokes_max_open: 180,
        }
    }

    fn colliding(
        &self,
        x: f64,
        y: f64,
        width: u8,
        height: u8,
        x2: f64,
        y2: f64,
        width2: u8,
        height2: u8,
    ) -> bool {
        let x_collision = (fabs(x - x2) * 2.0) < (width + width2) as f64;
        let y_collision = (fabs(y - y2) * 2.0) < (height + height2) as f64;
        x_collision && y_collision
    }

    fn colliding_circle(
        &self,
        x: f64,
        y: f64,
        width: u8,
        height: u8,
        x2: f64,
        y2: f64,
        radius: f64,
    ) -> bool {
        let mut test_x = x2;
        let mut test_y = y2;

        if x2 < x {
            test_x = x;
        } else if x2 > x + width as f64 {
            test_x = x + width as f64;
        }

        if y2 < y {
            test_y = y;
        } else if y2 > y + height as f64 {
            test_y = y + height as f64;
        }

        let distance = self.distance(x2, y2, test_x, test_y);
        if distance < radius {
            return true;
        }

        false
    }

    fn is_colliding_with_wall(&self, x: f64, y: f64, width: u8, height: u8) -> (bool, f64, f64) {
        for y2 in 0..self.walls.len() {
            for x2 in 0..self.walls[y2].len() {
                if self.walls[y2][x2] == 1 {
                    let collide = self.colliding(
                        x,
                        y,
                        width,
                        height,
                        x2 as f64 * self.wall_width as f64,
                        y2 as f64 * self.wall_height as f64,
                        self.wall_width,
                        self.wall_height,
                    );

                    if collide {
                        return (collide, x2 as f64, y2 as f64);
                    }
                }
            }
        }

        (false, 0.0, 0.0)
    }

    fn is_colliding_with_player(
        &self,
        player: Player,
        x: f64,
        y: f64,
        width: u8,
        height: u8,
    ) -> bool {
        self.colliding(
            x,
            y,
            width,
            height,
            player.x,
            player.y,
            self.player_width,
            self.player_height,
        )
    }

    fn is_colliding_with_any_player(
        &self,
        x: f64,
        y: f64,
        width: u8,
        height: u8,
    ) -> (bool, f64, f64) {
        for player in self.players.iter() {
            let colliding = self.colliding(
                x,
                y,
                width,
                height,
                player.x,
                player.y,
                self.player_width,
                self.player_height,
            );

            if colliding {
                return (colliding, player.x, player.y);
            }
        }

        (false, 0.0, 0.0)
    }

    fn is_colliding_with_smoke(&self, x: f64, y: f64, width: u8, height: u8) -> (bool, f64, f64) {
        for smoke in self.smokes.iter() {
            if smoke.opened {
                let colliding = self.colliding_circle(
                    x,
                    y,
                    width,
                    height,
                    smoke.x,
                    smoke.y,
                    self.smokes_radius,
                );

                if colliding {
                    return (colliding, smoke.x, smoke.y);
                }
            }
        }

        (false, 0.0, 0.0)
    }

    fn is_smoke_colliding_with_wall(&self, x: f64, y: f64) -> bool {
        for y2 in 0..self.walls.len() {
            for x2 in 0..self.walls[y2].len() {
                if self.walls[y2][x2] == 1 {
                    let x2_f = x2 as f64 * self.wall_width as f64;
                    let y2_f = y2 as f64 * self.wall_height as f64;

                    let mut test_x = x;
                    let mut test_y = x;

                    if x < x2_f {
                        test_x = x;
                    } else if x > x2_f + self.wall_width as f64 {
                        test_x = x2_f + self.wall_width as f64;
                    }

                    if y < y2_f {
                        test_y = y2_f;
                    } else if y > y2_f + self.wall_height as f64 {
                        test_y = y2_f + self.wall_height as f64;
                    }

                    let distance = self.distance(x, y, test_x, test_y);
                    if distance < 0.1 {
                        return true;
                    }
                }
            }
        }

        false
    }

    fn player_move(&mut self, controller_x: f64, controller_y: f64) {
        self.players[self.turn].x += controller_x.min(1.0).max(-1.0);
        self.players[self.turn].y += controller_y.min(1.0).max(-1.0);

        for (i, player) in self.players.iter().enumerate() {
            if i != self.turn {
                if self
                    .is_colliding_with_wall(
                        self.players[self.turn].x,
                        self.players[self.turn].y,
                        self.player_width,
                        self.player_height,
                    )
                    .0
                    || self.is_colliding_with_player(
                        player.clone(),
                        self.players[self.turn].x,
                        self.players[self.turn].y,
                        self.player_width,
                        self.player_height,
                    )
                {
                    self.players[self.turn].x -= controller_x.min(1.0).max(-1.0);
                    self.players[self.turn].y -= controller_y.min(1.0).max(-1.0);
                    break;
                }
            }
        }
    }

    fn forward(&self, rot: f64) -> (f64, f64) {
        (sin(rot.to_radians()), cos(rot.to_radians()))
    }

    fn fire_bullet(&mut self) {
        if self.players[self.turn].ammo > 0 {
            self.bullets.push(Bullet {
                x: self.players[self.turn].x,
                y: self.players[self.turn].y,
                rotation: self.players[self.turn].rotation,
                fired_by: self.turn,
            });
            self.players[self.turn].ammo -= 1;
        }
    }

    fn bullet_tick(&mut self) {
        let mut bullets: Vec<Bullet> = vec![];

        for i in 0..self.bullets.len() {
            let forward = self.forward(self.bullets[i].rotation);

            self.bullets[i].x += forward.0;
            self.bullets[i].y += forward.1;

            bullets.push(self.bullets[i].clone());

            if self
                .is_colliding_with_wall(self.bullets[i].x, self.bullets[i].y, 1, 1)
                .0
            {
                bullets.pop();
            }
        }

        self.bullets = bullets;
    }

    fn get_players_hit_by_bullet(&mut self) -> Vec<usize> {
        let mut players_hit = vec![];

        for i in 0..self.players.len() {
            for j in 0..self.bullets.len() {
                if self.bullets[j].fired_by != i {
                    if self.is_colliding_with_player(
                        self.players[i].clone(),
                        self.bullets[j].x,
                        self.bullets[j].y,
                        1,
                        1,
                    ) {
                        players_hit.push(i);
                    }
                }
            }
        }

        players_hit
    }

    fn next_turn(&mut self) {
        self.turn = (self.turn + 1) % self.players.len();
    }

    fn distance(&self, x: f64, y: f64, x2: f64, y2: f64) -> f64 {
        sqrt(pow(x - x2, 2.0) + pow(y - y2, 2.0))
    }

    fn ray(&self, x: f64, y: f64, rotation: f64) -> (f64, u8) {
        let forward = self.forward(rotation);

        let mut x_cur = x;
        let mut y_cur = y;

        loop {
            x_cur += forward.0;
            y_cur += forward.1;

            let collision_wall = self.is_colliding_with_wall(x_cur, y_cur, 1, 1);
            if collision_wall.0 {
                return (self.distance(x, y, collision_wall.1, collision_wall.2), 0);
            }

            let collision_player = self.is_colliding_with_any_player(x_cur, y_cur, 1, 1);
            if collision_player.0 {
                if !self.is_colliding_with_player(
                    self.players[self.turn].clone(),
                    x_cur,
                    y_cur,
                    1,
                    1,
                ) {
                    return (
                        self.distance(x, y, collision_player.1, collision_player.2),
                        1,
                    );
                }
            }

            let collision_smoke = self.is_colliding_with_smoke(x_cur, y_cur, 1, 1);
            if collision_smoke.0 {
                return (self.distance(x, y, collision_smoke.1, collision_smoke.2), 2);
            }
        }
    }

    fn ray_fov(&self, fov: f64, number_of_rays: f64) -> Vec<(f64, u8)> {
        let mut results = vec![];
        let mut rotation_traveled = 0.0;
        let rotation_per = fov / number_of_rays;
        let half = fov / 2.0;
        let mut count = -half;

        while rotation_traveled < fov {
            results.push(self.ray(
                self.players[self.turn].x,
                self.players[self.turn].y,
                self.players[self.turn].rotation + count,
            ));
            count += rotation_per;
            rotation_traveled += rotation_per;
        }

        results
    }

    fn fire_smoke(&mut self) {
        if self.players[self.turn].smokes > 0 {
            self.smokes.push(Smoke {
                x: self.players[self.turn].x,
                y: self.players[self.turn].y,
                radius: self.smokes_radius,
                rotation: self.players[self.turn].rotation,
                frames_moved: 0,
                opened: false,
                frames_opened: 0,
            });
            self.players[self.turn].smokes -= 1;
        }
    }

    fn smoke_tick(&mut self) {
        let mut smokes: Vec<Smoke> = vec![];

        for i in 0..self.smokes.len() {
            if self.smokes[i].frames_moved < self.smokes_max_move && !self.smokes[i].opened {
                let forward = self.forward(self.smokes[i].rotation);
                self.smokes[i].frames_moved += 1;

                self.smokes[i].x += forward.0;
                self.smokes[i].y += forward.1;

                if self.is_smoke_colliding_with_wall(self.smokes[i].x, self.smokes[i].y) {
                    self.smokes[i].x -= forward.0;
                    self.smokes[i].y -= forward.1;
                    self.smokes[i].frames_moved = self.smokes_max_move;
                }

                smokes.push(self.smokes[i].clone());
            } else if self.smokes[i].opened {
                self.smokes[i].frames_opened += 1;
                smokes.push(self.smokes[i].clone());

                if self.smokes[i].frames_opened > self.smokes_max_open {
                    smokes.pop();
                }
            } else {
                self.smokes[i].opened = true;
                smokes.push(self.smokes[i].clone());
            }
        }

        self.smokes = smokes;
    }

    fn set_rotation(&mut self, rotation: f64) {
        self.players[self.turn].rotation = rotation
    }

    fn set_sound(&mut self, sound: f64) {
        self.players[self.turn].sound = sound
    }

    fn set_memory_values(&mut self, value: Vec<f64>) {
        self.players[self.turn].memory_values = value;
    }

    fn set_memory_keys(&mut self, value: Vec<f64>) {
        self.players[self.turn].memory_keys = value;
    }
}

#[pymodule]
fn utils_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    //let sys = _py.import("sys")?;
    //sys.setattr("stdout", LoggingStdout.into_py(_py))?;
    m.add_class::<Utils>()?;
    Ok(())
}
