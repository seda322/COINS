# browser_saver.py
import json
import os

# Пытаемся импортировать мост Pygbag (работает только в браузере)
try:
    import js
    import pyodide

    IS_BROWSER = True
except ImportError:
    IS_BROWSER = False


class BrowserStorage:
    def __init__(self, key="game_save_v1"):
        self.key = key
        # Путь для сохранения на ПК
        self.pc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")

    def save(self, data_dict):
        json_str = json.dumps(data_dict, ensure_ascii=True)
        if IS_BROWSER:
            # Сохраняем в память браузера (localStorage)
            js.localStorage.setItem(self.key, json_str)
        else:
            # Сохраняем в файл на компьютере
            try:
                with open(self.pc_path, "w") as f:
                    f.write(json_str)
            except Exception as e:
                print(f"Save error: {e}")

    def load(self):
        json_str = None
        if IS_BROWSER:
            # Читаем из памяти браузера
            js_data = js.localStorage.getItem(self.key)
            if js_data is not None:
                json_str = str(js_data)
        else:
            # Читаем файл на компьютере
            try:
                if os.path.exists(self.pc_path):
                    with open(self.pc_path, "r") as f:
                        json_str = f.read()
            except Exception as e:
                print(f"Load error: {e}")

        if json_str:
            try:
                return json.loads(json_str)
            except:
                return None
        return None

    def delete(self):
        """Полное удаление сохранения (для сброса)"""
        if IS_BROWSER:
            js.localStorage.removeItem(self.key)
        else:
            if os.path.exists(self.pc_path):
                try:
                    os.remove(self.pc_path)
                except:
                    pass