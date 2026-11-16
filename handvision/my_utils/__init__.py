__all__ = ["PerformanceMetrics", "get_land_marks", "draw_hand_landmarks"]


def __getattr__(name):
    if name == "PerformanceMetrics":
        from .detections_metrics import PerformanceMetrics

        return PerformanceMetrics
    if name == "get_land_marks":
        from .extract_land_mark import get_land_marks

        return get_land_marks
    if name == "draw_hand_landmarks":
        from .land_mark_draw import draw_hand_landmarks

        return draw_hand_landmarks
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")