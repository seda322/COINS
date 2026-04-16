import pygame
import math
from logic.assets.sprite_pygame import PygameSprite


class Tornado(PygameSprite):
    def __init__(self, x: float, y: float, textures: list, sound, scale: float = 1.0, world_scale: float = 1.0,
                 world_width: int = 1920):
        start_texture = None
        self.textures = textures

        if self.textures:
            start_texture = self.textures[0]
        else:
            start_texture = pygame.Surface((100, 100), pygame.SRCALPHA)
            start_texture.fill((100, 100, 255))
            self.texture = start_texture

        super().__init__(image=start_texture, scale=scale)

        self.center_x = x
        self.center_y = y

        if sound:
            sound.play()

        self.duration = 7.8
        self.timer = 0.0

        self.anim_speed = 0.05
        self.frame_index = 0
        self.anim_timer = 0.0

        self.pull_radius = (world_width / 4.0) * world_scale
        self.pull_strength = 2000.0 * world_scale
        self.spin_strength = 750.0 * world_scale

        self.fade_duration = 0.5

    def update(self, dt: float) -> bool:
        self.timer += dt

        alpha = 255
        if self.timer < self.fade_duration:
            alpha = int(255 * (self.timer / self.fade_duration))
        elif self.timer > self.duration - self.fade_duration:
            alpha = int(255 * ((self.duration - self.timer) / self.fade_duration))
        self.alpha = alpha

        if self.textures and len(self.textures) > 1:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.frame_index = (self.frame_index - 1) % len(self.textures)
                self.texture = self.textures[self.frame_index]

        if self.timer >= self.duration:
            return False
        return True

    def affect_coin(self, coin, dt):
        if not hasattr(coin, 'vx'): return
        if coin.wisp_immunity_timer > 0: return

        suction_point_x = self.center_x
        suction_point_y = self.bottom

        dx = suction_point_x - coin.sprite.center_x
        dy = suction_point_y - coin.sprite.center_y
        dist_sq = dx * dx + dy * dy
        is_inside = dist_sq < (self.pull_radius * self.pull_radius)

        if is_inside:
            dist = math.sqrt(dist_sq)
            if dist == 0: dist = 0.001

            nx = dx / dist
            ny = dy / dist

            progress = 1.0 - (dist / self.pull_radius)

            # === УЧЕТ МАССЫ ===
            # Тяжелые монеты всасываются медленнее (сила делится на массу)
            mass_factor = 1.0 / coin.mass

            pull_force = self.pull_strength * progress * mass_factor
            spin_force = self.spin_strength * progress * mass_factor

            coin.vx += (nx * pull_force - ny * spin_force) * dt
            coin.vy += (ny * pull_force + nx * spin_force) * dt

            coin.tornado_hit = True

        else:
            if coin.tornado_hit:
                coin.tornado_hit = False
                coin.vx *= 0.8
                coin.vy *= 0.8

    def draw(self, surface, screen_height) -> None:
        super().draw(surface, screen_height)