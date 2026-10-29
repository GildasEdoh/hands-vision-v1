import cv2
import mediapipe as mp
import time

# MediaPipe Tasks configuration
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

MODEL_PATH = "hand_landmarker.task"

# Hand skeleton connections
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]


def draw_hand_landmarks(frame, landmarks):
    height, width, _ = frame.shape
    points = []

    # Convert normalized coordinates into pixel coordinates
    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))

    # Draw skeleton connections
    for start, end in HAND_CONNECTIONS:
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


def main():

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

    # Initialize hand detector
    with HandLandmarker.create_from_options(options) as detector:

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise RuntimeError("Unable to access webcam")

        try:
            while True:

                success, frame = cap.read()

                if not success:
                    print("Unable to read webcam frame")
                    break

                # Mirror webcam image
                frame = cv2.flip(frame, 1)

                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB
                )

                # Create MediaPipe image
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame
                )

                # Timestamp in milliseconds
                timestamp_ms = time.monotonic_ns() // 1_000_000

                # Detect hands
                results = detector.detect_for_video(
                    mp_image,
                    timestamp_ms
                )

                # Process detected hands
                if results.hand_landmarks:

                    for index, landmarks in enumerate(
                        results.hand_landmarks
                    ):

                        # Draw hand skeleton
                        draw_hand_landmarks(frame, landmarks)

                        # Get handedness
                        handedness = results.handedness[index][0]
                        hand_label = handedness.category_name

                        cv2.putText(
                            frame,
                            hand_label,
                            (20, 80 + index * 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (255, 255, 0),
                            2
                        )

                        # Get index finger tip coordinates
                        index_tip = landmarks[8]

                        x = index_tip.x
                        y = index_tip.y
                        z = index_tip.z

                        print(
                            f"Index: X={x:.3f}, "
                            f"Y={y:.3f}, Z={z:.3f}"
                        )

                    cv2.putText(
                        frame,
                        f"Hands detected: {len(results.hand_landmarks)}",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )

                else:
                    cv2.putText(
                        frame,
                        "No hand detected",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2
                    )

                # Display webcam
                cv2.imshow(
                    "MediaPipe Hand Tracking",
                    frame
                )

                # Press Q to quit
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()