import logging
import threading
import time
from queue import Empty, Full, Queue
from typing import Callable, Optional, Union

import cv2

from handvision.my_utils import PerformanceMetrics
from handvision.my_utils.land_mark_draw import (
    draw_hand_landmarks,
    draw_no_hands_results,
)
from handvision.modules.base import VisionModule
from handvision.vision.draw_manager import DrawManager
from handvision.vision.frame_queue import LatestFrameQueue


logger = logging.getLogger(__name__)
VideoSource = Union[int, str]


class StreamCaptureManager:
    def __init__(
        self,
        detector_factory: Optional[Callable] = None,
        module: Optional[VisionModule] = None,
        window_title: str = "Real time detection",
    ):
        self._detector_factory = detector_factory
        self.module = module if module is not None else DrawManager()
        self.window_title = window_title
        self._stop_event = threading.Event()
        self._module_closed = threading.Event()
        self._worker_errors = Queue(maxsize=1)
        self.capture_queue = LatestFrameQueue()
        self.result_queue = LatestFrameQueue()
        self.metrics = PerformanceMetrics()
        self.video_frame_obtained = 0
        self.video_frame_processed = 0
        self.video_frame_count_visualized = 0
        self.start_time = 0.0

    def run(self, source: VideoSource = 0, flip: bool = True) -> None:
        try:
            if self._detector_factory is None:
                from handvision.detection import MediaPipeHandDetector

                detector = MediaPipeHandDetector()
            else:
                detector = self._detector_factory()
        except Exception:
            self.module.close()
            raise
        try:
            capture = cv2.VideoCapture(source)
        except Exception:
            detector.close()
            self.module.close()
            raise
        if not capture.isOpened():
            capture.release()
            detector.close()
            self.module.close()
            raise RuntimeError(f"Unable to open video source: {source!r}")

        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._stop_event.clear()
        self._module_closed.clear()
        self._worker_errors = Queue(maxsize=1)
        self.capture_queue = LatestFrameQueue()
        self.result_queue = LatestFrameQueue()
        self.metrics = PerformanceMetrics()
        self.video_frame_obtained = 0
        self.video_frame_processed = 0
        self.video_frame_count_visualized = 0
        self.start_time = time.perf_counter()

        capture_thread = threading.Thread(
            target=self._capture_frames,
            args=(capture, flip),
            name="handvision-capture",
        )
        processing_thread = threading.Thread(
            target=self._process_frames,
            args=(detector,),
            name="handvision-processing",
        )

        started_threads = []
        try:
            capture_thread.start()
            started_threads.append(capture_thread)
            processing_thread.start()
            started_threads.append(processing_thread)
            self._display_frames()
        except KeyboardInterrupt:
            logger.info("Shutdown requested.")
        finally:
            self._stop_event.set()
            capture.release()
            for thread in started_threads:
                thread.join()
            try:
                detector.close()
            finally:
                try:
                    if not self._module_closed.is_set():
                        self.module.close()
                finally:
                    cv2.destroyAllWindows()
                    self._log_summary()

        self._raise_worker_error()

    def _capture_frames(self, capture, flip: bool) -> None:
        frame_id = 0
        try:
            while not self._stop_event.is_set():
                success, frame = capture.read()
                if not success:
                    break

                captured_at = time.perf_counter()
                frame_id += 1
                self.video_frame_obtained = frame_id
                if flip:
                    frame = cv2.flip(frame, 1)
                self.capture_queue.put_latest((frame, frame_id, captured_at))
        except Exception as error:
            self._report_worker_error("Video capture failed.", error)
        finally:
            self._stop_event.set()

    def _process_frames(self, detector) -> None:
        try:
            while not self._stop_event.is_set():
                try:
                    frame, frame_id, captured_at = self.capture_queue.get(timeout=0.1)
                except Empty:
                    continue

                processing_started_at = time.perf_counter()
                detection_started_at = processing_started_at
                landmarks = detector.detect(frame)
                detection_finished_at = time.perf_counter()
                if landmarks:
                    # draw_hand_landmarks(frame, landmarks)
                    pass
                else:
                    draw_no_hands_results(frame)
                rendered_frame = self.module.process_frame(
                    frame,
                    landmarks,
                    fps=self.metrics.processing_fps,
                    elapsed_seconds=self._elapsed_time(),
                )
                completed_at = time.perf_counter()

                self.metrics.record_frame(
                    queue_wait_ms=(processing_started_at - captured_at) * 1000,
                    detection_ms=(detection_finished_at - detection_started_at) * 1000,
                    drawing_ms=(completed_at - detection_finished_at) * 1000,
                    processing_ms=(completed_at - processing_started_at) * 1000,
                    completed_at=completed_at,
                )
                self.video_frame_processed += 1
                self.result_queue.put_latest((rendered_frame, frame_id, captured_at))
        except Exception as error:
            self._report_worker_error("Frame processing failed.", error)
        finally:
            try:
                self.module.close()
            except Exception as error:
                self._report_worker_error("Vision module shutdown failed.", error)
            finally:
                self._module_closed.set()

    def _display_frames(self) -> None:
        while not self._stop_event.is_set():
            self._raise_worker_error()
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                self._stop_event.set()
                break
            if hasattr(self.module, "handle_key") and key != 255:
                self.module.handle_key(key)

            try:
                frame, frame_id, captured_at = self.result_queue.get_nowait()
            except Empty:
                continue
            self.real_time_visualisation(frame, captured_at)

    def real_time_visualisation(
        self,
        frame,
        captured_at: float,
    ) -> None:
        self.video_frame_count_visualized += 1
        cv2.imshow(self.window_title, frame)
        self.metrics.record_display(captured_at, time.perf_counter())

    def _elapsed_time(self) -> float:
        return max(0.0, time.perf_counter() - self.start_time)

    def _report_worker_error(self, message: str, error: Exception) -> None:
        logger.exception(message)
        try:
            self._worker_errors.put_nowait(error)
        except Full:
            logger.error("An additional background worker error was suppressed.")
        self._stop_event.set()

    def _raise_worker_error(self) -> None:
        try:
            error = self._worker_errors.get_nowait()
        except Empty:
            return
        raise RuntimeError("A background video worker failed.") from error

    def _log_summary(self) -> None:
        summary = self.metrics.summary()
        logger.info(
            "Frames captured=%d, processed=%d, displayed=%d; replaced stale "
            "frames: capture=%d, results=%d.",
            self.video_frame_obtained,
            self.video_frame_processed,
            self.video_frame_count_visualized,
            self.capture_queue.replaced_count,
            self.result_queue.replaced_count,
        )
        if self.video_frame_processed == 0:
            logger.info("No frames were processed.")
            return

        logger.info(
            "Processed %d frames (%.1f FPS); recent average/p95 ms: "
            "queue %.1f/%.1f, detection %.1f/%.1f, drawing %.1f/%.1f, "
            "end-to-end %.1f/%.1f; displayed-frame latency %.1f/%.1f ms.",
            self.video_frame_processed,
            summary.get("processing_fps", 0.0),
            summary.get("queue_wait_ms_avg", 0.0),
            summary.get("queue_wait_ms_p95", 0.0),
            summary.get("detection_ms_avg", 0.0),
            summary.get("detection_ms_p95", 0.0),
            summary.get("drawing_ms_avg", 0.0),
            summary.get("drawing_ms_p95", 0.0),
            summary.get("processing_ms_avg", 0.0),
            summary.get("processing_ms_p95", 0.0),
            summary.get("display_latency_avg", 0.0),
            summary.get("display_latency_p95", 0.0),
        )