import threading
import unittest
from unittest.mock import patch

import numpy as np

from handvision.vision.stream_capture_manager import StreamCaptureManager


class FakeCapture:
    def __init__(self):
        self.released = threading.Event()

    def isOpened(self):
        return True

    def set(self, property_id, value):
        return True

    def read(self):
        if self.released.wait(0.005):
            return False, None
        return True, np.zeros((120, 160, 3), dtype=np.uint8)

    def release(self):
        self.released.set()


class FakeDetector:
    def __init__(self):
        self.closed = False

    def detect(self, frame):
        return []

    def close(self):
        self.closed = True


class FakeModule:
    def __init__(self):
        self.processed_frames = 0
        self.closed = False

    def process_frame(self, frame, landmarks, *, fps, elapsed_seconds):
        self.processed_frames += 1
        return frame

    def close(self):
        self.closed = True


class ModulePipelineTests(unittest.TestCase):
    def test_pipeline_delegates_frames_and_closes_components(self):
        capture = FakeCapture()
        detector = FakeDetector()
        module = FakeModule()
        displayed = threading.Event()

        with (
            patch(
                "handvision.vision.stream_capture_manager.cv2.VideoCapture",
                return_value=capture,
            ),
            patch(
                "handvision.vision.stream_capture_manager.cv2.waitKey",
                side_effect=lambda delay: ord("q") if displayed.is_set() else -1,
            ),
            patch(
                "handvision.vision.stream_capture_manager.cv2.imshow",
                side_effect=lambda *args: displayed.set(),
            ),
            patch("handvision.vision.stream_capture_manager.cv2.destroyAllWindows"),
        ):
            manager = StreamCaptureManager(
                detector_factory=lambda: detector,
                module=module,
            )
            manager.run()

        self.assertGreater(module.processed_frames, 0)
        self.assertTrue(module.closed)
        self.assertTrue(detector.closed)


if __name__ == "__main__":
    unittest.main()
