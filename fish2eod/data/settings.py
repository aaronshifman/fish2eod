from dataclasses import dataclass


@dataclass
class FishSettings:
    name: str
    normal_length: float
    head_distance: float
    tail_distance: float
    head_conductance: float
    tail_conductance: float
    organ_start: float
    organ_length: float
    organ_width: float

    def middle_conductance(self, head_fraction: float, tail_fraction: float, x: float) -> float:
        """Compute the middle_cond which is a linear slope between head and tail."""
        middle_range = self.tail_conductance - self.head_conductance
        middle_slope = middle_range / (tail_fraction - head_fraction)
        return self.head_conductance + middle_slope * (x - head_fraction)


APTERONOTUS = FishSettings(
    name="apteronotus",
    normal_length=21.0,
    head_distance=12.73,
    tail_distance=19.09,
    head_conductance=0.00025 / 100,
    tail_conductance=0.0025 / 100,
    organ_start=2.38,
    organ_length=17.95,
    organ_width=1.25e-4 * 100,
)

EIGENMANNIA = FishSettings(
    name="eigenmannia",
    normal_length=26.0,
    head_distance=15.6,
    tail_distance=23.4,
    head_conductance=0.00025 / 100,
    tail_conductance=0.0025 / 100,
    organ_start=3,
    organ_length=22,
    organ_width=0.005,
)
