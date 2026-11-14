import cv2


def draw_hand_landmarks(frame, landmarks, hand_connections):
    height, width, _ = frame.shape
    points = []

    # Convert normalized coordinates into pixel coordinates
    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))

    # Draw skeleton connections
    for start, end in hand_connections:
        cv2.line(
            frame,
            points[start],
            points[end],
            (0, 255, 0),
            2
        )

    # Draw landmarks
    for point in points:
        cv2.circle(
            frame,
            point,
            5,
            (0, 0, 255),
            -1
        )

    # Highlight wrist
    cv2.circle(
        frame,
        points[0],
        8,
        (255, 0, 0),
        -1
    )