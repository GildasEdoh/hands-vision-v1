from pathlib import Path
from typing import List

import cv2
import mediapipe as mp

from handvision.constants import MODEL_PATH
from handvision.core.timing import MonotonicMillisecondClock
from handvision.interfaces import Landmark
from handvision.my_utils.extract_land_mark import get_land_marks


class MediaPipeHandDetector:
    def __init__(self, model_path=MODEL_PATH):
        model_path = Path(model_path)
        if not model_path.is_file():
            raise FileNotFoundError(f"MediaPipe hand model not found: {model_path}")

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self._landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self._clock = MonotonicMillisecondClock()

    def detect(self, frame) -> List[Landmark]:
        if self._landmarker is None:
            raise RuntimeError("The hand detector is closed.")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self._landmarker.detect_for_video(image, self._clock.next())

        if not results.hand_landmarks:
            return []
        return get_land_marks(results)

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
