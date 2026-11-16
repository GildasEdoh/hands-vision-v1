import unittest

from handvision.core.timing import MonotonicMillisecondClock


class MonotonicMillisecondClockTests(unittest.TestCase):
    def test_timestamps_strictly_increase_when_clock_repeats(self):
        clock = MonotonicMillisecondClock(lambda: 5_000_000_000)

        self.assertEqual(clock.next(), 5000)
        self.assertEqual(clock.next(), 5001)


if __name__ == "__main__":
    unittest.main()
