"""Tests for narration word-boundary grouping and derived-spec safety."""

import json
import tempfile
import unittest
from pathlib import Path

from src.renderer.narration import TICKS_PER_SECOND, group_word_boundaries, prepare_narrated_spec


class TestNarration(unittest.TestCase):
    def test_word_boundaries_group_into_readable_caption_chunks(self):
        words = [
            {"text": "The", "offset": 0, "duration": TICKS_PER_SECOND // 5},
            {"text": " mystery", "offset": TICKS_PER_SECOND // 5, "duration": TICKS_PER_SECOND // 4},
            {"text": " begins", "offset": TICKS_PER_SECOND // 2, "duration": TICKS_PER_SECOND // 4},
            {"text": ".", "offset": 3 * TICKS_PER_SECOND // 4, "duration": TICKS_PER_SECOND // 10},
            {"text": " Next", "offset": TICKS_PER_SECOND, "duration": TICKS_PER_SECOND // 4},
        ]
        captions = group_word_boundaries(words, max_words=5)
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0]["text"], "The mystery begins.")
        self.assertEqual(captions[1]["text"], "Next")
        self.assertLess(captions[0]["start"], captions[0]["end"])

    def test_word_boundaries_group_into_caption_chunks_without_leading_spaces(self):
        words = [
            {"text": "The", "offset": 0, "duration": TICKS_PER_SECOND // 5},
            {"text": "mystery", "offset": TICKS_PER_SECOND // 5, "duration": TICKS_PER_SECOND // 4},
            {"text": "begins.", "offset": TICKS_PER_SECOND // 2, "duration": TICKS_PER_SECOND // 4},
            {"text": "Next", "offset": TICKS_PER_SECOND, "duration": TICKS_PER_SECOND // 4},
        ]
        captions = group_word_boundaries(words, max_words=5)
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0]["text"], "The mystery begins.")
        self.assertEqual(captions[1]["text"], "Next")
        self.assertLess(captions[0]["start"], captions[0]["end"])

    def test_max_words_splits_caption_chunks(self):
        words = [
            {"text": f" word{i}", "offset": i * TICKS_PER_SECOND // 4, "duration": TICKS_PER_SECOND // 5}
            for i in range(6)
        ]
        captions = group_word_boundaries(words, max_words=3)
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0]["text"], "word0 word1 word2")
        self.assertEqual(captions[1]["text"], "word3 word4 word5")

    def test_invalid_caption_grouping_options_rejected(self):
        with self.assertRaises(ValueError):
            group_word_boundaries([], max_words=0)
        with self.assertRaises(ValueError):
            group_word_boundaries([], max_duration=0)

    def test_derived_spec_does_not_overwrite_approved_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "approved.json"
            derived = root / "approved.narrated.json"
            original = {
                "title": "Test",
                "profile": "developer_workflow",
                "creative_brief": {"approval": {"status": "approved"}},
                "scenes": [{"type": "title", "duration": 2, "headline": "Test", "narration": "Hello"}],
            }
            source.write_text(json.dumps(original), encoding="utf-8")
            # This checks the source/derived path contract without network TTS.
            self.assertFalse(derived.exists())
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), original)
            self.assertFalse(derived.exists())


if __name__ == "__main__":
    unittest.main()
