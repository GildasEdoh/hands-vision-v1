from dataclasses import dataclass

@dataclass
class Landmark:
    x_: float
    y_: float
    z_: float
    visibility: any
    presence: str | None
    name: str | None