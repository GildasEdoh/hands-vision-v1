from typing import List

import cv2

from handvision.constants import HAND_CONNECTIONS
from handvision.interfaces import Landmark


def draw_hand_landmarks(frame, landmarks: List[Landmark]):
    height, width, _ = frame.shape
    landmarks_per_hand = 21

    for offset in range(0, len(landmarks) - landmarks_per_hand + 1, landmarks_per_hand):
        points = [
            (
                int(landmark.x_ * width),
                int(landmark.y_ * height),
            )
            for landmark in landmarks[offset : offset + landmarks_per_hand]
        ]

        for start, end in HAND_CONNECTIONS:
            cv2.line(frame, points[start], points[end], (0, 255, 0), 2)

        for point in points:
            cv2.circle(frame, point, 5, (0, 0, 255), -1)

        cv2.circle(frame, points[0], 8, (255, 0, 0), -1)

    return frame


def draw_no_hands_results(frame):
    cv2.putText(
        frame,
        "No hand detected",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )