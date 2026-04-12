class PrestigeManager:
    def __init__(self):
        self.points = 0
        self.multiplier = 1.0
        self.total_earned = 0  # Сколько всего заработано денег за текущую игру

    def get_data(self):
        return {
            "points": self.points,
            "multiplier": self.multiplier,
            "total_earned": self.total_earned
        }

    def load_data(self, data):
        self.points = data.get("points", 0)
        self.multiplier = data.get("multiplier", 1.0)
        # При загрузке total_earned сбрасываем в 0, так как это новая игровая сессия
        self.total_earned = 0

    def can_prestige(self):
        # Условие: заработать хотя бы 1 миллиард (1,000,000,000) за игру
        return self.total_earned >= 1_000_000_000

    def calculate_gain(self):
        # Формула: +1 очко за каждый миллиард
        return int(self.total_earned / 1_000_000_000)

    def add_income(self, amount: int):
        self.total_earned += amount

    def reset_run_stats(self):
        self.total_earned = 0

    def add_point(self):
        self.points += 1
        self.multiplier = 1.0 + (self.points * 0.1)