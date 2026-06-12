"""farming.py — Crop growth and soil state management for Solstice Farm."""

from __future__ import annotations

from settings import CROPS, SUN_GROWTH_SCHEDULE


# ---------------------------------------------------------------------------
# Sunlight multiplier helper
# ---------------------------------------------------------------------------

def get_sun_multiplier(time_fraction: float) -> float:
    """Return the crop growth speed multiplier for the current time of day."""
    tf = max(0.0, min(1.0, time_fraction))
    schedule = SUN_GROWTH_SCHEDULE

    for i in range(len(schedule) - 1):
        t0, m0 = schedule[i]
        t1, m1 = schedule[i + 1]
        if tf <= t1:
            span = t1 - t0
            lt = (tf - t0) / span if span > 0 else 0.0
            return m0 + (m1 - m0) * lt
    return schedule[-1][1]


# ---------------------------------------------------------------------------
# Crop
# ---------------------------------------------------------------------------

class Crop:
    """A single crop planted in a soil tile."""

    def __init__(self, crop_type: str) -> None:
        self.crop_type = crop_type
        self.data = CROPS[crop_type]
        self.progress: float = 0.0        # 0.0 → 1.0
        self.watered: bool = False
        self.times_watered: int = 0
        self.water_needed: int = self.data["water_needed"]
        self.needs_water: bool = True      # starts needing initial watering
        self.ready: bool = False
        self.is_solstice_only: bool = self.data.get("special") == "solstice_only"
        self.event_boost: float = 1.0      # temporary boost from events

        # Water checkpoints (evenly distributed through growth)
        self._water_points: list[float] = []
        if self.water_needed > 1:
            for i in range(1, self.water_needed):
                self._water_points.append(i / self.water_needed)
        self._next_wp: int = 0

    @property
    def stage(self) -> int:
        """Current visual stage index (0-based)."""
        stages = self.data["stages"]
        if self.ready:
            return stages - 1
        return min(int(self.progress * stages), stages - 2)

    def water_crop(self) -> bool:
        """Water this crop. Returns True if it actually needed water."""
        if self.needs_water and not self.ready:
            self.watered = True
            self.needs_water = False
            self.times_watered += 1
            return True
        return False

    def update(self, dt: float, time_fraction: float) -> None:
        """Advance growth. Pauses if needs_water or already ready."""
        if self.ready or self.needs_water:
            return

        multiplier = get_sun_multiplier(time_fraction)

        # Solstice Bloom: only grows when sun multiplier >= 1.0 (peak hours)
        if self.is_solstice_only and multiplier < 1.0:
            return  # dormant outside peak sun

        # Apply event boost (e.g. Sunburst)
        multiplier *= self.event_boost

        self.progress += (dt / self.data["grow_time"]) * multiplier

        # Check next water checkpoint
        if self._next_wp < len(self._water_points):
            threshold = self._water_points[self._next_wp]
            if self.progress >= threshold:
                self.progress = threshold
                self.needs_water = True
                self.watered = False
                self._next_wp += 1
                return

        # Check completion
        if self.progress >= 1.0:
            self.progress = 1.0
            self.ready = True

    def harvest_value(self) -> int:
        """Return the sell value of this crop."""
        return self.data["sell_price"] if self.ready else 0
