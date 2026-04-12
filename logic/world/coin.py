from logic.assets.sprite_pygame import PygameSprite
import random
import math
import pygame


class Coin:
    def __init__(
            self,
            x: float,
            y: float,
            sprites: dict,
            value: int,
            scale: float = 1.0,
            scale_factor: float = 1.0
    ) -> None:
        self.value = value
        self.sprites = sprites
        self.scale = scale
        self.world_scale = scale_factor
        self.is_grabbed = False

        self.sprite = PygameSprite()
        self.sprite.center_x = x
        self.sprite.center_y = y

        # По умолчанию орел
        self.sprite.texture = sprites["heads"]
        self.sprite.scale = self.scale

        self.tornado_exit_time = 0.0
        self.radius = 32.0 * self.scale

        self.lifetime = None
        self.fade_duration = 2.0
        self.is_fading = False

        self.sprite.coin = self

        # Физика
        self.vx = 0.0
        self.vy = 0.0

        # Анимация полета
        self.anim = []
        self.anim_index = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.05

        # Для смены анимации в торнадо
        self._last_flying_direction = None

        # === ФИЗИКА ВРАЩЕНИЯ ===
        self.angle = 0.0
        self.angular_velocity = 0.0
        self.spin_friction = 0.90

        # Состояние
        self.is_moving = False
        self.last_outcome_value = 0
        self.landed = False
        self.fixed_outcome_texture = None

        # Сохраняем текущую сторону (орел/решка) для корректного подхвата
        self.current_face = "heads"

        self.needs_toss_sound = False
        self.explosion_chance = 0.0
        self.victims_to_flip = []
        self.just_landed = False

        self.wisp_immunity_timer = 0.0
        self.tornado_hit = False
        self.manual_override = False

        self.MAX_SPEED = 2500.0 * self.world_scale
        self.MAX_ANGULAR_VELOCITY = 25.0

    def update(self, dt: float, width: int, height: int, nearby_coins: list) -> None:
        if self.is_grabbed:
            self.angle += self.angular_velocity * dt
            if abs(self.angular_velocity) > 0.01:
                self.angular_velocity *= 0.90
            else:
                self.angular_velocity = 0
            return

        # --- Угасание ---
        if self.lifetime is not None and self.lifetime > 0:
            self.lifetime -= dt
            if self.lifetime <= self.fade_duration:
                self.is_fading = True
                ratio = max(0, self.lifetime / self.fade_duration)
                self.sprite.alpha = int(255 * ratio)
            if self.lifetime <= 0:
                return

        if self.wisp_immunity_timer > 0:
            self.wisp_immunity_timer -= dt
            if self.wisp_immunity_timer < 0:
                self.wisp_immunity_timer = 0

        # === ТОРНАДО: Переход в полет ===
        if not self.is_moving and self.tornado_hit:
            speed = math.hypot(self.vx, self.vy)
            if speed > 30.0:  # Порог взлета
                self.is_moving = True
                # ВАЖНО: Сразу выбираем анимацию
                self._select_flying_animation()

        # === ПОЛЕТ ===
        if self.is_moving:
            self.sprite.center_x += self.vx * dt
            self.sprite.center_y += self.vy * dt

            # ИСПРАВЛЕНИЕ: Воздушное трение (чтобы монетки падали, а не летели вечно)
            if not self.tornado_hit:
                self.vx *= 0.995
                self.vy *= 0.995

            self._clamp_speed()
            self._handle_wall_bounce(width, height)

            # Динамическая смена анимации (ТОРНАДО)
            if self.tornado_hit:
                self._update_flying_direction_dynamic()

            # Анимация
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.anim_index += 1
                if self.anim and self.anim_index < len(self.anim):
                    self.sprite.texture = self.anim[self.anim_index]
                else:
                    self.land()

        # === ЗЕМЛЯ ===
        else:
            current_friction = 0.93
            if self.tornado_exit_time > 0:
                current_friction = 0.985
                self.tornado_exit_time -= dt

            if self.tornado_hit:
                self.vx *= 0.96
                self.vy *= 0.96
            else:
                self.vx *= current_friction
                self.vy *= current_friction

            if abs(self.vx) < 0.5: self.vx = 0
            if abs(self.vy) < 0.5: self.vy = 0

            self.sprite.center_x += self.vx * dt
            self.sprite.center_y += self.vy * dt

            # Вращение
            self.angle += self.angular_velocity * dt
            if abs(self.angular_velocity) > 0.01:
                self.angular_velocity *= self.spin_friction
            else:
                self.angular_velocity = 0

            self._handle_collisions(nearby_coins)
            if not self.tornado_hit:
                self._handle_wall_bounce(width, height)

            self.check_land_event()

    def land(self) -> None:
        # ИСПРАВЛЕНИЕ: Если мы в торнадо, не приземляемся, а продолжаем анимацию
        if self.tornado_hit:
            self.anim_index = 0
            if not self.anim:
                self._select_flying_animation()
            return

        self.is_moving = False
        self.anim = []
        self.landed = True
        self.just_landed = True
        self.manual_override = False

        self.fixed_outcome_texture = None

        is_heads = random.random() < 0.5
        if is_heads:
            self.sprite.texture = self.sprites.get("heads")
            self.last_outcome_value = self.value
            self.current_face = "heads"
        else:
            self.sprite.texture = self.sprites.get("tails")
            self.last_outcome_value = 0
            self.current_face = "tails"

    def draw(self, surface, screen_height) -> None:
        if self.is_moving:
            # Тень для всех летящих монет
            if not self.is_grabbed:
                shadow_scale = 1.15
                shadow_radius = int(self.radius * shadow_scale)
                shadow_surf = pygame.Surface((shadow_radius * 2, shadow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(shadow_surf, (0, 0, 0, 60), (shadow_radius, shadow_radius), shadow_radius)

                offset = 15
                shadow_center_y = (screen_height - self.sprite.center_y) + offset
                draw_shadow_x = int(self.sprite.center_x - shadow_radius)
                draw_shadow_y = int(shadow_center_y - shadow_radius)
                surface.blit(shadow_surf, (draw_shadow_x, draw_shadow_y))

            self.sprite.draw(surface, screen_height)

        else:
            # ЗЕМЛЯ (Вращение)
            base_texture = self.sprite.texture
            angle_degrees = math.degrees(self.angle)
            rotated_texture = pygame.transform.rotate(base_texture, angle_degrees)
            rect = rotated_texture.get_rect()
            rect.center = (self.sprite.center_x, screen_height - self.sprite.center_y)
            surface.blit(rotated_texture, rect)

    def hit_by_coin(self, source_coin, nx, ny) -> None:
        self.is_moving = True
        self.vx = nx * (600 * self.world_scale)
        self.vy = ny * (600 * self.world_scale)
        self._select_flying_animation()
        self.anim_index = 0
        if self.anim:
            self.sprite.texture = self.anim[0]
        self.needs_toss_sound = True

    def hit(self, dx: int, dy: int) -> None:
        self.is_moving = True
        self.vx = 0
        self.vy = 0.0
        length = math.sqrt(dx * dx + dy * dy)
        dead_zone = self.radius * 0.2
        base_speed = 600 * self.world_scale
        if length < dead_zone:
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle) * base_speed
            self.vy = math.sin(angle) * base_speed
        else:
            if length > 0:
                self.vx = (-dx / length) * base_speed
                self.vy = (-dy / length) * base_speed
        self._select_flying_animation()
        self.anim_index = 0
        if self.anim:
            self.sprite.texture = self.anim[0]
        self.needs_toss_sound = True

    def check_land_event(self):
        val = self.last_outcome_value
        self.last_outcome_value = 0
        return val

    def _select_flying_animation(self):
        # ВОССТАНОВЛЕННАЯ ЛОГИКА (Классическая)
        if abs(self.vx) > 1.5 * abs(self.vy):
            self.anim = self.sprites.get("right", []) if self.vx > 0 else self.sprites.get("left", [])
        elif abs(self.vy) > 1.5 * abs(self.vx):
            self.anim = self.sprites.get("up", []) if self.vy > 0 else self.sprites.get("down", [])
        else:
            if self.vx > 0 and self.vy > 0:
                self.anim = self.sprites.get("up_right", [])
            elif self.vx > 0 and self.vy < 0:
                self.anim = self.sprites.get("down_right", [])
            elif self.vx < 0 and self.vy > 0:
                self.anim = self.sprites.get("up_left", [])
            else:
                self.anim = self.sprites.get("down_left", [])

        if not self.anim:
            # Fallback если папки нет
            if abs(self.vx) > abs(self.vy):
                self.anim = self.sprites.get("right", []) if self.vx > 0 else self.sprites.get("left", [])
            else:
                self.anim = self.sprites.get("up", []) if self.vy > 0 else self.sprites.get("down", [])

        if not self.anim:
            self.anim = [self.sprites.get("heads")]

    def _update_flying_direction_dynamic(self):
        """Динамическая смена анимации во время полета (для торнадо)"""
        new_anim = None

        if abs(self.vx) > 1.5 * abs(self.vy):
            new_anim = self.sprites.get("right" if self.vx > 0 else "left", [])
        elif abs(self.vy) > 1.5 * abs(self.vx):
            new_anim = self.sprites.get("up" if self.vy > 0 else "down", [])
        else:
            if self.vx > 0 and self.vy > 0:
                new_anim = self.sprites.get("up_right", [])
            elif self.vx > 0 and self.vy < 0:
                new_anim = self.sprites.get("down_right", [])
            elif self.vx < 0 and self.vy > 0:
                new_anim = self.sprites.get("up_left", [])
            else:
                new_anim = self.sprites.get("down_left", [])

        if new_anim and (not self.anim or new_anim[0] != self.anim[0]):
            self.anim = new_anim
            self.anim_index = 0

    def _handle_collisions(self, nearby_coins):
        for other in nearby_coins:
            if other is self: continue
            if other.is_moving: continue

            dx = self.sprite.center_x - other.sprite.center_x
            dy = self.sprite.center_y - other.sprite.center_y
            dist_sq = dx * dx + dy * dy
            min_dist = self.radius + other.radius

            if dist_sq < (min_dist * min_dist) and dist_sq > 0:
                dist = math.sqrt(dist_sq)
                overlap = min_dist - dist
                nx = dx / dist
                ny = dy / dist

                # 1. Раздвигаем
                max_instant_sep = 2.0
                sep_mag = min(overlap * 0.5, max_instant_sep)
                self.sprite.center_x += sep_mag * nx
                self.sprite.center_y += sep_mag * ny
                other.sprite.center_x -= sep_mag * nx
                other.sprite.center_y -= sep_mag * ny

                # 2. Импульс отталкивания
                stiffness = 4.8
                push = overlap * stiffness
                self.vx += nx * push
                self.vy += ny * push
                other.vx -= nx * push
                other.vy -= ny * push

                # 3. ФИЗИКА ВРАЩЕНИЯ
                dvx = self.vx - other.vx
                dvy = self.vy - other.vy
                tx = -ny
                ty = nx
                vel_along_tangent = dvx * tx + dvy * ty
                spin_impulse = vel_along_tangent * 0.01

                self.angular_velocity += spin_impulse
                other.angular_velocity -= spin_impulse

                impact_speed = math.sqrt(dvx ** 2 + dvy ** 2)

                if impact_speed < 40.0:
                    self.angular_velocity *= 0.5
                    other.angular_velocity *= 0.5

                self.angular_velocity = max(-self.MAX_ANGULAR_VELOCITY,
                                            min(self.MAX_ANGULAR_VELOCITY, self.angular_velocity))
                other.angular_velocity = max(-self.MAX_ANGULAR_VELOCITY,
                                             min(self.MAX_ANGULAR_VELOCITY, other.angular_velocity))

    def _clamp_speed(self):
        current_speed_sq = self.vx * self.vx + self.vy * self.vy
        if current_speed_sq > self.MAX_SPEED ** 2:
            current_speed = math.sqrt(current_speed_sq)
            ratio = self.MAX_SPEED / current_speed
            self.vx *= ratio
            self.vy *= ratio

    def _handle_wall_bounce(self, width, height):
        if self.is_grabbed: return
        hit_something = False

        if self.vx > 0:
            direction = 1
        elif self.vx < 0:
            direction = -1
        else:
            direction = 0

        if self.sprite.left < 0:
            self.sprite.left = 0
            self.vx *= -0.5
            hit_something = True
        elif self.sprite.right > width:
            self.sprite.right = width
            self.vx *= -0.5
            hit_something = True

        if self.sprite.bottom < 0:
            self.sprite.bottom = 0
            self.vy *= -0.5
            hit_something = True
        elif self.sprite.top > height:
            self.sprite.top = height
            self.vy *= -0.5
            hit_something = True

        if hit_something and abs(self.vx) > 10:
            self.angular_velocity += 1.5 * direction