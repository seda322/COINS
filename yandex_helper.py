# yandex_helper.py
import localization
import sys
import time

# Пытаемся импортировать JS мост
try:
    import js
    import pyodide

    IS_BROWSER = True
except ImportError:
    IS_BROWSER = False

# === ГЛОБАЛЬНЫЕ ФЛАГИ ===
ad_is_pausing_game = False
reward_ready = False
last_ad_time = 0.0
INTERSTITIAL_INTERVAL = 120.0


def is_mobile():
    if IS_BROWSER:
        try:
            has_touch = js.window.hasTouchScreen()
            return bool(has_touch)
        except Exception as e:
            print(f"Touch check error: {e}")
            return True
    return False


def initialize_environment():
    if not IS_BROWSER:
        import locale
        try:
            lang = locale.getdefaultlocale()[0]
            if lang and lang.startswith('ru'):
                localization.current_lang = 'ru'
            else:
                localization.current_lang = 'en'
        except:
            pass


# === ФУНКЦИИ РЕКЛАМЫ ===

def show_interstitial_ad():
    global last_ad_time
    current_time = time.time()

    if current_time - last_ad_time < INTERSTITIAL_INTERVAL:
        return
    if ad_is_pausing_game:
        return

    if IS_BROWSER:
        try:
            print("Calling JS showInterstitial")
            js.window.showInterstitial()
            last_ad_time = current_time
        except Exception as e:
            print(f"Interstitial call error: {e}")


def show_rewarded_ad():
    if IS_BROWSER:
        try:
            print("Calling JS showRewardedVideo")
            js.window.showRewardedVideo()
        except Exception as e:
            print(f"Rewarded call error: {e}")
    else:
        # === СИМУЛЯЦИЯ ДЛЯ ТЕСТОВ НА ПК ===
        # Если мы не в браузере, просто ждем 1 секунду и даем награду
        print("LOCAL TEST: Simulating ad reward in 1 sec...")
        import threading
        def mock_reward():
            time.sleep(1)
            on_ad_opened()
            time.sleep(0.5)
            on_ad_closed()
            # Принудительно ставим флаг награды
            global reward_ready
            reward_ready = True

        t = threading.Thread(target=mock_reward)
        t.start()


def check_ad_pause():
    return ad_is_pausing_game


def check_and_reset_reward():
    global reward_ready
    if reward_ready:
        reward_ready = False
        return True
    return False


# === ФУНКЦИИ ДЛЯ JS ===

def on_ad_opened():
    global ad_is_pausing_game
    ad_is_pausing_game = True
    print("Game PAUSED by Ad")


def on_ad_closed():
    global ad_is_pausing_game
    global last_ad_time
    import time

    ad_is_pausing_game = False
    print("Game RESUMED after Ad")
    last_ad_time = time.time()