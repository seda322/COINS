import pygame
import sys
import os
import random
import math

from logic.assets.asset_manager import AssetManager
from logic.assets.sound_manager import SoundManager
from logic.controllers.ui_controller import UIController
from logic.controllers.game_controller import GameController
from logic.assets.sprite_pygame import PygameSprite

# ВАЖНО: Импортируем модуль целиком, чтобы видеть изменения current_lang
import localization

# --- КОНСТАНТЫ ---
VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080
PANEL_WIDTH = 500
WORLD_WIDTH = VIRTUAL_WIDTH - PANEL_WIDTH
FPS = 60
TITLE = "Incremental Coin Game (Pygame)"

STATE_MENU = 0
STATE_GAME = 1


class MenuCoin(PygameSprite):
    """
    Монетка для главного меню. Наследуется от PygameSprite для качественного рендера.
    """

    def __init__(self, x, y, sprites_dict, scale=1.0):
        # 1. Инициализация спрайта
        start_face = random.choice(["heads", "tails"])
        start_tex = sprites_dict.get(start_face)
        if not start_tex:
            start_tex = pygame.Surface((64, 64), pygame.SRCALPHA)
            start_tex.fill((255, 0, 0))

        super().__init__(image=start_tex, scale=scale)

        self.center_x = x
        self.center_y = y

        self.sprites = sprites_dict
        self.base_width = start_tex.get_width()

        # Радиус коллизии (45% от ширины визуала)
        self.radius = (self.base_width * scale) * 0.45

        # Физика
        speed = 150 * scale
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        # Состояние
        self.is_moving = False  # False = скольжение, True = полет

        # Анимация
        self.anim = []
        self.anim_index = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.05

        # --- ЛОГИКА ТАЙМЕРА ---
        self.timer = 0.0
        self.next_action_time = random.uniform(0, 8.0)  # Время первого подброса
        self.is_cooldown = False  # Флаг фазы (False = окно подброса, True = кд 4 сек)

    def update(self, dt, width, height):
        # --- 1. Логика Таймера и Подброса ---
        if not self.is_moving:
            self.timer += dt

            if self.is_cooldown:
                # Фаза ожидания после приземления (4 секунды)
                if self.timer >= 4.0:
                    self.is_cooldown = False
                    self.timer = 0.0
                    self.next_action_time = random.uniform(0, 8.0)
            else:
                # Фаза ожидания подброса (окно 8 секунд)
                if self.timer >= self.next_action_time:
                    self._do_toss()

        # --- 2. Физика ---
        if self.is_moving:
            # === ПОЛЕТ ===
            self.center_x += self.vx * dt
            self.center_y += self.vy * dt

            # Отскок от стен
            if self.left < 0:
                self.left = 0
                self.vx = abs(self.vx)
            elif self.right > width:
                self.right = width
                self.vx = -abs(self.vx)

            if self.bottom < 0:
                self.bottom = 0
                self.vy = abs(self.vy)
            elif self.top > height:
                self.top = height
                self.vy = -abs(self.vy)

            # Анимация
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.anim_index += 1

                # ПРИЗЕМЛЕНИЕ: Сразу после последнего кадра
                if self.anim_index >= len(self.anim):
                    self.land()
        else:
            # === СКОЛЬЖЕНИЕ ===
            self.center_x += self.vx * dt
            self.center_y += self.vy * dt

            # Отскок от стен
            if self.left < 0:
                self.left = 0
                self.vx *= -1
            elif self.right > width:
                self.right = width
                self.vx *= -1

            if self.bottom < 0:
                self.bottom = 0
                self.vy *= -1
            elif self.top > height:
                self.top = height
                self.vy *= -1

    def _do_toss(self):
        """Запуск подбрасывания"""
        self.is_moving = True

        force = random.uniform(600, 900)
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * force
        self.vy = math.sin(angle) * force

        self._select_flying_animation()
        self.anim_index = 0
        self.anim_timer = 0

    def land(self):
        """Приземление"""
        self.is_moving = False

        # Смена текстуры на статичную (орел/решка)
        if random.random() < 0.5:
            self.texture = self.sprites.get("heads")
        else:
            self.texture = self.sprites.get("tails")

        # Запуск кулдауна (4 секунды)
        self.is_cooldown = True
        self.timer = 0.0

    def _select_flying_animation(self):
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
            self.anim = [self.sprites.get("heads")]

    def draw(self, surface, screen_height):
        # --- ОБНОВЛЕНИЕ ТЕКСТУРЫ ДЛЯ АНИМАЦИИ ---
        if self.is_moving:
            if self.anim and self.anim_index < len(self.anim):
                self.texture = self.anim[self.anim_index]

            # Тень
            shadow_radius = int(self.width * 0.55)
            shadow_surf = pygame.Surface((shadow_radius * 2, shadow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (0, 0, 0, 50), (shadow_radius, shadow_radius), shadow_radius)

            draw_y = int(screen_height - self.center_y)
            surface.blit(shadow_surf, (int(self.center_x - shadow_radius), draw_y + 10 - shadow_radius))

        # Отрисовка самой монетки
        super().draw(surface, screen_height)


def _handle_menu_collisions(coins):
    """
    Коллизия только для скользящих монет.
    Летающие монеты (is_moving=True) игнорируют столкновения.
    """
    n = len(coins)
    for i in range(n):
        for j in range(i + 1, n):
            c1 = coins[i]
            c2 = coins[j]

            # ЕСЛИ ХОТЯ БЫ ОДНА ЛЕТИТ - КОЛЛИЗИИ НЕТ (ПРОЛЕТАЮТ СКВОЗЬ)
            if c1.is_moving or c2.is_moving:
                continue

            # Стандартная физика для "наземных" монет
            dx = c2.center_x - c1.center_x
            dy = c2.center_y - c1.center_y
            dist_sq = dx * dx + dy * dy
            min_dist = c1.radius + c2.radius

            if dist_sq < min_dist * min_dist and dist_sq > 0:
                dist = math.sqrt(dist_sq)

                nx = dx / dist
                ny = dy / dist

                overlap = min_dist - dist
                c1.center_x -= nx * overlap * 0.5
                c1.center_y -= ny * overlap * 0.5
                c2.center_x += nx * overlap * 0.5
                c2.center_y += ny * overlap * 0.5

                dvx = c1.vx - c2.vx
                dvy = c1.vy - c2.vy
                dot = dvx * nx + dvy * ny

                if dot > 0:
                    c1.vx -= dot * nx
                    c1.vy -= dot * ny
                    c2.vx += dot * nx
                    c2.vy += dot * ny


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    info = pygame.display.Info()
    start_w = int(info.current_w * 0.8)
    start_h = int(info.current_h * 0.8)
    screen = pygame.display.set_mode((start_w, start_h), pygame.RESIZABLE)
    pygame.display.set_caption(TITLE)

    canvas = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    clock = pygame.time.Clock()

    print("Initializing Managers...")
    asset_manager = AssetManager()
    asset_manager.load_all()
    asset_manager.load_ui_assets()

    sound_manager = SoundManager()
    sound_manager.load_all()

    font_path = asset_manager.ui_assets.get("font_name", "Arial")
    try:
        if font_path != "Arial" and os.path.exists(font_path):
            main_font = pygame.font.Font(font_path, 20)
            title_font = pygame.font.Font(font_path, 40)
        else:
            main_font = pygame.font.SysFont("Arial", 20)
            title_font = pygame.font.SysFont("Arial", 40)
    except:
        main_font = pygame.font.SysFont("Arial", 20)
        title_font = pygame.font.SysFont("Arial", 40)

    scale_factor = 1.0
    ui = UIController(
        panel_x=WORLD_WIDTH,
        panel_width=PANEL_WIDTH,
        panel_height=VIRTUAL_HEIGHT,
        ui_assets=asset_manager.ui_assets,
        scale_factor=scale_factor
    )

    game = GameController(
        asset_manager=asset_manager,
        ui_controller=ui,
        sound_manager=sound_manager,
        world_width=WORLD_WIDTH,
        world_height=VIRTUAL_HEIGHT,
        scale_factor=scale_factor
    )

    state = STATE_MENU
    running = True

    has_save = False
    save_path = game.get_save_path()
    if os.path.exists(save_path):
        if game.load_game():
            has_save = True
        else:
            try:
                os.remove(save_path)
            except:
                pass

    menu_coins = []

    def spawn_menu_coins():
        menu_coins.clear()

        def add_batch(sprites_dict, count, scale):
            if not sprites_dict: return
            for _ in range(count):
                x = random.randint(100, int(VIRTUAL_WIDTH - 100))
                y = random.randint(100, int(VIRTUAL_HEIGHT - 100))
                menu_coins.append(MenuCoin(x, y, sprites_dict, scale))

        add_batch(asset_manager.bronze_coin_sprites, 15, 0.8)
        add_batch(asset_manager.silver_coin_sprites, 8, 1.0)
        add_batch(asset_manager.gold_coin_sprites, 4, 1.2)

    spawn_menu_coins()

    btn_w, btn_h = 300, 70
    cx, cy = VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2
    btn_play_rect = pygame.Rect(cx - btn_w // 2, cy, btn_w, btn_h)
    btn_help_rect = pygame.Rect(cx - btn_w // 2, cy + 90, btn_w, btn_h)

    # Кнопки настроек в МЕНЮ
    settings_btn_w = 100
    settings_btn_h = 50
    settings_margin = 20
    btn_lang_rect = pygame.Rect(VIRTUAL_WIDTH - settings_btn_w - settings_margin, settings_margin, settings_btn_w,
                                settings_btn_h)
    btn_sound_rect = pygame.Rect(VIRTUAL_WIDTH - (settings_btn_w * 2) - (settings_margin * 2), settings_margin,
                                 settings_btn_w, settings_btn_h)

    # Кнопки настроек в ИГРЕ
    game_btn_w = 110
    game_btn_h = 50
    game_btn_margin = 20
    game_mute_rect = pygame.Rect(VIRTUAL_WIDTH - game_btn_w - game_btn_margin, game_btn_margin, game_btn_w, game_btn_h)
    game_lang_rect = pygame.Rect(VIRTUAL_WIDTH - (game_btn_w * 2) - (game_btn_margin * 2), game_btn_margin, game_btn_w,
                                 game_btn_h)

    show_help = False
    help_scroll_y = 0
    help_w, help_h = 600, 400

    # --- ГЛАВНЫЙ ЦИКЛ ---
    while running:
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.1: dt = 0.1

        mx, my = pygame.mouse.get_pos()
        vmx = mx * (VIRTUAL_WIDTH / screen.get_width())
        vmy = my * (VIRTUAL_HEIGHT / screen.get_height())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if state == STATE_GAME: game.save_game()
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if state == STATE_MENU:
                    if show_help:
                        help_x = (VIRTUAL_WIDTH - help_w) // 2
                        help_y = (VIRTUAL_HEIGHT - help_h) // 2
                        close_btn_size = 30
                        close_rect = pygame.Rect(help_x + help_w - close_btn_size - 10, help_y + 10, close_btn_size,
                                                 close_btn_size)
                        if close_rect.collidepoint(vmx, vmy):
                            show_help = False
                            continue
                    else:
                        if btn_play_rect.collidepoint(vmx, vmy):
                            state = STATE_GAME
                            if not has_save: game.reset_game()
                        elif btn_help_rect.collidepoint(vmx, vmy):
                            show_help = True
                        elif btn_lang_rect.collidepoint(vmx, vmy):
                            localization.toggle_language()
                            ui.reload_texts()
                            # УБРАНО: spawn_menu_coins() - монетки больше не сбрасываются
                        elif btn_sound_rect.collidepoint(vmx, vmy):
                            sound_manager.toggle_mute()

                elif state == STATE_GAME:
                    logic_y = VIRTUAL_HEIGHT - vmy
                    if event.button == pygame.BUTTON_LEFT:
                        if game_mute_rect.collidepoint(vmx, vmy):
                            sound_manager.toggle_mute()
                        elif game_lang_rect.collidepoint(vmx, vmy):
                            localization.toggle_language()
                            ui.reload_texts()
                        elif vmx > WORLD_WIDTH:
                            ui.on_mouse_press(vmx, vmy)
                        else:
                            game.on_mouse_press(vmx, logic_y, pygame.BUTTON_LEFT)
                    elif event.button == pygame.BUTTON_RIGHT:
                        if vmx <= WORLD_WIDTH:
                            game.on_mouse_press_rmb(vmx, logic_y)

            elif event.type == pygame.MOUSEBUTTONUP:
                if state == STATE_GAME:
                    logic_y = VIRTUAL_HEIGHT - vmy
                    if event.button == pygame.BUTTON_RIGHT:
                        game.on_mouse_release_rmb(vmx, logic_y)
                    elif event.button == pygame.BUTTON_LEFT:
                        if vmx > WORLD_WIDTH:
                            if not (game_mute_rect.collidepoint(vmx, vmy) or game_lang_rect.collidepoint(vmx, vmy)):
                                upgrade_id = ui.on_mouse_release(vmx, vmy)
                                if upgrade_id:
                                    if upgrade_id == "finish_game":
                                        game.save_game()
                                        running = False
                                    else:
                                        game.try_buy_upgrade(upgrade_id)

            elif event.type == pygame.MOUSEMOTION:
                if state == STATE_GAME:
                    logic_y = VIRTUAL_HEIGHT - vmy
                    game.on_mouse_motion(vmx, logic_y, event.rel[0] * (VIRTUAL_WIDTH / screen.get_width()),
                                         -event.rel[1] * (VIRTUAL_HEIGHT / screen.get_height()))

            elif event.type == pygame.MOUSEWHEEL:
                if state == STATE_MENU and show_help:
                    help_scroll_y += event.y * 30
                    if help_scroll_y < 0: help_scroll_y = 0
                elif state == STATE_GAME:
                    if vmx > WORLD_WIDTH:
                        ui.on_mouse_scroll(vmx, vmy, event.y)

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

        # UPDATE
        if state == STATE_MENU:
            for c in menu_coins:
                c.update(dt, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
            _handle_menu_collisions(menu_coins)
        elif state == STATE_GAME:
            game.update(dt)
            ui.update(game.balance.get(), game.get_coin_counts())

        # DRAW
        canvas.fill((255, 255, 255))

        if state == STATE_MENU:
            sorted_coins = sorted(menu_coins, key=lambda c: c.is_moving)

            for c in sorted_coins:
                c.draw(canvas, VIRTUAL_HEIGHT)

            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 50))
            canvas.blit(overlay, (0, 0))

            if not show_help:
                title_surf = title_font.render(localization.get_text("menu_title"), True, (0, 0, 0))
                title_rect = title_surf.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT * 0.2))
                canvas.blit(title_surf, title_rect)

                buttons = [(btn_play_rect, localization.get_text("btn_play")),
                           (btn_help_rect, localization.get_text("btn_help"))]
                for rect, text in buttons:
                    color = (100, 100, 100) if rect.collidepoint(vmx, vmy) else (50, 50, 50)
                    pygame.draw.rect(canvas, color, rect, border_radius=5)
                    pygame.draw.rect(canvas, (200, 200, 200), rect, 2, border_radius=5)
                    txt_surf = main_font.render(text, True, (255, 255, 255))
                    txt_rect = txt_surf.get_rect(center=rect.center)
                    canvas.blit(txt_surf, txt_rect)

                lang_key = "lang_" + localization.current_lang
                lang_text = localization.get_text(lang_key)

                sound_state = "ON" if not sound_manager.muted else "OFF"
                sound_text_final = f"SOUND: {sound_state}"

                for rect, text in [(btn_lang_rect, lang_text), (btn_sound_rect, sound_text_final)]:
                    color = (70, 70, 70) if rect.collidepoint(vmx, vmy) else (50, 50, 50)
                    pygame.draw.rect(canvas, color, rect, border_radius=5)
                    pygame.draw.rect(canvas, (150, 150, 150), rect, 2, border_radius=5)
                    txt_surf = main_font.render(text, True, (255, 255, 255))
                    txt_rect = txt_surf.get_rect(center=rect.center)
                    canvas.blit(txt_surf, txt_rect)

            else:
                help_x = (VIRTUAL_WIDTH - help_w) // 2
                help_y = (VIRTUAL_HEIGHT - help_h) // 2
                pygame.draw.rect(canvas, (30, 30, 30), (help_x, help_y, help_w, help_h))
                pygame.draw.rect(canvas, (255, 255, 255), (help_x, help_y, help_w, help_h), 2)

                help_lines = [
                    localization.get_text("help_goal"), localization.get_text("help_goal_text"), "",
                    localization.get_text("help_gameplay"), localization.get_text("help_gameplay_text"), "",
                    localization.get_text("help_fusion"), localization.get_text("help_fusion_text"), "",
                    localization.get_text("help_luck")
                ]

                clip_rect = pygame.Rect(help_x, help_y, help_w, help_h)
                canvas.set_clip(clip_rect)

                text_y = help_y + 20 + help_scroll_y
                for line in help_lines:
                    if "\n" in line:
                        parts = line.split("\n")
                        for part in parts:
                            l_surf = main_font.render(part, True, (200, 200, 200))
                            canvas.blit(l_surf, (help_x + 20, text_y))
                            text_y += 25
                    else:
                        l_surf = main_font.render(line, True, (200, 200, 200))
                        canvas.blit(l_surf, (help_x + 20, text_y))
                    text_y += 25

                canvas.set_clip(None)

                close_btn_size = 30
                close_rect = pygame.Rect(help_x + help_w - close_btn_size - 10, help_y + 10, close_btn_size,
                                         close_btn_size)
                pygame.draw.rect(canvas, (200, 50, 50), close_rect, border_radius=5)
                x_surf = main_font.render(localization.get_text("btn_close"), True, (255, 255, 255))
                canvas.blit(x_surf, x_surf.get_rect(center=close_rect.center))

        elif state == STATE_GAME:
            game.draw(canvas, VIRTUAL_HEIGHT)
            ui.draw(canvas, VIRTUAL_HEIGHT, game.balance.get())

            lang_key = "lang_" + localization.current_lang
            lang_text = localization.get_text(lang_key)

            lang_color = (80, 80, 80) if game_lang_rect.collidepoint(vmx, vmy) else (60, 60, 60)
            pygame.draw.rect(canvas, lang_color, game_lang_rect, border_radius=5)
            pygame.draw.rect(canvas, (150, 150, 150), game_lang_rect, 2, border_radius=5)
            lang_surf = main_font.render(lang_text, True, (255, 255, 255))
            canvas.blit(lang_surf, lang_surf.get_rect(center=game_lang_rect.center))

            sound_state = "ON" if not sound_manager.muted else "OFF"
            sound_text = f"SOUND: {sound_state}"

            sound_color = (80, 80, 80) if game_mute_rect.collidepoint(vmx, vmy) else (60, 60, 60)
            pygame.draw.rect(canvas, sound_color, game_mute_rect, border_radius=5)
            pygame.draw.rect(canvas, (150, 150, 150), game_mute_rect, 2, border_radius=5)
            sound_surf = main_font.render(sound_text, True, (255, 255, 255))
            canvas.blit(sound_surf, sound_surf.get_rect(center=game_mute_rect.center))

        pygame.transform.smoothscale(canvas, (screen.get_width(), screen.get_height()), screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()