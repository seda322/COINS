from logic.world.coin import Coin
import random

class GoldCoin(Coin):
    def __init__(
            self,
            x: float,
            y: float,
            sprites: dict,
            value: int = 100,
            scale: float = 1.5,
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
        # === МАССА ЗОЛОТА (Тяжелая) ===
        self.mass = 1.5

    def land(self) -> None:
        super().land()