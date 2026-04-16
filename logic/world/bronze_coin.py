from logic.world.coin import Coin

class BronzeCoin(Coin):
    def __init__(
        self,
        x: float,
        y: float,
        sprites: dict,
        value: int = 1,
        scale: float = 0.8,
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
        # === МАССА БРОНЗЫ ===
        self.mass = 0.8