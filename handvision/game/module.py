import math
import time
from typing import Optional, Sequence, Tuple

import cv2
import numpy as np

from handvision.interfaces import Landmark
from handvision.modules.base import VisionModule
from handvision.my_utils.land_mark_draw import draw_hand_landmarks
from handvision.game.game_engine import GameEngine, GameState


class BalloonShooterGameModule(VisionModule):
    """
    Vision-based balloon shooting game module.
    
    Uses index fingertip (Landmark #8) as a precision laser pointer,
    and thumb-to-index pinch (Landmark #4 & #8) to shoot and pop balloons.
    """

    def __init__(
        self,
        sound_enabled: bool = True,
        base_pinch_threshold: float = 38.0,
        show_skeleton: bool = False,
    ):
        self.engine = GameEngine(sound_enabled=sound_enabled)
        self.base_pinch_threshold = base_pinch_threshold
        self.show_skeleton = show_skeleton

        self._was_pinched: bool = False
        self._last_frame_time: Optional[float] = None
        self._last_shot_time: float = 0.0

    def process_frame(
        self,
        frame: np.ndarray,
        landmarks: Sequence[Landmark],
        *,
        fps: float,
        elapsed_seconds: float,
    ) -> np.ndarray:
        now = time.monotonic()
        if self._last_frame_time is None:
            dt = 1.0 / max(1.0, fps) if fps > 0 else 0.033
        else:
            dt = max(0.001, min(0.1, now - self._last_frame_time))
        self._last_frame_time = now

        height, width = frame.shape[:2]

        # 1. Optionnel : squelette discret de la main
        if self.show_skeleton and landmarks:
            draw_hand_landmarks(frame, list(landmarks))

        # 2. Analyse des landmarks pour la visée et le tir
        cursor_pos: Optional[Tuple[int, int]] = None
        thumb_pos: Optional[Tuple[int, int]] = None
        is_pinched = False
        pinch_ratio = 1.0

        if len(landmarks) >= 21:
            # Main principale (première main détectée)
            # Landmark #8 : bout de l'index
            ix = int(landmarks[8].x_ * width)
            iy = int(landmarks[8].y_ * height)
            cursor_pos = (ix, iy)

            # Landmark #4 : bout du pouce
            tx = int(landmarks[4].x_ * width)
            ty = int(landmarks[4].y_ * height)
            thumb_pos = (tx, ty)

            # Distance euclidienne en pixels entre le pouce et l'index
            distance = math.hypot(ix - tx, iy - ty)

            # Calibrage adaptatif du seuil selon l'éloignement de la main
            # Distance entre le poignet (#0) et la base du majeur (#9)
            hand_scale = math.hypot(
                (landmarks[9].x_ - landmarks[0].x_) * width,
                (landmarks[9].y_ - landmarks[0].y_) * height,
            )
            # Seuil dynamique clamped entre 24px et 55px
            dynamic_threshold = max(24.0, min(55.0, hand_scale * 0.32)) if hand_scale > 20 else self.base_pinch_threshold

            # Ratio de pincement (0.0 = complètement pincé, 1.0 = détendu)
            pinch_ratio = min(1.0, max(0.0, (distance - dynamic_threshold) / (dynamic_threshold * 1.6)))
            is_pinched = distance <= dynamic_threshold

            # Détection du tir : front montant (transition relâché -> pincé)
            # Cooldown de 140ms pour absorber le jitter haute fréquence
            if is_pinched and not self._was_pinched and (now - self._last_shot_time >= 0.14):
                self._last_shot_time = now
                self.engine.handle_shot(ix, iy, width, height)

            self._was_pinched = is_pinched
        else:
            self._was_pinched = False

        # 3. Mise à jour physique et logique du jeu
        self.engine.update(dt, width, height)

        # 4. Rendu visuel complet
        frame = self.engine.render(
            frame,
            fps=fps,
            cursor_pos=cursor_pos,
            thumb_pos=thumb_pos,
            is_pinched=is_pinched,
            pinch_ratio=pinch_ratio,
        )

        return frame

    def handle_key(self, key: int) -> None:
        """Handle keyboard shortcuts directly during gameplay."""
        if key in (ord("r"), ord("R")):
            self.engine.start_game()
        elif key in (ord("s"), ord("S")):
            self.engine.sound.enabled = not self.engine.sound.enabled
        elif key in (ord("h"), ord("H")):
            self.show_skeleton = not self.show_skeleton

    def close(self) -> None:
        """Cleanup any resources on module shutdown."""
        self.engine.target_manager.clear()
