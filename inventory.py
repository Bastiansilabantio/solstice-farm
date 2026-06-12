"""inventory.py — Inventory management for Solstice Farm."""

from __future__ import annotations

from settings import CROPS, CROP_TYPES, STARTING_MONEY


class Inventory:
    """Player inventory: tracks seeds, harvested crops, and money."""

    def __init__(self) -> None:
        self.money: int = STARTING_MONEY

        # Seeds: {crop_type: count}
        self.seeds: dict[str, int] = {
            "lettuce": 5,
            "tomato": 3,
        }

        # Harvested crops: {crop_type: count}
        self.harvested: dict[str, int] = {}

        # Stats tracking
        self.total_planted: int = 0
        self.total_harvested: int = 0
        self.total_earned: int = 0
        self.total_spent: int = 0

    # ------------------------------------------------------------------
    # Seeds
    # ------------------------------------------------------------------

    def has_seeds(self, crop_type: str) -> bool:
        return self.seeds.get(crop_type, 0) > 0

    def use_seed(self, crop_type: str) -> bool:
        if self.has_seeds(crop_type):
            self.seeds[crop_type] -= 1
            if self.seeds[crop_type] <= 0:
                del self.seeds[crop_type]
            self.total_planted += 1
            return True
        return False

    def add_seeds(self, crop_type: str, count: int) -> None:
        self.seeds[crop_type] = self.seeds.get(crop_type, 0) + count

    # ------------------------------------------------------------------
    # Harvested crops
    # ------------------------------------------------------------------

    def add_harvest(self, crop_type: str, count: int = 1) -> None:
        self.harvested[crop_type] = self.harvested.get(crop_type, 0) + count
        self.total_harvested += count

    def get_harvest_count(self, crop_type: str) -> int:
        return self.harvested.get(crop_type, 0)

    # ------------------------------------------------------------------
    # Economy
    # ------------------------------------------------------------------

    def can_afford(self, cost: int) -> bool:
        return self.money >= cost

    def buy_seeds(self, crop_type: str, count: int = 1) -> bool:
        """Buy seeds. Returns True on success."""
        cost = CROPS[crop_type]["seed_cost"] * count
        if self.can_afford(cost):
            self.money -= cost
            self.add_seeds(crop_type, count)
            self.total_spent += cost
            return True
        return False

    def sell_crop(self, crop_type: str, count: int = 1,
                  sell_multiplier: float = 1.0) -> bool:
        """Sell harvested crops. Returns True on success."""
        available = self.harvested.get(crop_type, 0)
        sell_count = min(count, available)
        if sell_count <= 0:
            return False
        value = int(CROPS[crop_type]["sell_price"] * sell_count * sell_multiplier)
        self.harvested[crop_type] -= sell_count
        if self.harvested[crop_type] <= 0:
            del self.harvested[crop_type]
        self.money += value
        self.total_earned += value
        return True

    def sell_all(self) -> int:
        """Sell all harvested crops. Returns total gold earned."""
        total = 0
        for crop_type in list(self.harvested.keys()):
            count = self.harvested[crop_type]
            value = CROPS[crop_type]["sell_price"] * count
            total += value
            self.total_earned += value
        self.harvested.clear()
        self.money += total
        return total
