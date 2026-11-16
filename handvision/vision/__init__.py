__all__ = ["StreamCaptureManager"]


def __getattr__(name):
    if name == "StreamCaptureManager":
        from .stream_capture_manager import StreamCaptureManager

        return StreamCaptureManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")