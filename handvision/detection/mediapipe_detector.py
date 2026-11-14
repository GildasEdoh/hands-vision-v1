import mediapipe as mp
from handvision.constants import MODEL_PATH
from handvision.interfaces import Landmark
from handvision.my_utils import get_land_marks
from typing import List
import time

# MediaPipe Tasks configuration
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions 
RunningMode = mp.tasks.vision.RunningMode
options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    running_mode=RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

global_handlandmarker = None

with HandLandmarker.create_from_options(options) as landmarker:
    global_handlandmarker = landmarker


def run_detection(frame) -> List[Landmark]:
    global global_handlandmarker
    if not global_handlandmarker:
        with HandLandmarker.create_from_options(options) as landmarker:
            global_handlandmarker = landmarker

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    timestamp_ms = time.monotonic_ns() // 1_000_000
    results = global_handlandmarker.detect_async(mp_image, timestamp_ms)
    print('results = ', results)
    landmarks = get_land_marks(results)
    return landmarks

