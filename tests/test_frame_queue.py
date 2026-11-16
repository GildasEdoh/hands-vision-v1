import unittest

from handvision.vision.frame_queue import LatestFrameQueue


class LatestFrameQueueTests(unittest.TestCase):
    def test_put_latest_replaces_stale_item(self):
        frames = LatestFrameQueue()
        frames.put_latest("old")
        frames.put_latest("new")

        self.assertEqual(frames.get_nowait(), "new")
        self.assertEqual(frames.replaced_count, 1)


if __name__ == "__main__":
    unittest.main()
