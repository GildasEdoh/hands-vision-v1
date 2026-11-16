from typing import Sequence

import cv2
import numpy as np

from handvision.interfaces import Landmark
from handvision.my_utils.land_mark_draw import (
    draw_no_hands_results,
)
from handvision.modules.base import VisionModule


class DrawManager(VisionModule):

    def process_frame(
        self,
        frame: np.ndarray,
        landmarks: Sequence[Landmark],
        *,
        fps: float,
        elapsed_seconds: float,
    ) -> np.ndarray:
        height, width = frame.shape[:2]

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2
        alpha = 0.8

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (0, 0),
            (int(width * 0.6), int(height * 0.1)),
            (235, 206, 135),
            thickness=-1,
        )
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        fps_label = f"FPS: {fps:.1f}"
        elapsed_time_label = f"Elapsed: {elapsed_seconds:.1f} s"
        text_color = (0, 0, 255)
        self.draw_top_labels(frame, fps_label, 20, 25, text_color, font, font_scale, thickness)
        time_x = 20 + self._get_label_width(fps_label, font, font_scale, thickness) + 10
        self.draw_top_labels(
            frame,
            elapsed_time_label,
            time_x,
            25,
            text_color,
            font,
            font_scale,
            thickness,
        )

        if not landmarks:
            draw_no_hands_results(frame)
        return frame

    def _get_label_width(self, label, font, font_scale, thickness):
        (text_width, text_height), _ = cv2.getTextSize(
            label,
            font,
            font_scale,
            thickness,
        )
        return text_width

    def draw_top_labels(
        self,
        frame,
        fps_label,
        fps_label_x,
        fps_label_y,
        text_color,
        font,
        fontscale,
        thickness,
    ):
        cv2.putText(
            frame,
            fps_label,
            (fps_label_x, fps_label_y),
            font,
            fontscale,
            text_color,
            thickness,
        )
