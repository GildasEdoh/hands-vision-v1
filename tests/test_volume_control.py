import unittest

import numpy as np

from handvision.interfaces import Landmark
from handvision.modules.volume_control import VolumeControlModule
from handvision.modules.volume_control.gesture import (
    VolumeGestureController,
    get_control_geometry,
)


def make_hand(thumb, index):
    hand = [Landmark(0.5, 0.5, 0.0, None, None, None) for _ in range(21)]
    hand[4] = Landmark(thumb[0], thumb[1], 0.0, None, None, None)
    hand[8] = Landmark(index[0], index[1], 0.0, None, None, None)
    return hand


def make_volume_gesture(geometry, width, height, distance, center=None):
    if center is None:
        center = (
            geometry.slider_x,
            (geometry.slider_top + geometry.slider_bottom) / 2,
        )
    center_x, center_y = center
    return make_hand(
        thumb=(
            (center_x - distance / 2) / width,
            center_y / height,
        ),
        index=(
            (center_x + distance / 2) / width,
            center_y / height,
        ),
    )


class FakeVolumeController:
    def __init__(self, value=0.25):
        self.value = value
        self.closed = False

    def get_volume(self):
        return self.value

    def set_volume(self, value):
        self.value = value

    def close(self):
        self.closed = True


class VolumeGestureControllerTests(unittest.TestCase):
    def test_index_touch_opens_slider_and_pinch_sets_ratio(self):
        width, height = 640, 480
        geometry = get_control_geometry(width, height)
        gestures = VolumeGestureController()

        icon_hand = make_hand(
            thumb=(0.5, 0.5),
            index=(
                geometry.icon_center[0] / width,
                geometry.icon_center[1] / height,
            ),
        )
        opened = gestures.update(icon_hand, width, height, now=1.0)
        self.assertTrue(opened.slider_open)
        self.assertTrue(opened.slider_toggled)

        pinch_hand = make_volume_gesture(
            geometry,
            width,
            height,
            (geometry.min_finger_distance + geometry.max_finger_distance) / 2,
            center=(width * 0.3, height * 0.4),
        )
        adjusted = gestures.update(pinch_hand, width, height, now=1.1)

        self.assertAlmostEqual(adjusted.volume_ratio, 0.5)
        lower = gestures.update(
            make_volume_gesture(
                geometry,
                width,
                height,
                geometry.min_finger_distance,
            ),
            width,
            height,
            now=1.2,
        )
        higher = gestures.update(
            make_volume_gesture(
                geometry,
                width,
                height,
                geometry.max_finger_distance,
            ),
            width,
            height,
            now=1.3,
        )
        self.assertAlmostEqual(lower.volume_ratio, 0.0)
        self.assertAlmostEqual(higher.volume_ratio, 1.0)

        gestures.update([], width, height, now=1.4)
        closed = gestures.update(icon_hand, width, height, now=1.5)
        self.assertFalse(closed.slider_open)


class VolumeControlModuleTests(unittest.TestCase):
    def test_gesture_updates_system_volume_and_closes_controller(self):
        width, height = 640, 480
        geometry = get_control_geometry(width, height)
        volume_controller = FakeVolumeController()
        module = VolumeControlModule(lambda: volume_controller)
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        icon_hand = make_hand(
            thumb=(0.5, 0.5),
            index=(
                geometry.icon_center[0] / width,
                geometry.icon_center[1] / height,
            ),
        )
        module.process_frame(
            frame.copy(),
            icon_hand,
            fps=30.0,
            elapsed_seconds=1.0,
        )
        pinch_hand = make_volume_gesture(
            geometry,
            width,
            height,
            (geometry.min_finger_distance + geometry.max_finger_distance) / 2,
            center=(width * 0.3, height * 0.4),
        )
        module.process_frame(
            frame.copy(),
            pinch_hand,
            fps=30.0,
            elapsed_seconds=1.1,
        )

        self.assertAlmostEqual(volume_controller.value, 0.5)
        module.close()
        self.assertTrue(volume_controller.closed)


if __name__ == "__main__":
    unittest.main()
