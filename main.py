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

# === РЕЖИМ РАЗРАБОТЧИКА ===
# Установите True, чтобы видеть админ-панель при тестах.
# Установите False перед публикацией игры!
DEBUG_MODE = True


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

    # === ИНИЦИАЛИЗАЦИЯ ЯЗЫКА (ПОДКЛЮЧАЕМ ЯНДЕКС ПОМОЩНИК) ===
    # Импортируем и запускаем определение языка
    import yandex_helper
    yandex_helper.initialize_environment()

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

    # === ПРОВЕРКА УСТРОЙСТВА ===
    # Вычисляем один раз при старте
    game.is_mobile_device = yandex_helper.is_mobile()
    print(f"Is Mobile Device: {game.is_mobile_device}")

    state = STATE_MENU
    running = True

    has_save = False
    # save_path теперь не нужен, GC сам управляет хранилищем
    # Проверяем наличие сохранения через контроллер (он использует storage)
    if game.load_game():
        has_save = True

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

    # --- АДМИН-ПАНЕЛЬ (Кнопки) ---
    admin_btn_w = 200
    admin_btn_h = 40
    admin_x = 10
    admin_y = 10

    admin_btn_lucky = pygame.Rect(admin_x, admin_y, admin_btn_w, admin_btn_h)
    admin_btn_cursed = pygame.Rect(admin_x, admin_y + 50, admin_btn_w, admin_btn_h)
    admin_btn_money = pygame.Rect(admin_x, admin_y + 100, admin_btn_w, admin_btn_h)
    admin_btn_beetle = pygame.Rect(admin_x, admin_y + 150, admin_btn_w, admin_btn_h)

    show_help = False
    help_scroll_y = 0
    help_w, help_h = 600, 400
    # Добавьте эти переменные (аналоги игровых)
    is_dragging_help = False
    help_last_drag_y = 0

    # --- ГЛАВНЫЙ ЦИКЛ ---
    active_dialog = None

    # Переменные для Drag & Drop скролла (Игра)
    is_dragging_ui = False
    last_drag_y = 0
    potential_click = False

    # Переменные для скролла помощи (Меню)
    help_dragging = False
    help_last_y = 0

    while running:
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.1: dt = 0.1

        mx, my = pygame.mouse.get_pos()
        vmx = int(mx * (VIRTUAL_WIDTH / screen.get_width()))
        vmy = int(my * (VIRTUAL_HEIGHT / screen.get_height()))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if state == STATE_GAME: game.save_game()
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if state == STATE_MENU:
                    # === ЛОГИКА МЕНЮ ===
                    if show_help:
                        help_x = (VIRTUAL_WIDTH - help_w) // 2
                        help_y = (VIRTUAL_HEIGHT - help_h) // 2
                        close_rect = pygame.Rect(help_x + help_w - 40, help_y + 10, 30, 30)
                        if close_rect.collidepoint(vmx, vmy):
                            show_help = False
                            continue

                        # Логика как в игре: Захват
                        help_rect = pygame.Rect(help_x, help_y, help_w, help_h)
                        if help_rect.collidepoint(vmx, vmy):
                            is_dragging_help = True
                            help_last_drag_y = vmy
                    else:
                        if btn_play_rect.collidepoint(vmx, vmy):
                            state = STATE_GAME
                            if not has_save: game.reset_game()
                        elif btn_help_rect.collidepoint(vmx, vmy):
                            show_help = True
                        elif btn_lang_rect.collidepoint(vmx, vmy):
                            localization.toggle_language()
                            ui.reload_texts()
                        elif btn_sound_rect.collidepoint(vmx, vmy):
                            sound_manager.toggle_mute()

                elif state == STATE_GAME:
                    # === ЛОГИКА ДИАЛОГОВ ===
                    if active_dialog:
                        dialog_w, dialog_h = 500, 250
                        dialog_x = (VIRTUAL_WIDTH - dialog_w) // 2
                        dialog_y = (VIRTUAL_HEIGHT - dialog_h) // 2
                        btn_w_d, btn_h_d = 120, 50
                        btn_yes = pygame.Rect(dialog_x + 50, dialog_y + dialog_h - 70, btn_w_d, btn_h_d)
                        btn_no = pygame.Rect(dialog_x + dialog_w - 170, dialog_y + dialog_h - 70, btn_w_d, btn_h_d)
                        btn_close_d = pygame.Rect(dialog_x + dialog_w - 40, dialog_y + 10, 30, 30)

                        if event.button == pygame.BUTTON_LEFT:
                            if btn_yes.collidepoint(vmx, vmy):
                                if active_dialog == 'prestige':
                                    game.perform_prestige()
                                elif active_dialog == 'new_game':
                                    game.reset_game(hard_reset=False)
                                active_dialog = None
                            elif btn_no.collidepoint(vmx, vmy) or btn_close_d.collidepoint(vmx, vmy):
                                active_dialog = None
                        continue

                    # === ОСНОВНАЯ ИГРОВАЯ ЛОГИКА ===
                    logic_y = VIRTUAL_HEIGHT - vmy

                    # === АДМИН-ПАНЕЛЬ (ТОЛЬКО ДЛЯ РАЗРАБОТЧИКА) ===
                    if DEBUG_MODE:
                        if event.button == pygame.BUTTON_LEFT:
                            admin_y_start = VIRTUAL_HEIGHT - 60 - 220 - 20
                            admin_btn_lucky = pygame.Rect(10, admin_y_start + 10, 200, 40)
                            admin_btn_cursed = pygame.Rect(10, admin_y_start + 60, 200, 40)
                            admin_btn_money = pygame.Rect(10, admin_y_start + 110, 200, 40)
                            admin_btn_beetle = pygame.Rect(10, admin_y_start + 160, 200, 40)

                            if admin_btn_lucky.collidepoint(vmx, vmy):
                                game.spawn_coin("lucky", vmx, logic_y)
                                continue
                            elif admin_btn_cursed.collidepoint(vmx, vmy):
                                game.spawn_coin("cursed", vmx, logic_y)
                                continue
                            elif admin_btn_money.collidepoint(vmx, vmy):
                                amount = 1_000_000_000_000_000_000_000_000
                                game.balance.add(amount)
                                game.prestige.add_income(amount)
                                continue
                            elif admin_btn_beetle.collidepoint(vmx, vmy):
                                game.spawn_beetle()
                                continue

                    if event.button == pygame.BUTTON_LEFT:
                        # Кнопка захвата
                        if game.grab_purchased and game.is_mobile_device:
                            grab_btn_rect = pygame.Rect(game_lang_rect.x - 120, game_btn_margin, 100, game_btn_h)
                            if grab_btn_rect.collidepoint(vmx, vmy):
                                game.grab_mode_active = not game.grab_mode_active
                                continue

                        # Звук и Язык
                        if game_mute_rect.collidepoint(vmx, vmy):
                            sound_manager.toggle_mute()
                        elif game_lang_rect.collidepoint(vmx, vmy):
                            localization.toggle_language()
                            ui.reload_texts()

                        # === ЛОГИКА UI (Скролл/Клик) ===
                        elif vmx > WORLD_WIDTH:
                            # 1. Сначала "нажимаем"
                            ui.on_mouse_press(vmx, vmy)

                            # 2. Проверяем результат
                            pressed_id = ui.get_pressed_button_id()

                            if pressed_id:
                                # Мы попали в кнопку
                                if ui.is_button_enabled(pressed_id):
                                    # Кнопка активна -> это КЛИК
                                    potential_click = True
                                    # is_dragging_ui остается False
                                else:
                                    # Кнопка неактивна -> это СКРОЛЛ
                                    potential_click = False
                                    is_dragging_ui = True
                                    last_drag_y = vmy
                                    ui.cancel_press()
                            else:
                                # Попали в фон -> это СКРОЛЛ
                                potential_click = False
                                is_dragging_ui = True
                                last_drag_y = vmy

                        # Клик по полю
                        else:
                            game.on_mouse_press(vmx, logic_y, pygame.BUTTON_LEFT)

                    elif event.button == pygame.BUTTON_RIGHT:
                        if vmx <= WORLD_WIDTH:
                            game.on_mouse_press_rmb(vmx, logic_y)

            elif event.type == pygame.MOUSEBUTTONUP:
                # Сброс перетаскивания меню помощи
                if state == STATE_MENU:
                    is_dragging_help = False
                if state == STATE_GAME and not active_dialog:
                    logic_y = VIRTUAL_HEIGHT - vmy
                    if event.button == pygame.BUTTON_RIGHT:
                        game.on_mouse_release_rmb(vmx, logic_y)
                    elif event.button == pygame.BUTTON_LEFT:
                        # === ОБРАБОТКА РЕЖИМА ЗАХВАТА ===
                        if game.grab_purchased and game.grab_mode_active:
                            if game.grabbed_coin:
                                game.on_mouse_release_rmb(vmx, logic_y)
                            else:
                                game.on_mouse_press_rmb(vmx, logic_y)
                            continue

                        # Сброс скролла
                        is_dragging_ui = False

                        # Обработка клика (если был начат клик и не перешел в скролл)
                        if potential_click:
                            potential_click = False
                            if vmx > WORLD_WIDTH:
                                if not (game_mute_rect.collidepoint(vmx, vmy) or game_lang_rect.collidepoint(vmx, vmy)):
                                    upgrade_id = ui.on_mouse_release(vmx, vmy)
                                    if upgrade_id:
                                        if upgrade_id == "prestige":
                                            if game.prestige.can_prestige():
                                                active_dialog = 'prestige'
                                        elif upgrade_id == "new_game":
                                            active_dialog = 'new_game'
                                        elif upgrade_id == "exit_to_menu":
                                            game.save_game()
                                            state = STATE_MENU
                                            has_save = True
                                        elif upgrade_id == "finish_game":
                                            game.save_game()
                                            running = False
                                        else:
                                            game.try_buy_upgrade(upgrade_id)

            elif event.type == pygame.MOUSEMOTION:
                # === МЕНЮ ПОМОЩИ (Перетаскивание - ТОЧНО КАК В ИГРЕ) ===
                if state == STATE_MENU and show_help and is_dragging_help:
                    dy = vmy - help_last_drag_y

                    # === ПОВТОРЯЕМ ЛОГИКУ ИГРЫ ===
                    # В игре: ui.on_mouse_scroll(vmx, vmy, dy * 0.05)
                    # В UI: scroll_y -= val * 20.
                    # Итого: scroll_y -= dy.
                    # Это значит: Тянем ВНИЗ (dy > 0) -> Скролл уменьшается -> Текст едет ВНИЗ (мы смотрим ВВЕРХ).

                    help_scroll_y -= dy
                    help_last_drag_y = vmy

                    # === ГРАНИЦЫ (с запасом 50px снизу) ===
                    lines_count = 0
                    h_keys = ["help_goal", "help_goal_text", "", "help_gameplay", "help_gameplay_text", "",
                              "help_special", "help_special_text", "", "help_entities", "help_entities_text", "",
                              "help_prestige", "help_prestige_text", "", "help_luck"]
                    for key in h_keys:
                        txt = localization.get_text(key)
                        if txt: lines_count += txt.count("\n") + 1

                    total_text_height = lines_count * 25 + 50  # +50 пикселей отступ снизу
                    max_scroll = total_text_height - help_h
                    if max_scroll < 0: max_scroll = 0

                    if help_scroll_y < 0: help_scroll_y = 0
                    if help_scroll_y > max_scroll: help_scroll_y = max_scroll

                # === ИГРОВОЙ UI И ИГРА (НЕ ТРОГАЕМ) ===
                if state == STATE_GAME and not active_dialog:
                    logic_y = VIRTUAL_HEIGHT - vmy

                    if is_dragging_ui:
                        dy = vmy - last_drag_y
                        ui.on_mouse_scroll(vmx, vmy, dy * 0.05)
                        last_drag_y = vmy
                    elif potential_click:
                        distance = math.sqrt(event.rel[0] ** 2 + event.rel[1] ** 2)
                        if distance > 5:
                            potential_click = False
                            is_dragging_ui = True
                            last_drag_y = vmy
                            ui.cancel_press()
                    else:
                        dx = int(event.rel[0] * (VIRTUAL_WIDTH / screen.get_width()))
                        dy = int(-event.rel[1] * (VIRTUAL_HEIGHT / screen.get_height()))
                        game.on_mouse_motion(vmx, logic_y, dx, dy)

            elif event.type == pygame.MOUSEWHEEL:
                if state == STATE_MENU and show_help:
                    # Стандарт: Колесо Вниз -> Скролл Вниз
                    help_scroll_y -= event.y * 30

                    # === ГРАНИЦЫ (с запасом 50px снизу) ===
                    lines_count = 0
                    h_keys = ["help_goal", "help_goal_text", "", "help_gameplay", "help_gameplay_text", "",
                              "help_special", "help_special_text", "", "help_entities", "help_entities_text", "",
                              "help_prestige", "help_prestige_text", "", "help_luck"]
                    for key in h_keys:
                        txt = localization.get_text(key)
                        if txt: lines_count += txt.count("\n") + 1

                    total_text_height = lines_count * 25 + 50  # +50 пикселей отступ снизу
                    max_scroll = total_text_height - help_h
                    if max_scroll < 0: max_scroll = 0

                    if help_scroll_y < 0: help_scroll_y = 0
                    if help_scroll_y > max_scroll: help_scroll_y = max_scroll

                elif state == STATE_GAME and not active_dialog:
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
                    localization.get_text("help_special"), localization.get_text("help_special_text"), "",
                    localization.get_text("help_entities"), localization.get_text("help_entities_text"), "",
                    localization.get_text("help_prestige"), localization.get_text("help_prestige_text"), "",
                    localization.get_text("help_luck")
                ]

                clip_rect = pygame.Rect(help_x, help_y, help_w, help_h)
                canvas.set_clip(clip_rect)

                text_y = help_y + 20 - help_scroll_y
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
            # 1. Рисуем игру
            game.draw(canvas, VIRTUAL_HEIGHT)
            ui.draw(canvas, VIRTUAL_HEIGHT, game.balance.get())

            # 2. Кнопки настроек
            lang_key = "lang_" + localization.current_lang
            lang_text = localization.get_text(lang_key)
            lang_color = (80, 80, 80) if game_lang_rect.collidepoint(vmx, vmy) else (60, 60, 60)
            pygame.draw.rect(canvas, lang_color, game_lang_rect, border_radius=5)
            pygame.draw.rect(canvas, (150, 150, 150), game_lang_rect, 2, border_radius=5)
            lang_surf = main_font.render(lang_text, True, (255, 255, 255))
            canvas.blit(lang_surf, lang_surf.get_rect(center=game_lang_rect.center))

            sound_state_key = "sound_on" if not sound_manager.muted else "sound_off"
            sound_text = localization.get_text(sound_state_key)

            sound_color = (80, 80, 80) if game_mute_rect.collidepoint(vmx, vmy) else (60, 60, 60)
            pygame.draw.rect(canvas, sound_color, game_mute_rect, border_radius=5)
            pygame.draw.rect(canvas, (150, 150, 150), game_mute_rect, 2, border_radius=5)
            sound_surf = main_font.render(sound_text, True, (255, 255, 255))
            canvas.blit(sound_surf, sound_surf.get_rect(center=game_mute_rect.center))

            # 3. Престиж
            pres_template = localization.get_text("prestige_level_text")
            prestige_text = pres_template.format(game.prestige.points, round(game.prestige.multiplier, 1))
            pres_surf = main_font.render(prestige_text, True, (0, 0, 0))
            canvas.blit(pres_surf, (10, 10))

            # === 4. АДМИН-ПАНЕЛЬ (ОТРИСОВКА) ===
            # Рисуется только если DEBUG_MODE == True
            if DEBUG_MODE:
                admin_panel_height = 220
                admin_y_start = VIRTUAL_HEIGHT - 60 - admin_panel_height - 20

                admin_btn_h = 40
                admin_btn_w = 200
                admin_x = 10

                admin_btn_lucky = pygame.Rect(admin_x, admin_y_start + 10, admin_btn_w, admin_btn_h)
                admin_btn_cursed = pygame.Rect(admin_x, admin_y_start + 60, admin_btn_w, admin_btn_h)
                admin_btn_money = pygame.Rect(admin_x, admin_y_start + 110, admin_btn_w, admin_btn_h)
                admin_btn_beetle = pygame.Rect(admin_x, admin_y_start + 160, admin_btn_w, admin_btn_h)

                # Фон панели
                pygame.draw.rect(canvas, (50, 50, 50, 180),
                                 (admin_x - 5, admin_y_start + 5, admin_btn_w + 10, admin_panel_height),
                                 border_radius=5)

                # Кнопка Lucky
                lucky_color = (50, 150, 50) if not admin_btn_lucky.collidepoint(vmx, vmy) else (70, 200, 70)
                pygame.draw.rect(canvas, lucky_color, admin_btn_lucky, border_radius=3)
                lucky_txt = main_font.render("SPAWN LUCKY", True, (255, 255, 255))
                canvas.blit(lucky_txt, (admin_btn_lucky.x + 10, admin_btn_lucky.y + 10))

                # Кнопка Cursed
                cursed_color = (100, 50, 100) if not admin_btn_cursed.collidepoint(vmx, vmy) else (150, 70, 150)
                pygame.draw.rect(canvas, cursed_color, admin_btn_cursed, border_radius=3)
                cursed_txt = main_font.render("SPAWN CURSED", True, (255, 255, 255))
                canvas.blit(cursed_txt, (admin_btn_cursed.x + 10, admin_btn_cursed.y + 10))

                # Кнопка Money
                money_color = (150, 150, 50) if not admin_btn_money.collidepoint(vmx, vmy) else (200, 200, 70)
                pygame.draw.rect(canvas, money_color, admin_btn_money, border_radius=3)
                money_txt = main_font.render("+1 SEPTILLION $", True, (0, 0, 0))
                canvas.blit(money_txt, (admin_btn_money.x + 10, admin_btn_money.y + 10))

                # Кнопка Beetle
                beetle_color = (150, 100, 50) if not admin_btn_beetle.collidepoint(vmx, vmy) else (200, 140, 70)
                pygame.draw.rect(canvas, beetle_color, admin_btn_beetle, border_radius=3)
                beetle_txt = main_font.render("SPAWN BEETLE", True, (255, 255, 255))
                canvas.blit(beetle_txt, (admin_btn_beetle.x + 10, admin_btn_beetle.y + 10))

            # === 5. ОТРИСОВКА ДИАЛОГОВ ===
            if active_dialog:
                overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 38))
                canvas.blit(overlay, (0, 0))

                dialog_w, dialog_h = 500, 250
                dialog_x = (VIRTUAL_WIDTH - dialog_w) // 2
                dialog_y = (VIRTUAL_HEIGHT - dialog_h) // 2

                pygame.draw.rect(canvas, (40, 40, 40), (dialog_x, dialog_y, dialog_w, dialog_h), border_radius=10)
                pygame.draw.rect(canvas, (200, 200, 200), (dialog_x, dialog_y, dialog_w, dialog_h), 2, border_radius=10)

                if active_dialog == 'prestige':
                    title = localization.get_text("dialog_prestige_title")
                    text = localization.get_text("dialog_prestige_text")
                else:
                    title = localization.get_text("dialog_new_game_title")
                    text = localization.get_text("dialog_new_game_text")

                title_surf = main_font.render(title, True, (255, 255, 255))
                title_rect = title_surf.get_rect(center=(dialog_x + dialog_w // 2, dialog_y + 40))
                canvas.blit(title_surf, title_rect)

                text_surf = main_font.render(text, True, (200, 200, 200))
                text_rect = text_surf.get_rect(center=(dialog_x + dialog_w // 2, dialog_y + 100))
                canvas.blit(text_surf, text_rect)

                btn_w_d, btn_h_d = 120, 50
                btn_yes = pygame.Rect(dialog_x + 50, dialog_y + dialog_h - 70, btn_w_d, btn_h_d)
                btn_no = pygame.Rect(dialog_x + dialog_w - 170, dialog_y + dialog_h - 70, btn_w_d, btn_h_d)
                btn_close_d = pygame.Rect(dialog_x + dialog_w - 40, dialog_y + 10, 30, 30)

                yes_color = (50, 150, 50) if not btn_yes.collidepoint(vmx, vmy) else (70, 200, 70)
                pygame.draw.rect(canvas, yes_color, btn_yes, border_radius=5)
                yes_txt = main_font.render(localization.get_text("dialog_yes"), True, (255, 255, 255))
                canvas.blit(yes_txt, yes_txt.get_rect(center=btn_yes.center))

                no_color = (150, 50, 50) if not btn_no.collidepoint(vmx, vmy) else (200, 70, 70)
                pygame.draw.rect(canvas, no_color, btn_no, border_radius=5)
                no_txt = main_font.render(localization.get_text("dialog_no"), True, (255, 255, 255))
                canvas.blit(no_txt, no_txt.get_rect(center=btn_no.center))

                pygame.draw.rect(canvas, (200, 50, 50), btn_close_d, border_radius=5)
                x_surf = main_font.render("X", True, (255, 255, 255))
                canvas.blit(x_surf, x_surf.get_rect(center=btn_close_d.center))

            # === КНОПКА РЕЖИМА ЗАХВАТА (ДЛЯ МОБИЛЬНЫХ) ===
            # Рисуем кнопку ТОЛЬКО если это мобильное устройство
            if game.grab_purchased and game.is_mobile_device:
                grab_btn_rect = pygame.Rect(game_lang_rect.x - 120, game_btn_margin, 100, game_btn_h)
                grab_color = (0, 150, 0) if game.grab_mode_active else (80, 80, 80)
                pygame.draw.rect(canvas, grab_color, grab_btn_rect, border_radius=5)
                txt = "GRAB: ON" if game.grab_mode_active else "GRAB: OFF"
                grab_txt = main_font.render(txt, True, (255, 255, 255))
                canvas.blit(grab_txt, grab_txt.get_rect(center=grab_btn_rect.center))

        pygame.transform.smoothscale(canvas, (screen.get_width(), screen.get_height()), screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()