import unittest
from src.collector import duration_seconds


class DurationTests(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(duration_seconds("PT30S"), 30)

    def test_minutes_seconds(self):
        self.assertEqual(duration_seconds("PT2M59S"), 179)

    def test_hours(self):
        self.assertEqual(duration_seconds("PT1H2M3S"), 3723)

    def test_invalid(self):
        self.assertIsNone(duration_seconds("invalid"))

    def test_missing(self):
        self.assertIsNone(duration_seconds(""))


if __name__ == "__main__":
    unittest.main()
