import pygame
import os
import time  # Импортируем time
from dataclasses import dataclass
from typing import Optional, List, Dict
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from localization import get_text


# --- Вспомогательные классы ---
@dataclass
class _TabStub:
    tab_id: int
    title: str


@dataclass
class _UiButtonStub:
    upgrade_id: str
    title: str
    base_name: str
    base_cost: int
    is_one_time: bool = True
    is_purchased: bool = False
    purchased_text: str = "уже куплен"
    level: int = 0
    max_level: int = -1


@dataclass
class _UiGroupStub:
    title: str
    buttons: List[_UiButtonStub]


class UIController:
    def __init__(self, panel_x: int, panel_width: int, panel_height: int, ui_assets: dict,
                 scale_factor: float = 1.0) -> None:
        self.panel_x = panel_x
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.ui_assets = ui_assets
        self.scale_factor = scale_factor
        self._has_tornado = False
        self._combo_unlocked = False

        # --- ШРИФТЫ ---
        raw_font_path = self.ui_assets.get("font_name", "Arial")
        try:
            if raw_font_path != "Arial" and os.path.exists(raw_font_path):
                self.game_font_path = raw_font_path
            else:
                self.game_font_path = None
        except:
            self.game_font_path = None

        if self.game_font_path:
            try:
                self.base_font = pygame.font.Font(self.game_font_path, 20)
            except:
                self.base_font = pygame.font.SysFont("Arial", 20)
        else:
            self.base_font = pygame.font.SysFont("Arial", 20)

        # --- НАСТРОЙКИ ЛАЙАУТА ---
        self.header_height = int(80 * self.scale_factor)
        self.tab_bar_height = int(50 * self.scale_factor)
        self.padding = int(20 * self.scale_factor)
        self.btn_height = int(80 * self.scale_factor)
        self.group_header_height = int(40 * self.scale_factor)
        self.btn_gap = int(10 * self.scale_factor)

        self.tabs = [
            _TabStub(0, get_text("tab_coins")),
            _TabStub(1, get_text("tab_map")),
            _TabStub(2, get_text("tab_general")),
        ]
        self.active_tab_index = 0
        self.tab_content: Dict[int, List[_UiGroupStub]] = {}

        # === ВКЛАДКА 0 ===
        self.tab_content[0] = [
            _UiGroupStub(get_text("grp_bronze"), [
                _UiButtonStub("buy_bronze_coin", "", "btn_buy_bronze", 10, is_one_time=False, level=1, max_level=-1),
                _UiButtonStub("bronze_value_upgrade", "", "btn_bronze_val", 50, is_one_time=False, level=0,
                              max_level=50),
            ]),
            _UiGroupStub(get_text("grp_silver"), [
                _UiButtonStub("silver_crit_chance_upgrade", "", "btn_silver_crit", 500, is_one_time=False, level=1,
                              max_level=50),
                _UiButtonStub("silver_crit_upgrade", "", "btn_silver_crit_size", 2000, is_one_time=False, level=1,
                              max_level=20),
                _UiButtonStub("silver_value_upgrade", "", "btn_silver_val", 1000, is_one_time=False, level=0,
                              max_level=50),
            ]),
            _UiGroupStub(get_text("grp_gold"), [
                _UiButtonStub("gold_explosion_upgrade", "", "btn_gold_explode", 15000, is_one_time=True),
                _UiButtonStub("grab_upgrade", "", "btn_grab", 25000, is_one_time=True),
                _UiButtonStub("gold_value_upgrade", "", "btn_gold_val", 5000, is_one_time=False, level=0, max_level=50),
            ]),
            _UiGroupStub(get_text("grp_combo"), [
                _UiButtonStub("unlock_combo", "", "btn_unlock_combo", 50000000, is_one_time=True),
                _UiButtonStub("upgrade_combo_limit", "", "btn_combo_limit", 100000000, is_one_time=False, level=1,
                              max_level=10),
            ]),
            _UiGroupStub(get_text("grp_common"), [
                _UiButtonStub("auto_flip_upgrade", "", "btn_autoflip", 1000, is_one_time=False, level=0, max_level=10),
                _UiButtonStub("fuse_to_silver", "", "btn_fuse_silver", 0, is_one_time=False, max_level=-1),
                _UiButtonStub("fuse_to_gold", "", "btn_fuse_gold", 0, is_one_time=False, max_level=-1),
            ])
        ]
        # === ВКЛАДКА 1 ===
        self.tab_content[1] = [
            _UiGroupStub(get_text("grp_wisp"), [
                _UiButtonStub("wisp_spawn", "", "btn_wisp", 50000, is_one_time=True),
                _UiButtonStub("wisp_speed", "", "btn_wisp_speed", 10000, is_one_time=False, level=0, max_level=30),
                _UiButtonStub("wisp_size", "", "btn_wisp_size", 10000, is_one_time=False, level=0, max_level=30),
            ]),
            _UiGroupStub(get_text("grp_zone2"), [
                _UiButtonStub("spawn_zone_2", "", "btn_spawn_zone2", 80000, is_one_time=True),
                _UiButtonStub("upgrade_zone_2_size", "", "btn_zone2_size", 20000, is_one_time=False, level=0,
                              max_level=20),
                _UiButtonStub("upgrade_zone_2_mult", "", "btn_zone2_mult", 40000, is_one_time=False, level=0,
                              max_level=10),
            ]),
            _UiGroupStub(get_text("grp_zone5"), [
                _UiButtonStub("spawn_zone_5", "", "btn_spawn_zone5", 500000, is_one_time=True),
                _UiButtonStub("upgrade_zone_5_size", "", "btn_zone5_size", 100000, is_one_time=False, level=0,
                              max_level=20),
                _UiButtonStub("upgrade_zone_5_mult", "", "btn_zone5_mult", 200000, is_one_time=False, level=0,
                              max_level=10),
            ]),
            _UiGroupStub(get_text("grp_tornado"), [
                _UiButtonStub("spawn_tornado", "", "btn_spawn_tornado", 2000000, is_one_time=True),
                _UiButtonStub("tornado_cooldown_upgrade", "", "btn_tornado_cd", 500000, is_one_time=False, level=0,
                              max_level=10),
            ]),
            _UiGroupStub(get_text("grp_meteor"), [
                _UiButtonStub("spawn_meteor", "", "btn_spawn_meteor", 10000000, is_one_time=True),
                _UiButtonStub("meteor_cooldown_upgrade", "", "btn_meteor_cd", 2000000, is_one_time=False, level=0,
                              max_level=10),
            ]),
        ]
        # === ВКЛАДКА 2 (Настройки) ===
        self.tab_content[2] = [
            _UiGroupStub(get_text("grp_settings"), [
                _UiButtonStub("watch_ad", "", "btn_free_gold", 0, is_one_time=False),
                _UiButtonStub("new_game", "", "btn_new_game", 0, is_one_time=True),
                _UiButtonStub("exit_to_menu", "", "btn_exit_menu", 0, is_one_time=True),
                _UiButtonStub("prestige", "", "btn_prestige", 0, is_one_time=False, max_level=-1),
                _UiButtonStub("buy_victory", "", "btn_victory", 10_000_000_000_000_000_000_000_000, is_one_time=True),
            ]),
        ]

        self._enabled = {b.upgrade_id: True
                         for tab_groups in self.tab_content.values()
                         for grp in tab_groups
                         for b in grp.buttons}

        self._pressed_id: Optional[str] = None
        self._pressed_down_id: Optional[str] = None

        self._has_gold = False
        self._grab_purchased = False
        self._explosion_purchased = False
        self._has_wisp = False
        self._has_zone_2 = False
        self._has_zone_5 = False
        self._meteor_unlocked = False

        self.scroll_y = 0

        # === РАЗМЕРЫ ШРИФТОВ ===
        self.font_size_header = int(38 * self.scale_factor)
        self.font_size_balance = int(36 * self.scale_factor)
        self.font_size_button = int(24 * self.scale_factor)
        self.font_size_tab = int(22 * self.scale_factor)
        self.font_size_group = int(28 * self.scale_factor)

        # === ТАЙМЕР РЕКЛАМЫ ===
        self._last_ad_time = 0  # Время последнего просмотра
        self._ad_cooldown = 60.0  # 2 минуты

        self.reload_texts()

    def mark_ad_watched(self):
        """Вызывается из main, когда награда за рекламу получена."""
        self._last_ad_time = time.time()

    def _format_number(self, num: int) -> str:
        if num == 0: return "0"
        suffixes = ['', 'K', 'M', 'B', 'T', 'Qa', 'Qi', 'Sx', 'Sp', 'Oc', 'No', 'Dc']
        magnitude = 0
        temp_num = abs(float(num))
        while temp_num >= 1000 and magnitude < len(suffixes) - 1:
            magnitude += 1
            temp_num /= 1000.0
        formatted_val = f"{temp_num:.1f}{suffixes[magnitude]}"
        return formatted_val

    def update_button(self, upgrade_id: str, cost: int, level: int = 0, name: str = None) -> None:
        if upgrade_id == "prestige": return
        for tab_groups in self.tab_content.values():
            for grp in tab_groups:
                for b in grp.buttons:
                    if b.upgrade_id == upgrade_id:
                        b.base_cost = cost
                        b.level = level
                        if name is not None: b.base_name = name
                        display_name = get_text(b.base_name)
                        price_str = self._format_number(cost)
                        if b.upgrade_id in ["new_game", "finish_game"]:
                            b.title = display_name
                            return
                        if b.is_one_time:
                            if not b.is_purchased: b.title = f"{display_name} ({price_str})"
                        else:
                            if level > 0:
                                b.title = f"{display_name} ({level}) ({price_str})"
                            else:
                                b.title = f"{display_name} ({price_str})"
                        return

    def update_grab_state(self, has_gold: bool, purchased: bool) -> None:
        self._has_gold = has_gold
        self._grab_purchased = purchased

    def update_explosion_state(self, purchased: bool) -> None:
        self._explosion_purchased = purchased

    def update_wisp_state(self, has_wisp: bool) -> None:
        self._has_wisp = has_wisp

    def update_meteor_state(self, unlocked: bool) -> None:
        self._meteor_unlocked = unlocked

    def update_zone_state(self, has_zone_2=None, has_zone_5=None) -> None:
        if has_zone_2 is not None: self._has_zone_2 = has_zone_2
        if has_zone_5 is not None: self._has_zone_5 = has_zone_5

    def update_tornado_state(self, unlocked: bool):
        self._has_tornado = unlocked

    def set_button_disabled(self, upgrade_id: str, title: str) -> None:
        for tab_groups in self.tab_content.values():
            for grp in tab_groups:
                for b in grp.buttons:
                    if b.upgrade_id == upgrade_id:
                        b.title = title
                        self._enabled[upgrade_id] = False
                        return

    def update(self, balance_value: int, coin_counts=None) -> None:
        current_time = time.time()

        for tab_groups in self.tab_content.values():
            for grp in tab_groups:
                for b in grp.buttons:
                    btn_name = get_text(b.base_name)
                    price_str = self._format_number(b.base_cost)

                    if b.upgrade_id == "new_game":
                        self._enabled[b.upgrade_id] = True
                        b.title = btn_name
                        continue

                    if b.upgrade_id == "prestige": continue

                    if b.upgrade_id == "exit_to_menu":
                        self._enabled[b.upgrade_id] = True
                        b.title = btn_name
                        continue

                    if b.max_level > 0 and b.level >= b.max_level:
                        b.title = f"{btn_name} ({get_text('status_max')})"
                        self._enabled[b.upgrade_id] = False
                        continue

                    if b.is_purchased:
                        b.title = f"{btn_name} ({get_text('status_purchased')})"
                        self._enabled[b.upgrade_id] = False
                        continue

                    enabled = False

                    if b.upgrade_id == "buy_victory":
                        enabled = balance_value >= b.base_cost
                        b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "upgrade_combo_limit":
                        enabled = self._combo_unlocked and (balance_value >= b.base_cost)
                        if b.level > 0:
                            b.title = f"{btn_name} ({b.level}) ({price_str})"
                        else:
                            b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "tornado_cooldown_upgrade":
                        if not self._has_tornado:
                            enabled = False
                            b.title = f"{btn_name} ({price_str})"
                        else:
                            enabled = b.level < b.max_level and balance_value >= b.base_cost
                            if b.level > 0:
                                b.title = f"{btn_name} ({b.level}) ({price_str})"
                            else:
                                b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "watch_ad":
                        # === ЛОГИКА ТАЙМЕРА РЕКЛАМЫ ===
                        elapsed = current_time - self._last_ad_time
                        if elapsed < self._ad_cooldown:
                            remaining = int(self._ad_cooldown - elapsed)
                            mins = remaining // 60
                            secs = remaining % 60
                            b.title = f"{btn_name} ({mins:02d}:{secs:02d})"
                            enabled = False
                        else:
                            b.title = f"{btn_name} (+10%)"
                            enabled = True

                    elif b.upgrade_id == "meteor_cooldown_upgrade":
                        if not self._meteor_unlocked:
                            enabled = False
                            b.title = f"{btn_name} ({price_str})"
                        else:
                            enabled = b.level < b.max_level and balance_value >= b.base_cost
                            if b.level > 0:
                                b.title = f"{btn_name} ({b.level}) ({price_str})"
                            else:
                                b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "spawn_tornado":
                        if self._has_tornado:
                            b.title = f"{btn_name} ({get_text('status_purchased')})"
                            enabled = False
                        else:
                            enabled = balance_value >= b.base_cost
                            b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "spawn_meteor":
                        if self._meteor_unlocked:
                            b.title = f"{btn_name} ({get_text('status_purchased')})"
                            enabled = False
                        else:
                            enabled = balance_value >= b.base_cost
                            b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "grab_upgrade":
                        if self._has_gold and not b.is_purchased: enabled = balance_value >= b.base_cost
                        b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "gold_explosion_upgrade":
                        enabled = (not self._explosion_purchased) and (balance_value >= b.base_cost)
                        b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "wisp_spawn":
                        if self._has_wisp:
                            b.title = f"{btn_name} ({get_text('status_purchased')})"
                            enabled = False
                        else:
                            enabled = balance_value >= b.base_cost
                            b.title = f"{btn_name} ({price_str})"
                    elif "wisp" in b.upgrade_id and b.upgrade_id != "wisp_spawn":
                        enabled = self._has_wisp and (balance_value >= b.base_cost)
                        if b.level > 0:
                            b.title = f"{btn_name} ({b.level}) ({price_str})"
                        else:
                            b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "spawn_zone_2":
                        if self._has_zone_2:
                            b.title = f"{btn_name} ({get_text('status_purchased')})"
                            enabled = False
                        else:
                            enabled = balance_value >= b.base_cost
                            b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "spawn_zone_5":
                        if self._has_zone_5:
                            b.title = f"{btn_name} ({get_text('status_purchased')})"
                            enabled = False
                        else:
                            enabled = balance_value >= b.base_cost
                            b.title = f"{btn_name} ({price_str})"
                    elif "upgrade_zone_2" in b.upgrade_id:
                        enabled = self._has_zone_2 and (balance_value >= b.base_cost)
                        if b.level > 0:
                            b.title = f"{btn_name} ({b.level}) ({price_str})"
                        else:
                            b.title = f"{btn_name} ({price_str})"
                    elif "upgrade_zone_5" in b.upgrade_id:
                        enabled = self._has_zone_5 and (balance_value >= b.base_cost)
                        if b.level > 0:
                            b.title = f"{btn_name} ({b.level}) ({price_str})"
                        else:
                            b.title = f"{btn_name} ({price_str})"
                    elif b.upgrade_id == "fuse_to_silver":
                        if coin_counts and coin_counts.get('bronze', 0) >= 5:
                            enabled = True
                            b.title = f"{btn_name} (5->1)"
                        else:
                            enabled = False
                            needed = 5 - coin_counts.get('bronze', 0) if coin_counts else 5
                            b.title = f"{btn_name} ({get_text('status_fuse_need')} {needed})"
                    elif b.upgrade_id == "fuse_to_gold":
                        if coin_counts and coin_counts.get('silver', 0) >= 3:
                            enabled = True
                            b.title = f"{btn_name} (3->1)"
                        else:
                            enabled = False
                            needed = 3 - coin_counts.get('silver', 0) if coin_counts else 3
                            b.title = f"{btn_name} ({get_text('status_fuse_need')} {needed})"
                    else:
                        enabled = balance_value >= b.base_cost
                        if not b.is_one_time and b.level > 0:
                            b.title = f"{btn_name} ({b.level}) ({price_str})"
                        else:
                            b.title = f"{btn_name} ({price_str})"

                    self._enabled[b.upgrade_id] = enabled

    def draw(self, surface, screen_height, balance_value: int) -> None:
        pygame.draw.rect(surface, (200, 200, 200), (self.panel_x, 0, self.panel_width, self.panel_height))
        header_rect = pygame.Rect(self.panel_x, 0, self.panel_width, self.header_height)
        tabs_rect = pygame.Rect(self.panel_x, self.header_height, self.panel_width, self.tab_bar_height)

        pygame.draw.rect(surface, (50, 50, 50), header_rect)

        head_font = pygame.font.Font(self.game_font_path,
                                     self.font_size_header) if self.game_font_path else pygame.font.SysFont("Arial",
                                                                                                            self.font_size_header)
        title_surf = head_font.render(get_text("ui_upgrades"), True, (200, 200, 200))
        surface.blit(title_surf, (self.panel_x + self.padding, 2))

        formatted_balance = self._format_number(balance_value)
        bal_font = pygame.font.Font(self.game_font_path,
                                    self.font_size_balance) if self.game_font_path else pygame.font.SysFont("Arial",
                                                                                                            self.font_size_balance)
        bal_surf = bal_font.render(f"{get_text('ui_balance')}: {formatted_balance}", True, (255, 255, 255))
        bal_rect = bal_surf.get_rect(midleft=(self.panel_x + 20, self.header_height - 20))
        surface.blit(bal_surf, bal_rect)

        self._draw_tab_bar(surface, tabs_rect)

        content_start_y = self.header_height + self.tab_bar_height
        content_height = self.panel_height - content_start_y
        clip_rect = pygame.Rect(self.panel_x, content_start_y, self.panel_width, content_height)
        surface.set_clip(clip_rect)

        current_draw_y = content_start_y - self.scroll_y

        group_font = pygame.font.Font(self.game_font_path,
                                      self.font_size_group) if self.game_font_path else pygame.font.SysFont("Arial",
                                                                                                            self.font_size_group)
        btn_font = pygame.font.Font(self.game_font_path,
                                    self.font_size_button) if self.game_font_path else pygame.font.SysFont("Arial",
                                                                                                           self.font_size_button)

        groups = self.tab_content.get(self.active_tab_index, [])

        for grp in groups:
            # === ЦЕНТРИРОВАНИЕ ЗАГОЛОВКА ГРУППЫ ===
            grp_surf = group_font.render(grp.title, True, (30, 30, 30))
            grp_rect = grp_surf.get_rect(centerx=self.panel_x + self.panel_width // 2, y=current_draw_y + 10)
            surface.blit(grp_surf, grp_rect)

            pygame.draw.line(surface, (100, 100, 100), (self.panel_x + self.padding, current_draw_y + 35),
                             (self.panel_x + self.panel_width - self.padding, current_draw_y + 35), 1)

            current_draw_y += self.group_header_height

            for b in grp.buttons:
                if current_draw_y > content_start_y + content_height: break

                enabled = self._enabled.get(b.upgrade_id, True)
                is_pressed = (self._pressed_id == b.upgrade_id)
                y_draw = current_draw_y + (6 if is_pressed else 0)

                texture_to_draw = None
                if self.ui_assets["btn_normal"]:
                    if not enabled:
                        texture_to_draw = self.ui_assets["btn_disabled"]
                    elif is_pressed:
                        texture_to_draw = self.ui_assets["btn_pressed"]
                    else:
                        texture_to_draw = self.ui_assets["btn_normal"]

                btn_w = self.panel_width - (self.padding * 2)

                if texture_to_draw:
                    scaled_tex = pygame.transform.scale(texture_to_draw, (btn_w, self.btn_height))
                    surface.blit(scaled_tex, (self.panel_x + self.padding, y_draw))
                else:
                    fill = (255, 255, 255) if enabled else (150, 150, 150)
                    pygame.draw.rect(surface, fill, (self.panel_x + self.padding, y_draw, btn_w, self.btn_height))
                    pygame.draw.rect(surface, (50, 50, 50),
                                     (self.panel_x + self.padding, y_draw, btn_w, self.btn_height), 1)

                color = (50, 50, 50) if enabled else (100, 100, 100)
                text_surf = btn_font.render(b.title, True, color)

                # === ЦЕНТРИРОВАНИЕ ТЕКСТА КНОПКИ ===
                text_rect = text_surf.get_rect()
                btn_center_x = (self.panel_x + self.padding) + (btn_w // 2)
                btn_center_y = y_draw + (self.btn_height // 2)
                text_rect.center = (btn_center_x, btn_center_y)
                surface.blit(text_surf, text_rect)

                current_draw_y += self.btn_height + self.btn_gap

            current_draw_y += 20
        surface.set_clip(None)

    # Остальные методы без изменений (_draw_tab_bar, hit_test, etc...)
    def _draw_tab_bar(self, surface, rect):
        tab_w = self.panel_width / len(self.tabs)
        tab_font = pygame.font.Font(self.game_font_path,
                                    self.font_size_tab) if self.game_font_path else pygame.font.SysFont("Arial",
                                                                                                        self.font_size_tab)

        for i, tab in enumerate(self.tabs):
            x = rect.x + i * tab_w
            if i == self.active_tab_index:
                bg_color = (255, 255, 255)
                text_color = (0, 0, 0)
            else:
                bg_color = (180, 180, 180)
                text_color = (50, 50, 50)

            pygame.draw.rect(surface, bg_color, (x, rect.y, tab_w, rect.height))
            pygame.draw.rect(surface, (100, 100, 100), (x, rect.y, tab_w, rect.height), 1)

            text_surf = tab_font.render(tab.title, True, text_color)
            text_rect = text_surf.get_rect(center=(x + tab_w / 2, rect.y + rect.height / 2))
            surface.blit(text_surf, text_rect)

    def _hit_test_tabs(self, x: int, y: int) -> Optional[int]:
        if self.header_height < y < self.header_height + self.tab_bar_height:
            if self.panel_x < x < self.panel_x + self.panel_width:
                tab_w = self.panel_width / len(self.tabs)
                col = int((x - self.panel_x) / tab_w)
                if 0 <= col < len(self.tabs): return col
        return None

    def _hit_test_buttons(self, x: int, y: int) -> Optional[str]:
        content_start_y = self.header_height + self.tab_bar_height
        current_y = content_start_y - self.scroll_y

        groups = self.tab_content.get(self.active_tab_index, [])
        for grp in groups:
            current_y += self.group_header_height
            for b in grp.buttons:
                bx = self.panel_x + self.padding
                by = current_y
                bw = self.panel_width - (self.padding * 2)
                bh = self.btn_height
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    return b.upgrade_id
                current_y += self.btn_height + self.btn_gap
            current_y += 20
        return None

    def on_mouse_press(self, x: int, y: int) -> None:
        clicked_tab_index = self._hit_test_tabs(x, y)
        if clicked_tab_index is not None:
            self.active_tab_index = clicked_tab_index
            self.scroll_y = 0
            self._pressed_id = None
            self._pressed_down_id = None
            return

        upgrade_id = self._hit_test_buttons(x, y)
        if upgrade_id is None:
            self._pressed_id = None
            self._pressed_down_id = None
            return

        if not self._enabled.get(upgrade_id, True):
            self._pressed_id = None
            self._pressed_down_id = None
            return

        self._pressed_id = upgrade_id
        self._pressed_down_id = upgrade_id

    def on_mouse_release(self, x: int, y: int) -> Optional[str]:
        released_over_id = self._hit_test_buttons(x, y)
        clicked_id: Optional[str] = None
        if self._pressed_down_id is not None and released_over_id == self._pressed_down_id:
            if self._enabled.get(self._pressed_down_id, True):
                clicked_id = self._pressed_down_id
        self._pressed_id = None
        self._pressed_down_id = None
        return clicked_id

    def on_mouse_scroll(self, x: int, y: int, scroll_y: int) -> None:
        self.scroll_y -= scroll_y * 20
        content_h = 0
        for grp in self.tab_content.get(self.active_tab_index, []):
            h = self.group_header_height
            h += len(grp.buttons) * (self.btn_height + self.btn_gap)
            h += 20
            content_h += h

        visible_h = self.panel_height - self.header_height - self.tab_bar_height
        max_scroll = max(0, content_h - visible_h)

        if self.scroll_y < 0: self.scroll_y = 0
        if self.scroll_y > max_scroll: self.scroll_y = max_scroll

    def mark_purchased(self, upgrade_id: str) -> None:
        for tab_groups in self.tab_content.values():
            for grp in tab_groups:
                for b in grp.buttons:
                    if b.upgrade_id == upgrade_id:
                        b.is_purchased = True
                        b.title = f"{get_text(b.base_name)} ({b.purchased_text})"
                        self._enabled[upgrade_id] = False
                        return

    def reload_texts(self):
        self.tabs[0].title = get_text("tab_coins")
        self.tabs[1].title = get_text("tab_map")
        self.tabs[2].title = get_text("tab_general")

        group_keys = {
            0: ["grp_bronze", "grp_silver", "grp_gold", "grp_combo", "grp_common"],
            1: ["grp_wisp", "grp_zone2", "grp_zone5", "grp_tornado", "grp_meteor"],
            2: ["grp_settings"]
        }

        for tab_idx, groups in self.tab_content.items():
            grp_keys_list = group_keys.get(tab_idx, [])
            for i, grp in enumerate(groups):
                if i < len(grp_keys_list): grp.title = get_text(grp_keys_list[i])

    def update_prestige_button(self, gain: int, total_points: int, multiplier: float):
        btn = None
        for groups in self.tab_content.values():
            for grp in groups:
                for b in grp.buttons:
                    if b.upgrade_id == "prestige":
                        btn = b
                        break

        if btn:
            if gain > 0:
                gain_str = self._format_number(gain)
                btn.title = f"{get_text('btn_prestige')} (+{gain_str})"
                self._enabled["prestige"] = True
            else:
                btn.title = get_text("prestige_need")
                self._enabled["prestige"] = False

    def update_combo_unlocked_state(self, unlocked: bool):
        self._combo_unlocked = unlocked

    def reset_all_buttons(self):
        for tab_groups in self.tab_content.values():
            for grp in tab_groups:
                for b in grp.buttons:
                    b.is_purchased = False
                    b.level = 0
                    b.title = get_text(b.base_name)

        self._has_gold = False
        self._grab_purchased = False
        self._explosion_purchased = False
        self._has_wisp = False
        self._has_zone_2 = False
        self._has_zone_5 = False
        self._meteor_unlocked = False
        self._has_tornado = False
        self._combo_unlocked = False

        for key in self._enabled: self._enabled[key] = True

    def cancel_press(self):
        self._pressed_id = None
        self._pressed_down_id = None

    def get_pressed_button_id(self) -> str:
        return self._pressed_down_id

    def is_button_enabled(self, upgrade_id: str) -> bool:
        return self._enabled.get(upgrade_id, False)