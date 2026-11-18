from dataclasses import dataclass, field
import math
import random
from typing import Tuple


BALLOON_COLORS = [
    (50, 60, 240),    # Rouge rubis
    (230, 150, 30),   # Bleu cyan
    (60, 210, 80),    # Vert émeraude
    (30, 210, 255),   # Jaune éclatant
    (200, 60, 210),   # Magenta / Violet
    (30, 140, 255),   # Orange vif
]
GOLDEN_COLOR = (45, 215, 255)  # Or brillant (BGR)


@dataclass
class Balloon:
    id: int
    x: float
    y: float
    base_x: float
    radius_x: int = 32
    radius_y: int = 40
    speed_y: float = 120.0
    oscillation_amplitude: float = 20.0
    oscillation_speed: float = 2.0
    phase: float = 0.0
    color: Tuple[int, int, int] = (50, 60, 240)
    is_golden: bool = False
    points: int = 10
    alive: bool = True
    age: float = 0.0

    @classmethod
    def create_random(
        cls,
        balloon_id: int,
        screen_width: int,
        screen_height: int,
        speed_multiplier: float = 1.0,
        golden_chance: float = 0.15,
    ) -> "Balloon":
        is_golden = random.random() < golden_chance
        radius_x = random.randint(26, 34) if is_golden else random.randint(30, 40)
        radius_y = int(radius_x * 1.25)
        
        # Marges pour que le ballon apparaisse bien dans le cadre
        margin = radius_x + 30
        base_x = random.uniform(margin, max(margin + 10, screen_width - margin))
        y = screen_height + radius_y + random.uniform(5, 50)

        # Vitesses aléatoires avec accélération progressive selon speed_multiplier
        base_speed = (random.uniform(140, 200) if is_golden else random.uniform(90, 150))
        speed_y = base_speed * speed_multiplier
        
        color = GOLDEN_COLOR if is_golden else random.choice(BALLOON_COLORS)
        points = 30 if is_golden else 10
        osc_amp = random.uniform(12.0, 28.0)
        osc_speed = random.uniform(1.8, 3.2)
        phase = random.uniform(0.0, 2 * math.pi)

        return cls(
            id=balloon_id,
            x=base_x,
            y=y,
            base_x=base_x,
            radius_x=radius_x,
            radius_y=radius_y,
            speed_y=speed_y,
            oscillation_amplitude=osc_amp,
            oscillation_speed=osc_speed,
            phase=phase,
            color=color,
            is_golden=is_golden,
            points=points,
        )

    def update(self, dt: float) -> None:
        """Advance balloon position and oscillation."""
        if not self.alive:
            return
        self.age += dt
        self.y -= self.speed_y * dt
        self.x = self.base_x + self.oscillation_amplitude * math.sin(
            self.oscillation_speed * self.age + self.phase
        )

    def is_hit(self, point_x: float, point_y: float) -> bool:
        """Check if (point_x, point_y) hits the balloon with slight ergonomic tolerance."""
        if not self.alive:
            return False
        # Marge ergonomique de +15% pour faciliter le tir en vision
        rx = self.radius_x * 1.15
        ry = self.radius_y * 1.15
        dx = (point_x - self.x) / rx
        dy = (point_y - self.y) / ry
        return (dx * dx + dy * dy) <= 1.0

    def is_offscreen(self) -> bool:
        """Check if balloon has completely exited above screen."""
        return self.y + self.radius_y < 0
