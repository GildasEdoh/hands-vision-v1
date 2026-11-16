from dataclasses import dataclass
from math import hypot
import time
from typing import Optional, Sequence, Tuple

from handvision.interfaces import Landmark


LANDMARKS_PER_HAND = 21
MIN_FINGER_DISTANCE_RATIO = 0.025
MAX_FINGER_DISTANCE_RATIO = 0.25


@dataclass(frozen=True)
class VolumeControlGeometry:
    icon_center: Tuple[int, int]
    icon_radius: int
    slider_x: int
    slider_top: int
    slider_bottom: int
    min_finger_distance: float
    max_finger_distance: float


@dataclass(frozen=True)
class GestureAction:
    slider_open: bool
    slider_toggled: bool
    volume_ratio: Optional[float]


def get_control_geometry(width: int, height: int) -> VolumeControlGeometry:
    min_dimension = min(width, height)
    icon_margin = max(24, min(48, int(min_dimension * 0.08)))
    icon_radius = max(18, int(min_dimension * 0.065))
    slider_x = width - max(48, int(width * 0.11))
    return VolumeControlGeometry(
        icon_center=(width - icon_margin, icon_margin),
        icon_radius=icon_radius,
        slider_x=slider_x,
        slider_top=int(height * 0.2),
        slider_bottom=int(height * 0.75),
        min_finger_distance=min_dimension * MIN_FINGER_DISTANCE_RATIO,
        max_finger_distance=min_dimension * MAX_FINGER_DISTANCE_RATIO,
    )


class VolumeGestureController:
    def __init__(self):
        self.slider_open = False
        self._icon_was_touched = False
        self._last_toggle_at = float("-inf")

    def update(
        self,
        landmarks: Sequence[Landmark],
        width: int,
        height: int,
        now: Optional[float] = None,
    ) -> GestureAction:
        now = time.monotonic() if now is None else now
        geometry = get_control_geometry(width, height)
        hands = []
        for offset in range(0, len(landmarks), LANDMARKS_PER_HAND):
            hand = landmarks[offset : offset + LANDMARKS_PER_HAND]
            if len(hand) == LANDMARKS_PER_HAND:
                hands.append(hand)

        icon_x, icon_y = geometry.icon_center
        icon_hit_radius = geometry.icon_radius * 1.5
        icon_touched = any(
            hypot(hand[8].x_ * width - icon_x, hand[8].y_ * height - icon_y)
            <= icon_hit_radius
            for hand in hands
        )

        finger_distances = []
        for hand in hands:
            thumb_x, thumb_y = hand[4].x_ * width, hand[4].y_ * height
            index_x, index_y = hand[8].x_ * width, hand[8].y_ * height
            distance = hypot(index_x - thumb_x, index_y - thumb_y)
            if distance <= geometry.max_finger_distance:
                finger_distances.append(distance)

        slider_toggled = False
        if (
            icon_touched
            and not self._icon_was_touched
            and now - self._last_toggle_at >= 0.4
        ):
            self.slider_open = not self.slider_open
            self._last_toggle_at = now
            slider_toggled = True
        self._icon_was_touched = icon_touched

        volume_ratio = None
        if self.slider_open and not slider_toggled and finger_distances:
            distance = finger_distances[0]
            distance_range = (
                geometry.max_finger_distance - geometry.min_finger_distance
            )
            volume_ratio = (distance - geometry.min_finger_distance) / distance_range
            volume_ratio = max(0.0, min(1.0, volume_ratio))

        return GestureAction(
            slider_open=self.slider_open,
            slider_toggled=slider_toggled,
            volume_ratio=volume_ratio,
        )
