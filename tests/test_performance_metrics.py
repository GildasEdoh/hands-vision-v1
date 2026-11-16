import unittest

from handvision.my_utils.detections_metrics import PerformanceMetrics


class PerformanceMetricsTests(unittest.TestCase):
    def test_empty_summary_is_safe(self):
        self.assertEqual(PerformanceMetrics().summary(), {"frames": 0})

    def test_summary_reports_recent_timing_and_display_latency(self):
        metrics = PerformanceMetrics(max_samples=2)
        metrics.record_frame(1, 10, 2, 13, 1.0)
        metrics.record_display(1.0, 1.02)
        metrics.record_frame(2, 20, 4, 26, 2.0)

        summary = metrics.summary()

        self.assertEqual(metrics.frame_count, 2)
        self.assertEqual(summary["queue_wait_ms_avg"], 1.5)
        self.assertEqual(summary["detection_ms_avg"], 15)
        self.assertAlmostEqual(summary["display_latency_avg"], 20)
        self.assertEqual(summary["processing_fps"], 1.0)


if __name__ == "__main__":
    unittest.main()
