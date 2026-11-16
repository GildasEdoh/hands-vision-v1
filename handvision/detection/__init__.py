__all__ = ["MediaPipeHandDetector"]


def __getattr__(name):
    if name == "MediaPipeHandDetector":
        from .mediapipe_detector import MediaPipeHandDetector

        return MediaPipeHandDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")