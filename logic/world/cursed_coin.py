from logic.world.coin import Coin
import random


class CursedCoin(Coin):
    def __init__(
            self,
            x: float,
            y: float,
            sprites: dict,
            value: int = 10,
            scale: float = 1.3,
            scale_factor: float = 1.0
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            sprites=sprites,
            value=value,
            scale=scale,
            scale_factor=scale_factor
        )
        # === МАССА (Тяжелая) ===
        self.mass = 1.5

        self.bankruptcy_triggered = False
        self.sound_played = False
        self.is_used = False

    def land(self) -> None:
        # Сбрасываем флаги
        self.bankruptcy_triggered = False
        self.sound_played = False
        super().land()

        is_heads = random.random() < 0.5

        if is_heads:
            self.last_outcome_value = self.value
            self.sprite.texture = self.sprites["heads"]
        else:
            self.last_outcome_value = 0
            self.bankruptcy_triggered = True
            self.sprite.texture = self.sprites["tails"]

        # Запуск исчезновения
        self.is_used = True
        self.lifetime = 2.5
        self.is_fading = True

    # ЗАЩИТА ОТ ПЕРЕВОРОТА
    def hit(self, dx: int, dy: int) -> None:
        if self.is_used: return
        super().hit(dx, dy)

    def hit_by_coin(self, source_coin, nx, ny) -> None:
        if self.is_used: return
        super().hit_by_coin(source_coin, nx, ny)