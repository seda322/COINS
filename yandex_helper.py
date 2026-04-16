# yandex_helper.py
import localization
import sys

# Пытаемся импортировать JS мост
try:
    import js
    import pyodide
    IS_BROWSER = True
except ImportError:
    IS_BROWSER = False

def is_mobile():
    """Возвращает True, если устройство имеет тачскрин."""
    if IS_BROWSER:
        try:
            # Вызываем JS функцию, которую мы добавили в index.html
            has_touch = js.window.hasTouchScreen()
            return bool(has_touch)
        except Exception as e:
            print(f"Touch check error: {e}")
            return True # Если ошибка, лучше показать кнопку (безопаснее для мобилок)
    return False # На ПК возвращаем False

def initialize_environment():
    """Устанавливает язык при запуске."""
    # Язык уже должен быть установлен через index.html скрипт,
    # но на всякий случай дублируем логику тут для ПК версии
    if not IS_BROWSER:
        # На ПК используем язык системы
        import locale
        try:
            lang = locale.getdefaultlocale()[0]
            if lang and lang.startswith('ru'):
                localization.current_lang = 'ru'
            else:
                localization.current_lang = 'en'
        except:
            pass