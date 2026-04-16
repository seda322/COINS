import pygame
import random
import math
import json
import os
import time
import sys
from browser_saver import BrowserStorage
from logic.economy.prestige import PrestigeManager
from logic.world.gold_coin import GoldCoin
from logic.world.bronze_coin import BronzeCoin
from logic.world.silver_coin import SilverCoin
from logic.world.map_activities.wisp import Wisp
from logic.world.map_activities.multiply_zone import MultiplyZone
from logic.assets.asset_manager import AssetManager
from logic.assets.sound_manager import SoundManager
from logic.assets.spatial_hash import SpatialHash
from logic.economy.balance import Balance
from logic.world.map_activities.beetle import Beetle
from logic.world.map_activities.crater import Crater
from logic.world.map_activities.meteor import Meteor
from logic.world.map_activities.explosion import Explosion
from logic.world.map_activities.tornado import Tornado
from logic.world.lucky_coin import LuckyCoin
from logic.world.cursed_coin import CursedCoin


class GameController:
    def __init__(self, asset_manager: AssetManager, ui_controller, sound_manager: SoundManager,
                 world_width: int, world_height: int, scale_factor: float):
        self.assets = asset_manager
        self.balance = Balance()
        self.ui = ui_controller
        self.sound_manager = sound_manager
        self.coins = []
        self.particles = []
        self.floating_texts = []
        self.grab_mode_active = False # НОВАя переменная для мобилок

        # === ПРЕСТИЖ ===
        self.prestige = PrestigeManager()
        self.confirmation_dialog = None
        # НОВОЕ: Инициализация хранилища и режима захвата
        self.storage = BrowserStorage()
        self.grab_mode_active = False  # Переменная для кнопки на мобильных

        # === КОНСТАНТЫ БАЗОВОЙ СТОИМОСТИ (ИСПРАВЛЕНО ДЛЯ БАЛАНСА) ===
        self.base_prices = {
            "buy_bronze_coin": 10,
            "bronze_value_upgrade": 100,  # Было 50. Подняли цену входа.
            "silver_crit_upgrade": 500,
            "silver_crit_chance_upgrade": 1000,
            "silver_value_upgrade": 2000,  # Было 5000. Опустили, чтобы серебро было актуально.
            "gold_value_upgrade": 50000,  # Было слишком дорого относительно дохода.
            "grab_upgrade": 100000,
            "gold_explosion_upgrade": 250000,
            "wisp_spawn": 1000000,
            "wisp_speed": 500000,
            "wisp_size": 500000,
            "unlock_combo": 50000000,
            "upgrade_combo_limit": 100000000,
            "auto_flip_upgrade": 10000,
            "spawn_zone_2": 50000000,
            "upgrade_zone_2_size": 20000000,
            "upgrade_zone_2_mult": 40000000,
            "spawn_zone_5": 500000000000,
            "upgrade_zone_5_size": 100000000000,
            "upgrade_zone_5_mult": 200000000000,
            "spawn_tornado": 2000000000000,
            "tornado_cooldown_upgrade": 5000000000000,
            "spawn_meteor": 1000000000000000,
            "meteor_cooldown_upgrade": 2000000000000000,
            "buy_victory": 10_000_000_000_000_000_000_000_000,
            "fuse_to_silver": 0,
            "fuse_to_gold": 0,
        }

        # === МНОЖИТЕЛИ РОСТА ЦЕН (ИСПРАВЛЕНО) ===
        self.price_mult = {
            "buy_bronze_coin": 1.10,
            "bronze_value_upgrade": 1.20,      # Было 1.15. Рост цены быстрее.
            "silver_value_upgrade": 1.20,
            "gold_value_upgrade": 1.20,       # Оставляем 1.20, так как база высокая.
            "silver_crit_upgrade": 1.30,
            "silver_crit_chance_upgrade": 1.40,
            "auto_flip_upgrade": 1.50,
            "wisp_speed": 1.30,
            "wisp_size": 1.30,
            "upgrade_combo_limit": 1.50,
            "upgrade_zone_2_size": 1.40,
            "upgrade_zone_2_mult": 1.50,
            "upgrade_zone_5_size": 1.40,
            "upgrade_zone_5_mult": 1.50,
            "tornado_cooldown_upgrade": 1.50,
            "meteor_cooldown_upgrade": 1.50,
        }

        self.base_coin_values = {"bronze": 1, "silver": 10, "gold": 100}

        # === ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ===
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.game_over_active = False
        self.game_over_timer = 0.0
        self.game_over_alpha = 0.0
        self.game_over_text_alpha = 0.0
        self.game_over_stage = 0
        self.combo_watch_timer = 0.0
        self.combo_hit_this_second = False
        self.combo_particle_timer = 0.0
        self.combo_visuals = []
        self.combo_stagnation_angle = 0.0

        self.tornado = None
        self.tornado_respawn_timer = 0.0
        self.tornado_next_spawn_time = 0.0
        self.tornado_unlocked = False
        self.tornado_cooldown_level = 0
        self.tornado_base_cooldown = 60.0
        self.tornado_list = []

        self.max_coins = 200
        self.silver_fusions_count = 0
        self.gold_fusions_count = 0
        self.max_silver_fusions = 75
        self.max_gold_fusions = 25

        # ИСПРАВЛЕНО: Комбо изначально 0 уровня и заблокировано
        self.combo_unlocked = False
        self.combo_value = 1.0
        self.combo_limit_level = 0
        self.combo_base_limit = 2.0
        self.combo_limit = self.combo_base_limit

        self.meteor = None
        self.crater = None
        self.explosions = []
        self.meteor_respawn_timer = 0.0
        self.meteor_next_spawn_time = random.uniform(10.0, 60.0)
        self.meteor_blast_radius = 400.0
        self.meteor_volume = 0.4
        self.meteor_trail_timer = 0.0
        self.meteor_unlocked = False
        self.meteor_cooldown_level = 0

        self.width = world_width
        self.height = world_height
        self.scale_factor = scale_factor

        self.bronze_coin_level = 1
        self.silver_coin_level = 0
        self.gold_coin_level = 0
        self.silver_crit_level = 1
        self.silver_crit_chance_level = 1
        self.auto_flip_level = 0
        self.auto_flip_timer = 0.0
        self.bronze_value_level = 0
        self.silver_value_level = 0
        self.gold_value_level = 0
        self.wisp_speed_level = 0
        self.wisp_size_level = 0
        self.zone_2_size_level = 0
        self.zone_2_mult_level = 0
        self.zone_5_size_level = 0
        self.zone_5_mult_level = 0

        self.has_gold_coin = False
        self.grab_purchased = False
        self.gold_explosion_unlocked = False
        self.grabbed_coin = None

        self.wisp = None
        self.wisp_list = []
        self.zones = []
        self.zone_2 = None
        self.zone_5 = None

        self.beetle = None
        self.beetle_stash = 0
        self.beetle_respawn_timer = 0.0
        self.beetle_respawn_interval = random.uniform(240.0, 300.0) # Первый спаун 4-5 минут

        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_dx = 0
        self.mouse_dy = 0
        self.mouse_velocity_history = []
        self.max_history_frames = 8

        self.spawn_special_coin_timer = 0.0
        self.spawn_special_coin_interval = 1.0

        self.start_coin_x = world_width * 0.25
        self.start_coin_y = world_height * 0.5

        self.spatial_hash = SpatialHash(cell_size=int(150 * self.scale_factor))

        # Загрузка шрифта
        raw_font_path = self.assets.ui_assets.get("font_name", "Arial")
        try:
            if raw_font_path != "Arial" and os.path.exists(raw_font_path):
                self.game_font = pygame.font.Font(raw_font_path, 20)
            else:
                self.game_font = pygame.font.SysFont("Arial", 20)
        except:
            self.game_font = pygame.font.SysFont("Arial", 20)

        self.upgrade_prices = {}

        if not self.load_game():
            self.spawn_coin("bronze")
            self._sync_ui_prices()

        self.spawn_beetle_initial()

    def _sync_ui_prices(self):
        for key, price in self.upgrade_prices.items():
            level = 0
            if key == "buy_bronze_coin":
                level = self.bronze_coin_level
            elif key == "silver_crit_upgrade":
                level = self.silver_crit_level
            elif key == "silver_crit_chance_upgrade":
                level = self.silver_crit_chance_level
            elif key == "bronze_value_upgrade":
                level = self.bronze_value_level
            elif key == "silver_value_upgrade":
                level = self.silver_value_level
            elif key == "gold_value_upgrade":
                level = self.gold_value_level
            elif key == "wisp_speed":
                level = self.wisp_speed_level
            elif key == "wisp_size":
                level = self.wisp_size_level
            elif key == "upgrade_combo_limit":
                level = self.combo_limit_level
            elif key == "auto_flip_upgrade":
                level = self.auto_flip_level

            # Обновляем кнопку престижа при синхронизации
            self._update_prestige_ui()

            self.ui.update_button(key, price, level)

    def spawn_coin(self, coin_type: str, x: float = None, y: float = None):
        if len(self.coins) >= self.max_coins:
            return None

        if x is None or y is None:
            w = self.width
            h = self.height
            margin = 100 * self.scale_factor
            x = random.randint(int(margin), int(w - margin))
            y = random.randint(int(margin), int(h - margin))

        if coin_type == "bronze":
            base = self.base_coin_values["bronze"]
            current_val = base * (2 ** self.bronze_value_level)
            coin = BronzeCoin(x, y, self.assets.bronze_coin_sprites, value=current_val, scale=0.7 * self.scale_factor,
                              scale_factor=self.scale_factor)
            coin.explosion_chance = 0
        elif coin_type == "silver":
            base = self.base_coin_values["silver"]
            current_val = base * (2 ** self.silver_value_level)
            crit_chance = 0.01 * self.silver_crit_chance_level
            coin = SilverCoin(x, y, self.assets.silver_coin_sprites, crit_chance, value=current_val,
                              scale=0.9 * self.scale_factor,
                              scale_factor=self.scale_factor)
            coin.explosion_chance = 0
        elif coin_type == "gold":
            base = self.base_coin_values["gold"]
            current_val = base * (2 ** self.gold_value_level)
            coin = GoldCoin(x, y, self.assets.gold_coin_sprites, value=current_val, scale=1.2 * self.scale_factor,
                            scale_factor=self.scale_factor)
            self.has_gold_coin = True
            if self.gold_explosion_unlocked:
                coin.explosion_chance = 0.5
            else:
                coin.explosion_chance = 0

        elif coin_type == "lucky":
            coin = LuckyCoin(x, y, self.assets.lucky_coin_sprites, scale=1.3 * self.scale_factor,
                             scale_factor=self.scale_factor)
            coin.explosion_chance = 0
        elif coin_type == "cursed":
            coin = CursedCoin(x, y, self.assets.cursed_coin_sprites, scale=1.3 * self.scale_factor,
                              scale_factor=self.scale_factor)
            coin.explosion_chance = 0

        self.coins.append(coin)
        return coin

    def _get_coin_type_string(self, coin) -> str:
        if isinstance(coin, GoldCoin):
            return "gold"
        elif isinstance(coin, SilverCoin):
            return "silver"
        else:
            return "bronze"

    def try_buy_upgrade(self, upgrade_id: str) -> bool:
        if upgrade_id == "new_game":
            self.reset_game(hard_reset=False)
            return True

        if upgrade_id == "prestige":
            if self.prestige.can_prestige():
                self.perform_prestige()
                return True
            return False

        level = self._get_current_level(upgrade_id)
        cost = self._calculate_price(upgrade_id, level)

        if upgrade_id in ["grab_upgrade", "gold_explosion_upgrade", "wisp_spawn", "unlock_combo",
                          "spawn_zone_2", "spawn_zone_5", "spawn_tornado", "spawn_meteor", "buy_victory",
                          "fuse_to_silver", "fuse_to_gold"]:
            cost = self.base_prices.get(upgrade_id, 1000)

        if self.balance.can_spend(cost):
            self.balance.spend(cost)
            success = True

            if upgrade_id == "buy_bronze_coin":
                coin = self.spawn_coin("bronze")
                if coin:
                    self.bronze_coin_level += 1
                else:
                    success = False

            elif upgrade_id == "bronze_value_upgrade":
                self.bronze_value_level += 1
                for c in self.coins:
                    if isinstance(c, BronzeCoin): c.value = int(
                        self.base_coin_values["bronze"] * (1.5 ** self.bronze_value_level))

            elif upgrade_id == "silver_value_upgrade":
                self.silver_value_level += 1
                for c in self.coins:
                    if isinstance(c, SilverCoin): c.value = int(
                        self.base_coin_values["silver"] * (1.5 ** self.silver_value_level))

            elif upgrade_id == "gold_value_upgrade":
                self.gold_value_level += 1
                for c in self.coins:
                    if isinstance(c, GoldCoin): c.value = int(
                        self.base_coin_values["gold"] * (1.5 ** self.gold_value_level))

            elif upgrade_id == "silver_crit_upgrade":
                self.silver_crit_level += 1
            elif upgrade_id == "silver_crit_chance_upgrade":
                self.silver_crit_chance_level += 1
            elif upgrade_id == "auto_flip_upgrade":
                self.auto_flip_level += 1

            elif upgrade_id == "wisp_speed":
                if self.wisp: self.wisp.upgrade_speed(50)
                self.wisp_speed_level += 1
            elif upgrade_id == "wisp_size":
                if self.wisp: self.wisp.upgrade_scale(0.025)
                self.wisp_size_level += 1

            elif upgrade_id == "upgrade_combo_limit":
                if not self.combo_unlocked:
                    return False
                self.combo_limit_level += 1
                new_limit = self.combo_base_limit + (self.combo_limit_level * 0.5)
                if new_limit > 10.0: new_limit = 10.0
                self.combo_limit = new_limit

            elif upgrade_id == "upgrade_zone_2_size":
                if self.zone_2: self.zone_2.upgrade_size(1.03)
                self.zone_2_size_level += 1
            elif upgrade_id == "upgrade_zone_2_mult":
                if self.zone_2: self.zone_2.upgrade_multiplier(0.2)
                self.zone_2_mult_level += 1
            elif upgrade_id == "upgrade_zone_5_size":
                if self.zone_5: self.zone_5.upgrade_size(1.03)
                self.zone_5_size_level += 1
            elif upgrade_id == "upgrade_zone_5_mult":
                if self.zone_5: self.zone_5.upgrade_multiplier(0.4)
                self.zone_5_mult_level += 1

            elif upgrade_id == "tornado_cooldown_upgrade":
                self.tornado_cooldown_level += 1
            elif upgrade_id == "meteor_cooldown_upgrade":
                self.meteor_cooldown_level += 1

            elif upgrade_id == "grab_upgrade":
                self.grab_purchased = True
                self.ui.mark_purchased(upgrade_id)
            elif upgrade_id == "gold_explosion_upgrade":
                self.gold_explosion_unlocked = True
                self.ui.mark_purchased(upgrade_id)
            elif upgrade_id == "wisp_spawn":
                if not self.wisp:
                    self.wisp = Wisp(self.width / 2, self.height / 2, self.assets.wisp_sprites,
                                     speed=100 * self.scale_factor, scale=0.33, scale_factor=self.scale_factor)
                    self.wisp_list.append(self.wisp)
                    self.ui.mark_purchased(upgrade_id)

            elif upgrade_id == "unlock_combo":
                if not self.combo_unlocked:
                    self.combo_unlocked = True
                    self.combo_limit_level = 1  # Сразу 1 уровень
                    self.combo_limit = self.combo_base_limit + 0.5
                    self.ui.mark_purchased(upgrade_id)

            elif upgrade_id == "spawn_zone_2":
                if self.zone_2 is None:
                    z2 = MultiplyZone(self.width, self.height, 2.0, (100, 255, 100, 100))
                    self.zones.append(z2)
                    self.zone_2 = z2
                    self.ui.mark_purchased(upgrade_id)
            elif upgrade_id == "spawn_zone_5":
                if self.zone_5 is None:
                    z5 = MultiplyZone(self.width, self.height, 5.0, (160, 32, 240, 100))
                    self.zones.append(z5)
                    self.zone_5 = z5
                    self.ui.mark_purchased(upgrade_id)

            elif upgrade_id == "spawn_tornado":
                if not self.tornado_unlocked:
                    self.tornado_unlocked = True
                    self.ui.mark_purchased(upgrade_id)
            elif upgrade_id == "spawn_meteor":
                if not self.meteor_unlocked:
                    self.meteor_unlocked = True
                    self.ui.mark_purchased(upgrade_id)

            elif upgrade_id == "buy_victory":
                if not self.game_over_active:
                    # Исправлено
                    self.storage.delete()
                    self.game_over_active = True
                    self.game_over_timer = 0.0
                    self.game_over_stage = 0
                    self.ui.mark_purchased(upgrade_id)

            elif upgrade_id == "fuse_to_silver":
                bronze_coins = [c for c in self.coins if isinstance(c, BronzeCoin)]
                if len(bronze_coins) >= 5 and self.silver_fusions_count < self.max_silver_fusions:
                    target_x = bronze_coins[0].sprite.center_x
                    target_y = bronze_coins[0].sprite.center_y
                    for i in range(5): self.coins.remove(bronze_coins[i])
                    self.spawn_coin("silver", x=target_x, y=target_y)
                    if self.sound_manager.merge_sound: self.sound_manager.merge_sound.play()
                    self.silver_fusions_count += 1
                    self._update_fusion_buttons()
                else:
                    success = False

            elif upgrade_id == "fuse_to_gold":
                silver_coins = [c for c in self.coins if isinstance(c, SilverCoin)]
                if len(silver_coins) >= 3 and self.gold_fusions_count < self.max_gold_fusions:
                    target_x = silver_coins[0].sprite.center_x
                    target_y = silver_coins[0].sprite.center_y
                    for i in range(3): self.coins.remove(silver_coins[i])
                    self.spawn_coin("gold", x=target_x, y=target_y)
                    if self.sound_manager.merge_sound: self.sound_manager.merge_sound.play()
                    self.gold_fusions_count += 1
                    self._update_fusion_buttons()
                else:
                    success = False

            if success:
                next_price = self._calculate_price(upgrade_id, self._get_current_level(upgrade_id))
                self.ui.update_button(upgrade_id, next_price, level=self._get_current_level(upgrade_id))
                self._update_prestige_ui()
                return True
            else:
                self.balance.add(cost)
                return False
        return False

    def update(self, dt: float) -> None:
        width = self.width
        height = self.height

        if self.game_over_active:
            self.game_over_timer += dt
            if self.game_over_stage == 0:
                target_alpha = 128
                if self.game_over_alpha < target_alpha:
                    self.game_over_alpha += dt * 50
                else:
                    self.game_over_alpha = target_alpha
                    self.game_over_timer = 0.0
                    self.game_over_stage = 1
            elif self.game_over_stage == 1:
                if self.game_over_text_alpha < 255:
                    self.game_over_text_alpha += dt * 500
                else:
                    self.game_over_text_alpha = 255
                    self.game_over_timer = 0.0
                    self.game_over_stage = 2
            elif self.game_over_stage == 2:
                if self.game_over_text_alpha > 0:
                    self.game_over_text_alpha -= dt * 300
                else:
                    self.game_over_text_alpha = 0
                    self.game_over_timer = 0.0
                    self.game_over_stage = 3
            elif self.game_over_stage == 3:
                if self.game_over_text_alpha < 255:
                    self.game_over_text_alpha += dt * 500
                else:
                    self.game_over_text_alpha = 255
                    self.game_over_timer = 0.0
                    self.game_over_stage = 4
            elif self.game_over_stage == 4:
                if self.game_over_text_alpha > 0:
                    self.game_over_text_alpha -= dt * 300
                else:
                    pass

        if not self.game_over_active:
            self.coins = [c for c in self.coins if
                          not (hasattr(c, 'lifetime') and c.lifetime is not None and c.lifetime <= 0)]

            if self.auto_flip_level >= 1:
                self.auto_flip_timer += dt
                flip_interval = 5.0 - (self.auto_flip_level - 1) * 0.3
                if flip_interval < 1.0: flip_interval = 1.0
                if self.auto_flip_timer >= flip_interval:
                    self.auto_flip_timer = 0
                    standing_coins = [c for c in self.coins if
                                      not c.is_moving and not isinstance(c, (LuckyCoin, CursedCoin))]
                    if standing_coins:
                        coin_to_flip = random.choice(standing_coins)
                        dx = random.randint(-50, 50)
                        dy = random.randint(-50, 50)
                        coin_to_flip.hit(dx, dy)
                        c_type = self._get_coin_type_string(coin_to_flip)
                        self.sound_manager.play_toss(c_type)

            if self.tornado_unlocked:
                if self.tornado:
                    is_alive = self.tornado.update(dt)
                    for coin in self.coins:
                        self.tornado.affect_coin(coin, dt)
                    if not is_alive:
                        self.tornado = None
                        self.tornado_list.clear()
                        for coin in self.coins:
                            coin.tornado_hit = False
                            if coin.is_moving:
                                coin.land()
                        cd = self.tornado_base_cooldown - (self.tornado_cooldown_level * 3.0)
                        if cd < 5.0: cd = 5.0
                        self.tornado_respawn_timer = 0.0
                        self.tornado_next_spawn_time = cd
                else:
                    self.tornado_respawn_timer += dt
                    if self.tornado_respawn_timer >= self.tornado_next_spawn_time:
                        self.spawn_tornado()
                        self.tornado_respawn_timer = 0.0

            if self.beetle:
                is_alive = self.beetle.update(dt, width, height)
                if is_alive is False:
                    self.beetle = None
                    self.beetle_respawn_interval = random.uniform(240.0, 300.0)  # 4-5 минут
                    self.beetle_respawn_timer = 0.0
            else:
                self.beetle_respawn_timer += dt
                if self.beetle_respawn_timer >= self.beetle_respawn_interval:
                    self.spawn_beetle()

            self.spawn_special_coin_timer += dt
            if self.spawn_special_coin_timer >= self.spawn_special_coin_interval:
                self.spawn_special_coin_timer = 0
                if random.random() < 0.001:
                    self.spawn_coin("lucky")
                elif random.random() < 0.0001:
                    self.spawn_coin("cursed")

            if self.meteor_unlocked:
                spawn_smoke = False
                if self.meteor:
                    is_trail = self.meteor.update(dt)
                    if is_trail and self.meteor.center_y > self.meteor.target_y:
                        spawn_smoke = True
                    hit_ground = self.meteor.center_y <= self.meteor.target_y
                    if hit_ground:
                        impact_x = self.meteor.center_x
                        impact_y = self.meteor.center_y

                        if self.sound_manager.boom_sound and not self.sound_manager.muted:
                            self.sound_manager.boom_sound.set_volume(self.meteor_volume)
                            self.sound_manager.boom_sound.play()

                        if self.assets.explosion_textures:
                            expl = Explosion(impact_x, impact_y, self.assets.explosion_textures)
                            self.explosions.append(expl)
                        self.create_explosion_particles(impact_x, impact_y)
                        if self.assets.crater_texture:
                            self.crater = Crater(impact_x, impact_y, self.assets.crater_texture)
                            self.crater.multiplier = 10.0
                            self.crater.scale = 1.5
                        else:
                            self.crater = None
                        for coin in self.coins:
                            dx = impact_x - coin.sprite.center_x
                            dy = impact_y - coin.sprite.center_y
                            dist_sq = dx * dx + dy * dy
                            if dist_sq < (self.meteor_blast_radius * self.meteor_blast_radius):
                                coin.hit(dx, dy)
                        self.meteor = None
                        self.create_explosion_particles(impact_x, impact_y)
                        self.shake_timer = 0.8
                        self.shake_intensity = 40.0 * self.scale_factor
                elif self.crater:
                    is_alive = self.crater.update(dt)
                    if not is_alive:
                        self.crater = None
                        max_cd = 2 - (self.meteor_cooldown_level * 0.1)
                        if max_cd < 0.5: max_cd = 0.5
                        self.meteor_respawn_timer = 0.0
                        self.meteor_next_spawn_time = random.uniform(1, max_cd)
                else:
                    self.meteor_respawn_timer += dt
                    if self.meteor_respawn_timer >= self.meteor_next_spawn_time:
                        self.spawn_meteor()
                        self.meteor_respawn_timer = 0.0

                if spawn_smoke and self.meteor:
                    self.create_particles(self.meteor.center_x, self.meteor.center_y, (100, 100, 100, 150))

                for expl in self.explosions[:]:
                    if not expl.update(dt):
                        self.explosions.remove(expl)

            if self.grabbed_coin:
                self.grabbed_coin.sprite.center_x = self.mouse_x
                self.grabbed_coin.sprite.center_y = self.mouse_y
                self.grabbed_coin.vx = 0
                self.grabbed_coin.vy = 0

            self.spatial_hash = SpatialHash(cell_size=int(150 * self.scale_factor))
            for coin in self.coins:
                self.spatial_hash.add(coin.sprite)

            for coin in self.coins:
                if coin is self.grabbed_coin: continue
                if coin.lifetime is not None and coin.lifetime <= 0: continue

                nearby_sprites = self.spatial_hash.get_sprites_near_point((coin.sprite.center_x, coin.sprite.center_y))
                nearby_coins = []
                for spr in nearby_sprites:
                    if hasattr(spr, 'coin') and spr.coin is not coin:
                        nearby_coins.append(spr.coin)

                coin.update(dt, width, height, nearby_coins)

                outcome = coin.check_land_event()

                # === ЛОГИКА УСПЕХА (Outcome > 0) ===
                if outcome > 0:
                    total_multiplier = 1.0
                    current_combo = self.combo_value if self.combo_unlocked else 1.0
                    final_value = int(outcome * total_multiplier * current_combo)
                    self._add_income(final_value)

                    if self.combo_unlocked and outcome > 0:
                        self.combo_hit_this_second = True
                        if self.combo_value < self.combo_limit:
                            self.combo_value += 0.1
                            if self.combo_value > self.combo_limit:
                                self.combo_value = self.combo_limit

                    if isinstance(coin, SilverCoin):
                        if coin.is_crit:
                            coin.is_crit = False
                            text_x = coin.sprite.right + 10
                            text_y = coin.sprite.top - 10
                            self.create_floating_text(f"x{self.silver_crit_level}", text_x, text_y,
                                                      (100, 200, 255, 255), coin)
                            self.create_particles(coin.sprite.center_x, coin.sprite.center_y, (192, 192, 192, 255),
                                                  coin)

                    if isinstance(coin, LuckyCoin):
                        if not coin.sound_played:
                            current_balance = self.balance.get()
                            profit = int(current_balance * 4)
                            self._add_income(profit)
                            lx = coin.sprite.right + 10
                            ly = coin.sprite.top - 10
                            self.create_floating_text("x5", lx, ly, (50, 255, 50, 255), coin)

                            if self.sound_manager.lucky_success and not self.sound_manager.muted:
                                self.sound_manager.lucky_success.play()
                            coin.sound_played = True

                    # Успех черной монетки
                    if isinstance(coin, CursedCoin):
                        if not coin.sound_played:
                            current_balance = self.balance.get()
                            profit = int(current_balance * 99)
                            self._add_income(profit)
                            cx = coin.sprite.right + 10
                            cy = coin.sprite.top - 10
                            self.create_floating_text("x100", cx, cy, (255, 50, 50, 255), coin)

                            if self.sound_manager.cursed_success and not self.sound_manager.muted:
                                self.sound_manager.cursed_success.play()
                            coin.sound_played = True

                # === ЛОГИКА НЕУДАЧИ (Вне зависимости от outcome) ===
                # Проверяем флаг банкротства только для CursedCoin
                if isinstance(coin, CursedCoin) and coin.bankruptcy_triggered:
                    # 1. Обнуляем баланс
                    self.balance.set(0)

                    # 2. Звук провала
                    if self.sound_manager.cursed_fail and not self.sound_manager.muted:
                        self.sound_manager.cursed_fail.play()

                    cx_pos, cy_pos = coin.sprite.center_x, coin.sprite.center_y

                    # 3. Эффекты
                    self.create_explosion_particles(cx_pos, cy_pos)
                    for c in self.coins:
                        if c is not coin:
                            dx = c.sprite.center_x - cx_pos
                            dy = c.sprite.center_y - cy_pos
                            dist_sq = dx * dx + dy * dy
                            if dist_sq > 0:
                                dist = math.sqrt(dist_sq)
                                # Базовая сила взрыва
                                base_force = 2000.0 * self.scale_factor * (
                                        1.0 - min(dist / (1000.0 * self.scale_factor), 0.5))

                                nx = dx / dist
                                ny = dy / dist

                                # === УЧЕТ МАССЫ ===
                                # Тяжелые монеты улетают недалеко
                                final_force = base_force / c.mass

                                c.vx += nx * final_force
                                c.vy += ny * final_force
                                c.is_moving = True
                                c._select_flying_animation()

                    self.shake_timer = 1.0
                    self.shake_intensity = 80.0 * self.scale_factor

                    # Сбрасываем флаг, чтобы не сработало дважды
                    coin.bankruptcy_triggered = False
                    coin.sound_played = True

                if coin.needs_toss_sound:
                    c_type = self._get_coin_type_string(coin)
                    self.sound_manager.play_toss(c_type)
                    coin.needs_toss_sound = False

                if coin.landed:
                    c_type = self._get_coin_type_string(coin)
                    self.sound_manager.play_land(c_type)
                    coin.landed = False

            if self.wisp:
                self.wisp.update(dt, width, height, self.coins, self.grabbed_coin)

            for zone in self.zones:
                zone.update(dt, width, height)

            for p in self.particles[:]:
                decay_speed = p.get('decay_speed', 1.0)
                p['life'] -= dt * decay_speed
                if 'linked_coin' in p and p['linked_coin'] is not None:
                    p['offset_x'] += p['vx'] * dt
                    p['offset_y'] += p['vy'] * dt
                    p['x'] = p['linked_coin'].sprite.center_x + p['offset_x']
                    p['y'] = p['linked_coin'].sprite.center_y + p['offset_y']
                else:
                    p['x'] += p['vx'] * dt
                    p['y'] += p['vy'] * dt

                if p['life'] <= 0:
                    self.particles.remove(p)

            self.ui.update_grab_state(self.has_gold_coin, self.grab_purchased)
            self.ui.update_explosion_state(self.gold_explosion_unlocked)
            self.ui.update_wisp_state(self.wisp is not None)
            self.ui.update_zone_state(has_zone_2=(self.zone_2 is not None), has_zone_5=(self.zone_5 is not None))
            self.ui.update_tornado_state(self.tornado_unlocked)
            self.ui.update_meteor_state(self.meteor_unlocked)
            self.ui.update_combo_unlocked_state(self.combo_unlocked)

            # === ВАЖНО: Обновление кнопки престижа каждый кадр ===
            # Это решает проблему, когда кнопка не обновляется при изменении баланса
            self._update_prestige_ui()

            if self.shake_timer > 0:
                self.shake_timer -= dt
                self.shake_intensity *= 0.9
                if self.shake_intensity < 0.5:
                    self.shake_timer = 0
                    self.shake_intensity = 0

            if self.combo_unlocked:
                if self.combo_value >= 10.0:
                    self.combo_particle_timer += dt
                    if self.combo_particle_timer >= 0.05:
                        self.combo_particle_timer = 0
                        self.create_combo_fire_particles()
                self.combo_watch_timer += dt
                if self.combo_watch_timer >= 1.0:
                    if not self.combo_hit_this_second:
                        self.combo_value = 1.0
                    self.combo_watch_timer = 0.0
                    self.combo_hit_this_second = False

            for ft in self.floating_texts[:]:
                ft['life'] -= dt
                ft['y'] += ft['vy'] * dt
                ft['x'] += ft['vx'] * dt
                if ft['linked_coin'] is not None:
                    if ft['linked_coin'] not in self.coins:
                        ft['linked_coin'] = None
                    else:
                        ft['x'] = ft['linked_coin'].sprite.right + 10
                        ft['y'] = ft['linked_coin'].sprite.top - 10

                if ft['life'] <= 0:
                    self.floating_texts.remove(ft)

    def draw(self, surface, screen_height) -> None:
        # --- SHAKE LOGIC ---
        if self.shake_timer > 0:
            sx = random.uniform(-self.shake_intensity, self.shake_intensity)
            sy = random.uniform(-self.shake_intensity, self.shake_intensity)
        else:
            sx = 0.0
            sy = 0.0

        # --- DRAW ZONES ---
        for zone in self.zones:
            # Apply shake temporarily for logic coordinates if needed,
            # but zone.draw uses screen coordinates, so we must pass shake manually or handle inside.
            # Simplest: zone.x/y are logic coords. zone.draw converts to screen.
            # We pass shake offsets to draw method? Or modify zone.x/y?
            # Modifying zone.x/y is dangerous (physics).
            # Let's pass shake to draw if we implemented it, or just ignore shake for zones for simplicity,
            # OR create a temporary offset.
            # Actually, in the original code:
            # zone.x += sx; zone.draw(); zone.x -= sx
            # We will do the same but via arguments.
            zone.x += sx
            zone.y += sy
            zone.draw(surface, screen_height)
            zone.x -= sx
            zone.y -= sy

        # --- DRAW BEETLE ---
        if self.beetle:
            self.beetle.center_x += sx
            self.beetle.center_y += sy
            self.beetle.draw(surface, screen_height)
            self.beetle.center_x -= sx
            self.beetle.center_y -= sy

        # --- DRAW CRATER ---
        if self.crater:
            self.crater.center_x += sx
            self.crater.center_y += sy
            self.crater.draw(surface, screen_height)
            self.crater.center_x -= sx
            self.crater.center_y -= sy

        # --- DRAW COINS (Static then Moving for layering) ---
        for coin in self.coins:
            if not coin.is_moving:
                coin.sprite.center_x += sx
                coin.sprite.center_y += sy
                coin.draw(surface, screen_height)
                coin.sprite.center_x -= sx
                coin.sprite.center_y -= sy

        for coin in self.coins:
            if coin.is_moving:
                coin.sprite.center_x += sx
                coin.sprite.center_y += sy
                coin.draw(surface, screen_height)
                coin.sprite.center_x -= sx
                coin.sprite.center_y -= sy

        # --- DRAW WISP ---
        for wisp in self.wisp_list:
            wisp.center_x += sx
            wisp.center_y += sy
            wisp.draw(surface, screen_height)
            wisp.center_x -= sx
            wisp.center_y -= sy

        # --- DRAW EXPLOSIONS ---
        for expl in self.explosions:
            expl.center_x += sx
            expl.center_y += sy
            expl.draw(surface, screen_height)
            expl.center_x -= sx
            expl.center_y -= sy

        # --- DRAW TORNADO ---
        for tornado in self.tornado_list:
            tornado.center_x += sx
            tornado.center_y += sy
            tornado.draw(surface, screen_height)
            tornado.center_x -= sx
            tornado.center_y -= sy

        # --- DRAW METEOR ---
        if self.meteor:
            self.meteor.center_x += sx
            self.meteor.center_y += sy
            self.meteor.draw(surface, screen_height)
            self.meteor.center_x -= sx
            self.meteor.center_y -= sy

        # --- DRAW PARTICLES ---
        for p in self.particles:
            life_ratio = p['life'] / 1.0
            alpha = min(255, int(255 * life_ratio))
            if alpha < 0: alpha = 0
            current_color = (p['color'][0], p['color'][1], p['color'][2], alpha)

            # Logic coords -> Screen coords
            # Pygame circle takes center (x, y)
            draw_x = int(p['x'] + sx)
            draw_y = int(screen_height - (p['y'] + sy))

            # Note: Pygame draw.circle doesn't support alpha on the main surface directly
            # efficiently without a temp surface. For performance with many particles,
            # we usually drop alpha or use a pre-rendered surface.
            # For simplicity here, we draw solid or ignore alpha if it's complex.
            # Let's try to support alpha via a temp surface if needed, or just solid color for now.
            # Solid is safer for performance.
            pygame.draw.circle(surface, current_color[:3], (draw_x, draw_y), int(p['size']))

        # --- DRAW COMBO ---
        if self.combo_unlocked and self.combo_value > 1.0:
            combo_x = 60 * self.scale_factor
            combo_y = self.height - (60 * self.scale_factor)
            pulse = 1.0 + 0.05 * math.sin(time.time() * 5)
            font_sz = int(40 * self.scale_factor * pulse)

            # Reload font with new size (slow but dynamic like original)
            # Optimization: Cache fonts? For now, simple reload.
            # Ideally use a font manager.
            try:
                combo_font = pygame.font.Font(self.assets.ui_assets.get("font_name"),
                                              font_sz) if self.assets.ui_assets.get(
                    "font_name") != "Arial" else pygame.font.SysFont("Arial", font_sz)
            except:
                combo_font = pygame.font.SysFont("Arial", font_sz)

            combo_int = int(self.combo_value)
            color_palette = [
                (200, 30, 30, 255), (220, 100, 0, 255), (200, 160, 0, 255), (30, 180, 30, 255),
                (0, 180, 200, 255), (50, 50, 220, 255), (180, 30, 200, 255), (200, 30, 30, 255),
                (220, 100, 0, 255), (200, 160, 0, 255)
            ]
            color_index = (combo_int - 1) % 10
            txt_color = color_palette[color_index]

            if self.combo_value >= self.combo_limit:
                self.combo_stagnation_angle += 0.1
                wobble_x = math.sin(self.combo_stagnation_angle * 2) * 5
                wobble_y = math.cos(self.combo_stagnation_angle * 2) * 5
                if int(self.combo_stagnation_angle * 2) % 2 == 0:
                    txt_color = (255, 0, 0, 255)
                draw_pos_x = combo_x + wobble_x + sx
                draw_pos_y = combo_y + wobble_y + sy
            else:
                draw_pos_x = combo_x + sx
                draw_pos_y = combo_y + sy

            text_surf = combo_font.render(f"x{self.combo_value:.1f}", True, txt_color[:3])
            # Logic Y -> Screen Y
            # text_pos logic is left-anchor? Original: anchor_x="left".
            # Pygame blit is top-left.
            screen_y = screen_height - draw_pos_y - (font_sz / 2)  # Rough centering vertically
            surface.blit(text_surf, (draw_pos_x, screen_y))

        # --- DRAW FLOATING TEXTS ---
        for ft in self.floating_texts:
            alpha = int(255 * (ft['life'] / 1.5))
            if alpha < 0: alpha = 0
            r, g, b, _ = ft['base_color']
            color = (r, g, b, alpha)

            ft_font = self.game_font  # Use default game font for simplicity
            text_surf = ft_font.render(ft['text'], True, color[:3])
            text_surf.set_alpha(alpha)

            # ft['x'], ft['y'] are logic coordinates
            screen_x = ft['x']
            screen_y = screen_height - ft['y']

            surface.blit(text_surf, (screen_x, screen_y))

        # --- DRAW GAME OVER ---
        if self.game_over_active:
            # Transparent overlay
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(self.game_over_alpha)))
            surface.blit(overlay, (0, 0))

            text_alpha = int(self.game_over_text_alpha)
            if text_alpha > 255: text_alpha = 255
            if text_alpha < 0: text_alpha = 0

            go_font_size = int(60 * self.scale_factor)
            try:
                go_font = pygame.font.Font(self.assets.ui_assets.get("font_name"),
                                           go_font_size) if self.assets.ui_assets.get(
                    "font_name") != "Arial" else pygame.font.SysFont("Arial", go_font_size)
            except:
                go_font = pygame.font.SysFont("Arial", go_font_size)

            if self.game_over_stage >= 1 and self.game_over_stage <= 2:
                txt = go_font.render("Конец?", True, (255, 255, 255))
                txt.set_alpha(text_alpha)
                rect = txt.get_rect(center=(self.width / 2, self.height / 2))
                surface.blit(txt, rect)
            elif self.game_over_stage >= 3:
                txt = go_font.render("Спасибо за игру!", True, (255, 255, 255))
                txt.set_alpha(text_alpha)
                rect = txt.get_rect(center=(self.width / 2, self.height / 2))
                surface.blit(txt, rect)

    def on_mouse_press(self, x: int, y: int, button: int) -> None:
        if self.game_over_active: return

        # === НОВОЕ: Обработка "Режима захвата" для мобильных ===
        # Если куплен захват и включен режим захвата, ЛКМ работает как ПКМ
        if button == pygame.BUTTON_LEFT:
            if self.grab_purchased and self.grab_mode_active:
                # Имитируем ПКМ для захвата
                self.on_mouse_press_rmb(x, y)
                return

        # Стандартная логика ЛКМ
        if button == pygame.BUTTON_LEFT:
            if x < self.width:
                clicked_coin = False
                for coin in self.coins:
                    if not coin.is_moving and coin is not self.grabbed_coin:
                        dx = x - coin.sprite.center_x
                        dy = y - coin.sprite.center_y
                        if dx * dx + dy * dy < (coin.radius * coin.radius):
                            is_special_used = isinstance(coin, (LuckyCoin, CursedCoin)) and getattr(coin, 'is_used',
                                                                                                    False)
                            if not is_special_used:
                                coin.hit(dx, dy)
                                c_type = self._get_coin_type_string(coin)
                                self.sound_manager.play_toss(c_type)
                                clicked_coin = True
                                break
                if not clicked_coin and self.beetle and self.beetle.can_be_clicked:
                    dx = x - self.beetle.center_x
                    dy = y - self.beetle.center_y
                    hit_radius = self.beetle.width / 2
                    if dx * dx + dy * dy < (hit_radius * hit_radius):
                        self.kill_beetle()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x = x
        self.mouse_y = y
        self.mouse_dx = dx
        self.mouse_dy = dy
        self.mouse_velocity_history.append((dx, dy))
        if len(self.mouse_velocity_history) > self.max_history_frames:
            self.mouse_velocity_history.pop(0)

    def on_mouse_press_rmb(self, x: int, y: int) -> None:
        if not self.grab_purchased: return
        for coin in self.coins:
            if isinstance(coin, GoldCoin) and not coin.is_moving:
                dx = x - coin.sprite.center_x
                dy = y - coin.sprite.center_y
                if dx * dx + dy * dy < (coin.radius * coin.radius):
                    self.grabbed_coin = coin

                    # 1. Отключаем торнадо
                    coin.tornado_hit = False

                    # 2. Переводим в режим "на земле"
                    coin.is_moving = False
                    coin.is_grabbed = True
                    coin.vx = 0
                    coin.vy = 0

                    # 3. Восстанавливаем текстуру и размер
                    face_key = coin.current_face if hasattr(coin, 'current_face') else "heads"
                    correct_texture = coin.sprites.get(face_key, coin.sprites["heads"])
                    coin.sprite.texture = correct_texture
                    coin.sprite.scale = coin.scale

                    coin.anim = []

                    self.mouse_x = x
                    self.mouse_y = y
                    self.mouse_velocity_history = []
                    break

    def on_mouse_release_rmb(self, x: int, y: int) -> None:
        if not self.grabbed_coin: return
        coin = self.grabbed_coin
        self.grabbed_coin = None
        coin.is_grabbed = False

        avg_dx = 0
        avg_dy = 0
        count = len(self.mouse_velocity_history)
        if count > 0:
            total_dx = sum(d[0] for d in self.mouse_velocity_history)
            total_dy = sum(d[1] for d in self.mouse_velocity_history)
            avg_dx = total_dx / count
            avg_dy = total_dy / count

        move_threshold = 10.0

        if abs(avg_dx) < move_threshold and abs(avg_dy) < move_threshold:
            coin.vx = 0
            coin.vy = 0
            return

        throw_multiplier = 150.0 * self.scale_factor

        coin.vx = avg_dx * throw_multiplier
        coin.vy = avg_dy * throw_multiplier

        MAX_SPEED = 2000.0 * self.scale_factor
        current_speed_sq = coin.vx * coin.vx + coin.vy * coin.vy
        if current_speed_sq > MAX_SPEED ** 2:
            current_speed = math.sqrt(current_speed_sq)
            ratio = MAX_SPEED / current_speed
            coin.vx *= ratio
            coin.vy *= ratio

        coin.is_moving = True
        coin._select_flying_animation()
        coin.anim_index = 0
        if coin.anim:
            coin.sprite.texture = coin.anim[0]

    def create_particles(self, cx, cy, color=(255, 215, 0, 255), coin=None):
        base_size = 4.0 * self.scale_factor
        size_var = 4.0 * self.scale_factor
        base_speed = 100.0 * self.scale_factor
        speed_var = 100.0 * self.scale_factor

        for _ in range(30):
            gray = random.randint(80, 200)
            base_color = (gray, gray, gray)
            angle = random.uniform(0, 6.28)
            speed = random.uniform(base_speed, base_speed + speed_var)
            size = random.uniform(base_size, base_size + size_var)

            particle_data = {
                'x': cx, 'y': cy,
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'life': 1.0,
                'color': base_color, 'size': size
            }
            if coin is not None:
                particle_data['linked_coin'] = coin
                particle_data['decay_speed'] = 2.0
                p_radius = coin.radius
                particle_data['offset_x'] = math.cos(angle) * (p_radius * 0.9)
                particle_data['offset_y'] = math.sin(angle) * (p_radius * 0.9)
            else:
                particle_data['decay_speed'] = 1.0
            self.particles.append(particle_data)

    def get_save_path(self):
        import sys
        import os
        application_path = os.path.dirname(sys.executable)
        return os.path.join(application_path, "save.json")

    def save_game(self) -> None:
        data = {
            "balance": self.balance.get(),
            "prestige": self.prestige.get_data(),
            "upgrade_prices": self.upgrade_prices,
            "silver_crit_level": self.silver_crit_level,
            "beetle_stash": self.beetle_stash,
            "fusions": {
                "silver": self.silver_fusions_count,
                "gold": self.gold_fusions_count
            },
            "auto_flip_level": self.auto_flip_level,
            "flags": {
                "has_gold_coin": self.has_gold_coin,
                "grab_purchased": self.grab_purchased,
                "gold_explosion_unlocked": self.gold_explosion_unlocked
            },
            "wisp": None,
            "zones": [],
            "coins": [],
            "levels": {
                "bronze_coin": self.bronze_coin_level,
                "silver_coin": self.silver_coin_level,
                "silver_crit_chance_level": self.silver_crit_chance_level,
                "gold_coin": self.gold_coin_level,
                "bronze_value": self.bronze_value_level,
                "silver_value": self.silver_value_level,
                "gold_value": self.gold_value_level,
                "wisp_speed": self.wisp_speed_level,
                "wisp_size": self.wisp_size_level,
                "zone_2_size": self.zone_2_size_level,
                "zone_2_mult": self.zone_2_mult_level,
                "zone_5_size": self.zone_5_size_level,
                "zone_5_mult": self.zone_5_mult_level,
            },
            "meteor_unlocked": self.meteor_unlocked,
            "meteor_cooldown_level": self.meteor_cooldown_level,
            "tornado_unlocked": self.tornado_unlocked,
            "tornado_cooldown_level": self.tornado_cooldown_level,
            "combo_unlocked": self.combo_unlocked,
            "combo_limit_level": self.combo_limit_level,
            "combo_value": self.combo_value
        }

        # Сохранение Виспа
        if self.wisp:
            data["wisp"] = {
                "speed": self.wisp.speed, "scale": self.wisp.scale,
                "x": self.wisp.center_x, "y": self.wisp.center_y,
                "vx": self.wisp.vx, "vy": self.wisp.vy
            }

        # Сохранение Зон
        for z in self.zones:
            z_type = "unknown"
            if z is self.zone_2:
                z_type = "zone_2"
            elif z is self.zone_5:
                z_type = "zone_5"
            data["zones"].append({
                "type": z_type, "multiplier": z.multiplier, "size": z.size,
                "x": z.x, "y": z.y, "vx": z.vx, "vy": z.vy
            })

        # Сохранение Монет
        for coin in self.coins:
            coin_type = "bronze"
            if isinstance(coin, SilverCoin):
                coin_type = "silver"
            elif isinstance(coin, GoldCoin):
                coin_type = "gold"
            elif isinstance(coin, LuckyCoin):
                coin_type = "lucky"
            elif isinstance(coin, CursedCoin):
                coin_type = "cursed"
            data["coins"].append({
                "type": coin_type,
                "x": coin.sprite.center_x, "y": coin.sprite.center_y,
                "vx": coin.vx, "vy": coin.vy, "scale": coin.scale,
                "is_moving": coin.is_moving, "angle": coin.angle
            })

        # ИСПОЛЬЗУЕМ НОВОЕ ХРАНИЛИЩЕ
        self.storage.save(data)

    def load_game(self) -> bool:
        # ИСПОЛЬЗУЕМ НОВОЕ ХРАНИЛИЩЕ
        data = self.storage.load()
        if not data: return False

        try:
            self.balance._value = data["balance"]
            if "prestige" in data:
                self.prestige.load_data(data["prestige"])
            else:
                self.prestige = PrestigeManager()

            self.upgrade_prices = data.get("upgrade_prices", {})
            self.beetle_stash = data.get("beetle_stash", 0)
            self.silver_crit_level = data["silver_crit_level"]
            self.silver_crit_chance_level = data.get("silver_crit_chance_level", 1)
            self.auto_flip_level = data.get("auto_flip_level", 0)

            flags = data["flags"]
            self.has_gold_coin = flags["has_gold_coin"]
            self.grab_purchased = flags["grab_purchased"]
            self.gold_explosion_unlocked = flags["gold_explosion_unlocked"]

            levels_data = data.get("levels", {})
            self.bronze_coin_level = levels_data.get("bronze_coin", 1)
            self.silver_coin_level = levels_data.get("silver_coin", 0)
            self.gold_coin_level = levels_data.get("gold_coin", 0)
            self.bronze_value_level = levels_data.get("bronze_value", 0)
            self.silver_value_level = levels_data.get("silver_value", 0)
            self.gold_value_level = levels_data.get("gold_value", 0)
            self.wisp_speed_level = levels_data.get("wisp_speed", 0)
            self.wisp_size_level = levels_data.get("wisp_size", 0)
            self.zone_2_size_level = levels_data.get("zone_2_size", 0)
            self.zone_2_mult_level = levels_data.get("zone_2_mult", 0)
            self.zone_5_size_level = levels_data.get("zone_5_size", 0)
            self.zone_5_mult_level = levels_data.get("zone_5_mult", 0)

            fusions_data = data.get("fusions", {})
            self.silver_fusions_count = fusions_data.get("silver", 0)
            self.gold_fusions_count = fusions_data.get("gold", 0)
            self._update_fusion_buttons()

            self.meteor_unlocked = data.get("meteor_unlocked", False)
            self.meteor_cooldown_level = data.get("meteor_cooldown_level", 0)
            self.tornado_unlocked = data.get("tornado_unlocked", False)
            self.tornado_cooldown_level = data.get("tornado_cooldown_level", 0)

            self.combo_unlocked = data.get("combo_unlocked", False)
            self.combo_limit_level = data.get("combo_limit_level", 0)
            loaded_combo_value = data.get("combo_value", 1.0)
            new_limit = self.combo_base_limit + (self.combo_limit_level * 0.5)
            if new_limit > 10.0: new_limit = 10.0
            self.combo_limit = new_limit
            if loaded_combo_value > self.combo_limit: loaded_combo_value = self.combo_limit
            self.combo_value = loaded_combo_value

            # Загрузка Wisp
            wisp_data = data.get("wisp")
            if wisp_data:
                self.wisp_list.clear()
                self.wisp = Wisp(self.width / 2, self.height / 2, self.assets.wisp_sprites, scale=wisp_data["scale"])
                self.wisp.speed = wisp_data["speed"]
                self.wisp.center_x = wisp_data["x"]
                self.wisp.center_y = wisp_data["y"]
                self.wisp.vx = wisp_data["vx"]
                self.wisp.vy = wisp_data["vy"]
                self.wisp_list.append(self.wisp)

            # Загрузка Зон
            self.zones.clear()
            self.zone_2 = None
            self.zone_5 = None
            for z_data in data["zones"]:
                z_type = z_data.get("type", "unknown")
                if z_type == "zone_2":
                    z = MultiplyZone(self.width, self.height, z_data["multiplier"], (100, 255, 100, 100))
                    self.zone_2 = z
                elif z_type == "zone_5":
                    z = MultiplyZone(self.width, self.height, z_data["multiplier"], (160, 32, 240, 100))
                    self.zone_5 = z
                else:
                    z = MultiplyZone(self.width, self.height, z_data["multiplier"], (0, 0, 0, 0))
                z.size = z_data["size"]
                z.width = z.size
                z.height = z.size
                z.x = z_data["x"]
                z.y = z_data["y"]
                z.vx = z_data["vx"]
                z.vy = z_data["vy"]
                self.zones.append(z)

            # Загрузка Монет
            self.coins.clear()
            for c_data in data["coins"]:
                c_type = c_data["type"]
                coin_value = 1
                if c_type == "bronze":
                    coin_value = self.base_coin_values["bronze"] * (1.5 ** self.bronze_value_level)
                    c = BronzeCoin(c_data["x"], c_data["y"], self.assets.bronze_coin_sprites, value=coin_value,
                                   scale=c_data["scale"], scale_factor=self.scale_factor)
                    c.angle = c_data.get("angle", 0.0)
                elif c_type == "silver":
                    coin_value = self.base_coin_values["silver"] * (1.5 ** self.silver_value_level)
                    crit_chance = 0.01 * self.silver_crit_chance_level
                    c = SilverCoin(c_data["x"], c_data["y"], self.assets.silver_coin_sprites, crit_chance,
                                   value=coin_value, scale=c_data["scale"], scale_factor=self.scale_factor)
                    c.angle = c_data.get("angle", 0.0)
                elif c_type == "gold":
                    coin_value = self.base_coin_values["gold"] * (1.5 ** self.gold_value_level)
                    c = GoldCoin(c_data["x"], c_data["y"], self.assets.gold_coin_sprites, value=coin_value,
                                 scale=c_data["scale"], scale_factor=self.scale_factor)
                    c.angle = c_data.get("angle", 0.0)
                elif c_type == "lucky":
                    c = LuckyCoin(c_data["x"], c_data["y"], self.assets.lucky_coin_sprites, scale=c_data["scale"],
                                  scale_factor=self.scale_factor)
                    c.angle = c_data.get("angle", 0.0)
                elif c_type == "cursed":
                    c = CursedCoin(c_data["x"], c_data["y"], self.assets.cursed_coin_sprites, scale=c_data["scale"],
                                   scale_factor=self.scale_factor)
                    c.angle = c_data.get("angle", 0.0)
                else:
                    continue

                c.vx = c_data["vx"]
                c.vy = c_data["vy"]
                c.is_moving = c_data["is_moving"]
                if c.is_moving:
                    c._select_flying_animation()
                    c.anim_index = 0
                else:
                    c.land()
                    c.landed = False
                self.coins.append(c)

            self._sync_ui_prices()

            # Обновление UI флагов
            if self.tornado_cooldown_level >= 10: self.ui.set_button_disabled("tornado_cooldown_upgrade",
                                                                              "КД Торнадо (Макс.)")
            if self.meteor_cooldown_level >= 10: self.ui.set_button_disabled("meteor_cooldown_upgrade",
                                                                             "КД метеорита (Макс.)")
            if self.silver_crit_chance_level >= 50: self.ui.set_button_disabled("silver_crit_chance_upgrade",
                                                                                "Шанс крита (Макс.)")
            if self.grab_purchased: self.ui.mark_purchased("grab_upgrade")
            if self.gold_explosion_unlocked: self.ui.mark_purchased("gold_explosion_upgrade")
            if self.wisp: self.ui.mark_purchased("wisp_spawn")
            if self.zone_2: self.ui.mark_purchased("spawn_zone_2")
            if self.zone_5: self.ui.mark_purchased("spawn_zone_5")
            if self.meteor_unlocked: self.ui.mark_purchased("spawn_meteor")

            self.ui.update_grab_state(self.has_gold_coin, self.grab_purchased)
            self.ui.update_explosion_state(self.gold_explosion_unlocked)
            self.ui.update_wisp_state(self.wisp is not None)
            self.ui.update_meteor_state(self.meteor_unlocked)
            self.ui.update_zone_state(has_zone_2=(self.zone_2 is not None), has_zone_5=(self.zone_5 is not None))
            return True
        except Exception as e:
            print(f"DEBUG: Error loading game: {e}")
            return False

    def reset_game(self, hard_reset=False) -> bool:
        self.coins.clear()
        self.particles.clear()
        self.zones.clear()
        self.zone_2 = None
        self.zone_5 = None
        self.beetle = None
        self.beetle_stash = 0
        self.wisp = None
        self.wisp_list.clear()
        self.crater = None
        self.meteor = None
        self.explosions.clear()

        self.bronze_coin_level = 1
        self.silver_coin_level = 0
        self.gold_coin_level = 0
        self.bronze_value_level = 0
        self.silver_value_level = 0
        self.gold_value_level = 0
        self.silver_crit_level = 1
        self.silver_crit_chance_level = 1
        self.auto_flip_level = 0
        self.wisp_speed_level = 0
        self.wisp_size_level = 0
        self.zone_2_size_level = 0
        self.zone_2_mult_level = 0
        self.zone_5_size_level = 0
        self.zone_5_mult_level = 0
        self.tornado_cooldown_level = 0
        self.meteor_cooldown_level = 0

        self.has_gold_coin = False
        self.grab_purchased = False
        self.gold_explosion_unlocked = False
        self.meteor_unlocked = False
        self.tornado_unlocked = False

        self.combo_unlocked = False
        self.combo_value = 1.0
        self.combo_limit_level = 0
        self.combo_limit = self.combo_base_limit

        self.silver_fusions_count = 0
        self.gold_fusions_count = 0

        self.balance._value = 0

        self.beetle_respawn_interval = random.uniform(240.0, 300.0)
        self.beetle_respawn_timer = 0.0

        if hard_reset:
            self.prestige = PrestigeManager()
            # ИСправлено: Удаляем через хранилище
            self.storage.delete()
        else:
            self.prestige.reset_run_stats()

        # ВАЖНО: Сброс цен!
        self.upgrade_prices = {}

        self.spawn_coin("bronze")
        self._sync_ui_prices()

        self.ui.reset_all_buttons()
        self._update_prestige_ui()

        self.confirmation_dialog = None
        return True

    def spawn_beetle(self) -> None:
        margin = 50
        x = random.randint(margin, int(self.width - margin))
        y = random.randint(margin, int(self.height - margin))
        self.beetle = Beetle(x, y, self.assets.beetle_sprites, scale_factor=self.scale_factor)

    def kill_beetle(self) -> None:
        if not self.beetle: return

        if self.sound_manager.beetle_dead_sound and not self.sound_manager.muted:
            self.sound_manager.beetle_dead_sound.play()

        # ИСПРАВЛЕНО: Возвращаем накопленное x2
        reward = int(self.beetle_stash * 2)
        self.balance.add(reward)
        self.beetle_stash = 0  # Сброс накопленного

        self.beetle.start_death()

        if reward > 0:
            if reward > 1000000:
                reward_str = f"+{reward / 1000000:.1f}M"
            elif reward > 1000:
                reward_str = f"+{reward / 1000:.1f}K"
            else:
                reward_str = f"+{reward}"
            # Текст зеленый, чтобы было видно, что это награда
            self.create_floating_text(reward_str, self.beetle.center_x, self.beetle.top + 20, (50, 255, 50, 255))

        self.beetle_respawn_interval = random.uniform(240.0, 300.0)  # Следующий через 4-5 мин

    def spawn_beetle_initial(self):
        self.beetle_respawn_interval = random.uniform(360.0, 420.0)
        self.beetle_respawn_timer = 0.0

    def spawn_meteor(self) -> None:
        if self.assets.crater_texture:
            crater_w = self.assets.crater_texture.get_width()
            crater_h = self.assets.crater_texture.get_height()
        else:
            crater_w = 100  # Заглушка если текстуры нет
            crater_h = 100
        half_w = int(crater_w / 2)
        half_h = int(crater_h / 2)

        margin = 50
        min_x = max(margin, half_w)
        max_x = min(self.width - margin, self.width - half_w)
        target_x = random.uniform(min_x, max_x)

        min_y = self.height * 0.4
        max_y = self.height * 0.8
        max_y = min(max_y, self.height - half_h)

        target_y = random.uniform(min_y, max_y)
        start_y = self.height + 100
        self.meteor = Meteor(target_x, start_y, target_y, self.assets.meteor_textures)

    def create_explosion_particles(self, cx: float, cy: float) -> None:
        base_size = 2.0 * self.scale_factor
        size_var = 3.0 * self.scale_factor
        base_speed = 100.0 * self.scale_factor
        speed_var = 300.0 * self.scale_factor

        for _ in range(50):
            red = 255
            green = random.randint(0, 200)
            color = (red, green, 0, 255)
            angle = random.uniform(0, 6.28)
            speed = random.uniform(base_speed, base_speed + speed_var)
            size = random.uniform(base_size, base_size + size_var)
            particle_data = {
                'x': cx, 'y': cy,
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'life': 1.0, 'color': color, 'size': size, 'decay_speed': 2.0
            }
            self.particles.append(particle_data)

    def spawn_tornado(self) -> None:
        margin = self.width / 4
        min_x = margin
        max_x = self.width - margin
        min_y = margin
        max_y = self.height - margin
        target_x = random.uniform(min_x, max_x)
        target_y = random.uniform(min_y, max_y)

        # ИСПРАВЛЕНИЕ: Передаем None, если звук выключен, чтобы Tornado не пытался его воспроизвести
        tornado_sound = None if self.sound_manager.muted else self.sound_manager.tornado_sound

        self.tornado = Tornado(target_x, target_y, self.assets.tornado_textures, tornado_sound,
                               scale=2.0 * self.scale_factor, world_scale=self.scale_factor, world_width=self.width)
        self.tornado.pull_radius = (self.width / 3.0) * self.scale_factor
        self.tornado_list.clear()
        self.tornado_list.append(self.tornado)

    def get_coin_counts(self) -> dict:
        counts = {
            "bronze": 0, "silver": 0, "gold": 0,
            # Добавляем данные о слияниях для UI
            "silver_fusions": self.silver_fusions_count,
            "max_silver_fusions": self.max_silver_fusions,
            "gold_fusions": self.gold_fusions_count,
            "max_gold_fusions": self.max_gold_fusions
        }
        for coin in self.coins:
            if isinstance(coin, BronzeCoin):
                counts["bronze"] += 1
            elif isinstance(coin, SilverCoin):
                counts["silver"] += 1
            elif isinstance(coin, GoldCoin):
                counts["gold"] += 1
        return counts

    def create_fusion_flash(self, cx: float, cy: float, fusion_type: str) -> None:
        if fusion_type == "silver":
            color = (200, 240, 255, 255)
        elif fusion_type == "gold":
            color = (255, 215, 0, 255)
        else:
            color = (255, 255, 255, 255)

        base_size = 4.0 * self.scale_factor
        size_var = 6.0 * self.scale_factor
        base_speed = 400.0 * self.scale_factor
        speed_var = 400.0 * self.scale_factor

        for _ in range(50):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(base_speed, base_speed + speed_var)
            size = random.uniform(base_size, base_size + size_var)
            particle_data = {
                'x': cx, 'y': cy,
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'life': 1, 'color': color, 'size': size, 'decay_speed': 2.5
            }
            self.particles.append(particle_data)

    def _get_coin_color(self, coin):
        if isinstance(coin, LuckyCoin):
            return (50, 255, 50, 255)
        elif isinstance(coin, CursedCoin):
            return (100, 50, 50, 255)
        elif isinstance(coin, GoldCoin):
            return (255, 215, 0, 255)
        elif isinstance(coin, SilverCoin):
            return (192, 192, 192, 255)
        else:
            return (181, 166, 66, 255)

    def create_floating_text(self, text: str, x: float, y: float, color: tuple, coin=None) -> None:
        # Сохраняем только данные, текст рендерим в draw()
        self.floating_texts.append({
            'text': text, 'life': 1.5, 'base_color': color,
            'linked_coin': coin, 'vx': 30, 'vy': 50, 'x': x, 'y': y
        })

    def create_combo_fire_particles(self) -> None:
        combo_x = 60 * self.scale_factor
        combo_y = self.height - (60 * self.scale_factor)
        spawn_center_offset = 60 * self.scale_factor

        base_size = 3.0 * self.scale_factor
        size_var = 3.0 * self.scale_factor
        base_speed = 20.0 * self.scale_factor
        speed_var = 40.0 * self.scale_factor

        for _ in range(2):
            red_comp = 255
            green_comp = random.randint(0, 100)
            color = (red_comp, green_comp, 0, 200)
            angle = random.uniform(4.5, 5.0)
            speed = random.uniform(base_speed, base_speed + speed_var)
            size = random.uniform(base_size, base_size + size_var)
            offset_x = random.uniform(-40, 40)
            offset_y = random.uniform(-10, 10)
            particle_data = {
                'x': combo_x + spawn_center_offset + offset_x,
                'y': combo_y + offset_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 0.8, 'color': color, 'size': size, 'decay_speed': 2.0
            }
            self.particles.append(particle_data)

    def _add_income(self, amount: int) -> None:
        if amount <= 0: return
        # Применяем множитель престижа
        final_amount = int(amount * self.prestige.multiplier)

        # Добавляем в статистику для престижа
        self.prestige.add_income(final_amount)

        # === ЛОГИКА ЖУКА (75% в тайник, 25% на баланс) ===
        if self.beetle:
            kept = int(final_amount * 0.25)
            stolen = final_amount - kept
            self.balance.add(kept)
            self.beetle_stash += stolen
        else:
            self.balance.add(final_amount)

    def _update_fusion_buttons(self):
        """Обновляет состояние кнопок слияния в UI, убрали установку русского текста."""
        # Теперь UI сам формирует текст на основе данных из get_coin_counts
        # Эта функция остается пустой или можно удалить её вызовы,
        # но для безопасности оставим её пустой, чтобы не ломать вызовы из load_game/reset_game.
        pass

    def _calculate_price(self, base_id: str, level: int) -> int:
        base = self.base_prices.get(base_id, 100)
        mult = self.price_mult.get(base_id, 1.15) # По умолчанию 1.15, если ключ забыт
        return int(base * (mult ** level))

    def _get_current_level(self, upgrade_id):
        if upgrade_id == "bronze_value_upgrade": return self.bronze_value_level
        if upgrade_id == "silver_value_upgrade": return self.silver_value_level
        if upgrade_id == "gold_value_upgrade": return self.gold_value_level
        if upgrade_id == "silver_crit_upgrade": return self.silver_crit_level
        if upgrade_id == "silver_crit_chance_upgrade": return self.silver_crit_chance_level
        if upgrade_id == "auto_flip_upgrade": return self.auto_flip_level
        if upgrade_id == "wisp_speed": return self.wisp_speed_level
        if upgrade_id == "wisp_size": return self.wisp_size_level
        if upgrade_id == "upgrade_combo_limit": return self.combo_limit_level
        if upgrade_id == "upgrade_zone_2_size": return self.zone_2_size_level
        if upgrade_id == "upgrade_zone_2_mult": return self.zone_2_mult_level
        if upgrade_id == "upgrade_zone_5_size": return self.zone_5_size_level
        if upgrade_id == "upgrade_zone_5_mult": return self.zone_5_mult_level
        if upgrade_id == "tornado_cooldown_upgrade": return self.tornado_cooldown_level
        if upgrade_id == "meteor_cooldown_upgrade": return self.meteor_cooldown_level
        if upgrade_id == "buy_bronze_coin": return self.bronze_coin_level
        return 0

    def _update_prestige_ui(self):
        gain = self.prestige.calculate_gain()
        # Принудительно обновляем кнопку в UI
        self.ui.update_prestige_button(gain, self.prestige.points, self.prestige.multiplier)

    def perform_prestige(self):
        if self.prestige.can_prestige():
            # gain = self.prestige.calculate_gain() # Можно использовать для анимации
            self.prestige.add_point()

            # ВАЖНО: Сбрасываем счетчик заработанного для престижа!
            self.prestige.reset_run_stats()

            # Полный сброс игры
            self.coins.clear()
            self.particles.clear()
            self.zones.clear()
            self.zone_2 = None
            self.zone_5 = None
            self.beetle = None
            self.beetle_stash = 0
            self.wisp = None
            self.wisp_list.clear()
            self.crater = None
            self.meteor = None
            self.explosions.clear()

            self.bronze_coin_level = 1
            self.silver_coin_level = 0
            self.gold_coin_level = 0
            self.bronze_value_level = 0
            self.silver_value_level = 0
            self.gold_value_level = 0
            self.silver_crit_level = 1
            self.silver_crit_chance_level = 1
            self.auto_flip_level = 0
            self.wisp_speed_level = 0
            self.wisp_size_level = 0
            self.zone_2_size_level = 0
            self.zone_2_mult_level = 0
            self.zone_5_size_level = 0
            self.zone_5_mult_level = 0
            self.tornado_cooldown_level = 0
            self.meteor_cooldown_level = 0
            self.has_gold_coin = False
            self.grab_purchased = False
            self.gold_explosion_unlocked = False
            self.meteor_unlocked = False
            self.tornado_unlocked = False
            self.combo_unlocked = False
            self.combo_value = 1.0
            self.combo_limit_level = 0
            self.combo_limit = self.combo_base_limit
            self.silver_fusions_count = 0
            self.gold_fusions_count = 0
            self.balance._value = 0
            self.upgrade_prices = {}  # Сброс цен

            self.spawn_coin("bronze")
            self._sync_ui_prices()
            self.ui.reset_all_buttons()

            # Принудительно обновляем UI престижа сразу после сброса
            self._update_prestige_ui()

            self.beetle_respawn_interval = random.uniform(240.0, 300.0)
            return True
        return False