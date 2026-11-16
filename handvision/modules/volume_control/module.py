from typing import Callable, Optional, Sequence

import cv2
import numpy as np

from handvision.interfaces import Landmark
from handvision.modules.base import VisionModule
from handvision.modules.volume_control.audio import (
    VolumeController,
    WindowsAudioVolumeController,
)
from handvision.modules.volume_control.gesture import (
    VolumeGestureController,
    get_control_geometry,
)


class VolumeControlModule(VisionModule):
    def __init__(
        self,
        volume_controller_factory: Callable[[], VolumeController] = (
            WindowsAudioVolumeController
        ),
    ):
        self._volume_controller_factory = volume_controller_factory
        self._volume_controller: Optional[VolumeController] = None
        self._volume = 0.0
        self._gestures = VolumeGestureController()

    def process_frame(
        self,
        frame: np.ndarray,
        landmarks: Sequence[Landmark],
        *,
        fps: float,
        elapsed_seconds: float,
    ) -> np.ndarray:
        controller = self._get_volume_controller()
        height, width = frame.shape[:2]
        action = self._gestures.update(landmarks, width, height)

        if (
            action.volume_ratio is not None
            and abs(action.volume_ratio - self._volume) >= 0.01
        ):
            controller.set_volume(action.volume_ratio)
            self._volume = action.volume_ratio

        self._draw_volume_icon(frame)
        self._draw_hud(frame, action.slider_open, fps, elapsed_seconds)
        return frame

    def close(self) -> None:
        if self._volume_controller is not None:
            self._volume_controller.close()
            self._volume_controller = None

    def _get_volume_controller(self) -> VolumeController:
        if self._volume_controller is None:
            self._volume_controller = self._volume_controller_factory()
            self._volume = self._volume_controller.get_volume()
        return self._volume_controller

    def _draw_volume_icon(self, frame: np.ndarray) -> None:
        height, width = frame.shape[:2]
        geometry = get_control_geometry(width, height)
        center_x, center_y = geometry.icon_center
        radius = geometry.icon_radius
        color = (80, 220, 100) if self._gestures.slider_open else (235, 206, 135)

        cv2.circle(frame, (center_x, center_y), radius, (30, 30, 30), -1)
        cv2.circle(frame, (center_x, center_y), radius, color, 2)
        speaker = np.array(
            [
                (center_x - radius // 2, center_y - radius // 4),
                (center_x - radius // 4, center_y - radius // 4),
                (center_x + radius // 5, center_y - radius // 2),
                (center_x + radius // 5, center_y + radius // 2),
                (center_x - radius // 4, center_y + radius // 4),
                (center_x - radius // 2, center_y + radius // 4),
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(frame, [speaker], color)
        if self._volume < 0.01:
            cv2.line(
                frame,
                (center_x + radius // 3, center_y - radius // 3),
                (center_x + radius * 2 // 3, center_y + radius // 3),
                (0, 0, 255),
                2,
            )
            cv2.line(
                frame,
                (center_x + radius * 2 // 3, center_y - radius // 3),
                (center_x + radius // 3, center_y + radius // 3),
                (0, 0, 255),
                2,
            )
        else:
            cv2.ellipse(
                frame,
                (center_x + radius // 6, center_y),
                (radius // 2, radius // 2),
                0,
                -55,
                55,
                color,
                2,
            )

    def _draw_hud(
        self,
        frame: np.ndarray,
        slider_open: bool,
        fps: float,
        elapsed_seconds: float,
    ) -> None:
        height, width = frame.shape[:2]
        geometry = get_control_geometry(width, height)
        panel_top = max(0, height - 112)
        panel_right = max(0, geometry.slider_x - 28)
        cv2.rectangle(
            frame,
            (0, panel_top),
            (panel_right, height),
            (25, 25, 25),
            -1,
        )
        volume_percent = int(round(self._volume * 100))

        if slider_open:
            cv2.putText(
                frame,
                "Barre = indicateur; ecart pouce-index = volume.",
                (12, panel_top + 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (245, 245, 245),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                "Rapprochez = moins; eloignez = plus.",
                (12, panel_top + 46),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (200, 200, 200),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Volume: {volume_percent}%",
                (12, panel_top + 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (245, 245, 245),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                "Touchez l'icone avec l'index pour masquer.",
                (12, panel_top + 93),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (200, 200, 200),
                1,
                cv2.LINE_AA,
            )
            cv2.rectangle(
                frame,
                (geometry.slider_x - 7, geometry.slider_top),
                (geometry.slider_x + 7, geometry.slider_bottom),
                (90, 90, 90),
                -1,
            )
            fill_y = geometry.slider_bottom - int(
                (geometry.slider_bottom - geometry.slider_top) * self._volume
            )
            cv2.rectangle(
                frame,
                (geometry.slider_x - 7, fill_y),
                (geometry.slider_x + 7, geometry.slider_bottom),
                (80, 220, 100),
                -1,
            )
            cv2.circle(
                frame,
                (geometry.slider_x, fill_y),
                10,
                (245, 245, 245),
                -1,
            )
        else:
            cv2.putText(
                frame,
                "Touchez l'icone volume avec l'index pour afficher les commandes.",
                (12, panel_top + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (245, 245, 245),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Volume: {volume_percent}%",
                (12, panel_top + 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (200, 200, 200),
                1,
                cv2.LINE_AA,
            )

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}   Temps: {elapsed_seconds:.1f} s",
            (12, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (170, 170, 170),
            1,
            cv2.LINE_AA,
        )
