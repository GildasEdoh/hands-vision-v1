import random
from typing import List, Optional, Tuple

from handvision.game.balloon import Balloon


class TargetManager:
    """Manages active balloons, spawning rules, speed progression, and hit detection."""

    def __init__(
        self,
        base_spawn_interval: float = 1.3,
        max_balloons: int = 5,
        golden_chance: float = 0.18,
    ):
        self.base_spawn_interval = base_spawn_interval
        self.max_balloons = max_balloons
        self.golden_chance = golden_chance
        self.balloons: List[Balloon] = []
        self.spawn_timer: float = 0.0
        self.balloon_id_counter: int = 0
        self.speed_multiplier: float = 1.0

    def update_difficulty(self, current_score: int) -> None:
        """Gradually scales speed and spawn rate as score increases."""
        # Tous les 50 points, la vitesse augmente de 8%
        level = current_score // 50
        self.speed_multiplier = min(2.2, 1.0 + level * 0.08)

    def update(
        self,
        dt: float,
        screen_width: int,
        screen_height: int,
    ) -> List[Balloon]:
        """
        Updates balloons and spawns new ones.
        Returns a list of balloons that escaped off the top of the screen.
        """
        escaped: List[Balloon] = []
        surviving: List[Balloon] = []

        for b in self.balloons:
            b.update(dt)
            if b.is_offscreen():
                escaped.append(b)
            else:
                surviving.append(b)
        self.balloons = surviving

        # Spawn logic
        self.spawn_timer += dt
        effective_interval = max(0.7, self.base_spawn_interval / (self.speed_multiplier ** 0.5))

        if self.spawn_timer >= effective_interval and len(self.balloons) < self.max_balloons:
            self.spawn_timer = 0.0
            self.balloon_id_counter += 1
            new_balloon = Balloon.create_random(
                balloon_id=self.balloon_id_counter,
                screen_width=screen_width,
                screen_height=screen_height,
                speed_multiplier=self.speed_multiplier,
                golden_chance=self.golden_chance,
            )
            self.balloons.append(new_balloon)

        return escaped

    def check_hit(self, point_x: float, point_y: float) -> Optional[Balloon]:
        """
        Checks if a shot at (point_x, point_y) hits any active balloon.
        If multiple balloons overlap, hits the closest one.
        """
        hit_candidates: List[Tuple[float, Balloon]] = []

        for b in self.balloons:
            if b.is_hit(point_x, point_y):
                dist_sq = (point_x - b.x) ** 2 + (point_y - b.y) ** 2
                hit_candidates.append((dist_sq, b))

        if not hit_candidates:
            return None

        # Trier pour toucher le ballon le plus proche du centre de visée
        hit_candidates.sort(key=lambda item: item[0])
        hit_balloon = hit_candidates[0][1]
        hit_balloon.alive = False
        self.balloons.remove(hit_balloon)
        return hit_balloon

    def clear(self) -> None:
        self.balloons.clear()
        self.spawn_timer = 0.0
        self.speed_multiplier = 1.0
