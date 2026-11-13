from interfaces import Landmark
from typing import Any, List, Dict, Tuple

def get_land_marks(results) -> List[Landmark]:
    mediapie_land_marks = results.hand_landmarks
    marks = []
    for index, landmarks in enumerate(
        mediapie_land_marks
    ):
        for landmark in landmarks:
            mark = Landmark(
                x_=landmark.x,
                y_=landmark.y,
                z_=landmark.z,
                visibility=landmark.visibility,
                name=landmark.name,
                presence=landmark.presence
            )
            marks.append(mark)
    return marks

