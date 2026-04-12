import pygame
import os
import random
import sys


class SoundManager:
    def __init__(self) -> None:
        self.muted = False

        # Списки для рандомных звуков
        self.bronze_toss_sounds = []
        self.bronze_landing_sounds = []
        self.silver_toss_sounds = []
        self.silver_landing_sounds = []
        self.gold_toss_sounds = []
        self.gold_landing_sounds = []

        # История для предотвращения повторов
        self._last_bronze_toss = None
        self._last_bronze_land = None
        self._last_silver_toss = None
        self._last_silver_land = None
        self._last_gold_toss = None
        self._last_gold_land = None

        # Отдельные звуки (ВАЖНО: они должны быть определены здесь, чтобы избежать AttributeError)
        self.beetle_dead_sound = None
        self.boom_sound = None
        self.tornado_sound = None
        self.merge_sound = None
        self.lucky_success = None
        self.lucky_fail = None
        self.cursed_success = None
        self.cursed_fail = None

    def load_all(self) -> None:
        # Определение путей
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            base_dir = project_root

        base_sound_dir = os.path.join(base_dir, "view", "sounds")
        print(f"DEBUG SoundManager: Loading sounds from {base_sound_dir}")

        # Загрузка стандартных звуков монет
        print("--- Loading Bronze Sounds ---")
        bronze_paths = [os.path.join(base_sound_dir, "bronze_sounds", "tossing"),
                        os.path.join(base_sound_dir, "silver_and_bronze_sounds", "tossing")]
        bronze_paths_land = [os.path.join(base_sound_dir, "bronze_sounds", "landing"),
                             os.path.join(base_sound_dir, "silver_and_bronze_sounds", "landing")]
        self._load_sounds_from_dir(bronze_paths, self.bronze_toss_sounds, "Bronze Toss")
        self._load_sounds_from_dir(bronze_paths_land, self.bronze_landing_sounds, "Bronze Land")

        print("--- Loading Silver Sounds ---")
        silver_paths = [os.path.join(base_sound_dir, "silver_sounds", "tossing"),
                        os.path.join(base_sound_dir, "silver_and_bronze_sounds", "tossing")]
        silver_paths_land = [os.path.join(base_sound_dir, "silver_sounds", "landing"),
                             os.path.join(base_sound_dir, "silver_and_bronze_sounds", "landing")]
        self._load_sounds_from_dir(silver_paths, self.silver_toss_sounds, "Silver Toss")
        self._load_sounds_from_dir(silver_paths_land, self.silver_landing_sounds, "Silver Land")

        print("--- Loading Gold Sounds ---")
        self._load_sounds_from_dir([os.path.join(base_sound_dir, "gold_sounds", "tossing")],
                                   self.gold_toss_sounds, "Gold Toss")
        self._load_sounds_from_dir([os.path.join(base_sound_dir, "gold_sounds", "landing")],
                                   self.gold_landing_sounds, "Gold Land")

        print("--- Loading Special Sounds ---")
        # Загрузка одиночных звуков
        self.beetle_dead_sound = self._load_sound_safe(base_sound_dir, "beetle", "beetle_dead")
        self.boom_sound = self._load_sound_safe(base_sound_dir, "boom", "boom")
        self.tornado_sound = self._load_sound_safe(base_sound_dir, "tornado", "tornado")
        self.merge_sound = self._load_sound_safe(base_sound_dir, "merge", "merge")

        # Загрузка Lucky Coin
        self.lucky_success = self._load_sound_safe(base_sound_dir, "lucky_coin", "lucky_coin_win")
        self.lucky_fail = self._load_sound_safe(base_sound_dir, "lucky_coin", "lucky_coin_fail")  # Если есть

        # Загрузка Cursed Coin
        self.cursed_success = self._load_sound_safe(base_sound_dir, "cursed_coin", "cursed_coin_win")
        self.cursed_fail = self._load_sound_safe(base_sound_dir, "cursed_coin", "cursed_coin_fail")

        print("--- Sound Loading Complete ---")

    def _load_sound_safe(self, base_dir: str, folder_name: str, filename: str):
        """
        Ищет звук в папке base_dir/folder_name/filename.
        Проверяет расширения в приоритете: .ogg, .wav, .mp3, .org (на всякий случай)
        """
        dir_path = os.path.join(base_dir, folder_name)
        if not os.path.exists(dir_path):
            # Пробуем искать в корневой папке звуков, если подпапки нет
            dir_path = base_dir
            if not os.path.exists(dir_path): return None

        # Приоритет форматов: OGG -> WAV -> MP3 -> ORG
        extensions = [".ogg", ".wav", ".mp3", ".org"]

        for ext in extensions:
            path = os.path.join(dir_path, f"{filename}{ext}")
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    print(f"  -> Loaded special sound: {filename}{ext}")
                    return snd
                except Exception as e:
                    print(f"  -> WARNING: Failed to load {path}: {e}")
                    continue

        # Если файл не найден, но должен был быть (например cursed_coin_fail.org)
        # Попробуем найти частичное совпадение имени в папке
        try:
            for f in os.listdir(dir_path):
                if f.startswith(filename):
                    try:
                        return pygame.mixer.Sound(os.path.join(dir_path, f))
                    except:
                        pass
        except:
            pass

        return None

    def _load_sounds_from_dir(self, directory_paths: list[str], target_list: list, label: str) -> None:
        """
        Загружает ВСЕ файлы звуковых форматов из указанных папок.
        """
        for directory_path in directory_paths:
            if os.path.exists(directory_path):
                files = sorted(os.listdir(directory_path))
                count = 0
                for f in files:
                    if f.lower().endswith((".ogg", ".wav", ".mp3", ".org")):
                        sound_path = os.path.join(directory_path, f)
                        try:
                            snd = pygame.mixer.Sound(sound_path)
                            snd.set_volume(0.5)
                            target_list.append(snd)
                            count += 1
                        except Exception as e:
                            print(f"  -> WARNING: Could not load sound {f}: {e}")

                if count > 0:
                    print(f"  -> Loaded {count} {label} from {os.path.basename(directory_path)}")
                    return
        print(f"  -> WARNING: No sounds found for {label}!")

    def play_toss(self, coin_type: str) -> None:
        if self.muted: return

        if coin_type == "gold":
            sound = self._pick_sound(self.gold_toss_sounds, self._last_gold_toss)
            self._last_gold_toss = sound
        elif coin_type == "silver":
            sound = self._pick_sound(self.silver_toss_sounds, self._last_silver_toss)
            self._last_silver_toss = sound
        else:  # bronze
            sound = self._pick_sound(self.bronze_toss_sounds, self._last_bronze_toss)
            self._last_bronze_toss = sound

        if sound:
            sound.play()

    def play_land(self, coin_type: str) -> None:
        if self.muted: return

        if coin_type == "gold":
            sound = self._pick_sound(self.gold_landing_sounds, self._last_gold_land)
            self._last_gold_land = sound
        elif coin_type == "silver":
            sound = self._pick_sound(self.silver_landing_sounds, self._last_silver_land)
            self._last_silver_land = sound
        else:  # bronze
            sound = self._pick_sound(self.bronze_landing_sounds, self._last_bronze_land)
            self._last_bronze_land = sound

        if sound:
            sound.play()

    def _pick_sound(self, pool: list, last_sound: any) -> any:
        if not pool:
            return None
        if len(pool) == 1:
            return pool[0]
        candidates = [s for s in pool if s != last_sound]
        if not candidates:
            return random.choice(pool)
        return random.choice(candidates)

    def toggle_mute(self):
        self.muted = not self.muted