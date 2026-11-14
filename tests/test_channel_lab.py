"""Pruebas sin claves ni acceso real a YouTube."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import channel_lab as lab


class ChannelLabTests(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(lab.duration_seconds("PT1M23S"), 83)
        self.assertEqual(lab.duration_seconds("PT3M"), 180)
        self.assertIsNone(lab.duration_seconds("unknown"))

    def test_public_rows(self):
        sample = [{"id": "abc", "snippet": {"title": "¿Qué pasaría si...?", "publishedAt": "2026-11-13T12:00:00Z"},
                   "contentDetails": {"duration": "PT45S"},
                   "statistics": {"viewCount": "2000", "likeCount": "100"}}]
        row = lab.video_rows(sample)[0]
        self.assertTrue(row["short_candidate"])
        self.assertEqual(row["likes_per_1000_views"], 50)
        self.assertIsNone(row["comments"])

    def test_correction_and_question(self):
        self.assertEqual(lab.suggest_reply("Eso es falso")["category"], "correction")
        self.assertEqual(lab.suggest_reply("¿Por qué ocurre?")["category"], "question")
        self.assertIsNone(lab.suggest_reply("Eres un idiota")["suggestion"])

    def test_fetch_channel(self):
        with patch.object(lab, "request_api", return_value={"items": [{"id": "UCtest"}]}) as api:
            self.assertEqual(lab.channel_details("@Neutrinitoo")["id"], "UCtest")
            self.assertEqual(api.call_args.args[0], "channels")

    def test_trends_are_title_keywords_not_search_volume(self):
        terms = lab.keywords(["El océano cambia", "Océano y clima"])
        self.assertEqual(terms[0], {"term": "oceano", "mentions": 2})


if __name__ == "__main__":
    unittest.main()
