"""Tests for audio track filter construction and source resolution."""

import tempfile
import unittest
from pathlib import Path

from src.renderer.audio import AudioMixError, build_audio_filter, resolve_audio_tracks
from src.renderer.validator import validate_spec


class TestAudioTracks(unittest.TestCase):
    def test_single_track_filter_applies_offset_gain_and_video_duration(self):
        graph = build_audio_filter(
            [{"source": "voice.wav", "start": 1.25, "gain": 0.8}], 5.0
        )
        self.assertIn("[1:a:0]", graph)
        self.assertIn("volume=0.800000", graph)
        self.assertIn("adelay=delays=1250:all=1", graph)
        self.assertIn("atrim=duration=5.000000", graph)

    def test_multiple_tracks_are_mixed_and_trimmed(self):
        graph = build_audio_filter(
            [
                {"source": "voice.wav", "start": 0, "gain": 1},
                {"source": "music.wav", "start": 0.5, "gain": 0.2},
            ],
            8.0,
        )
        self.assertIn("amix=inputs=2", graph)
        self.assertIn("volume=0.200000", graph)
        self.assertIn("atrim=duration=8.000000[aout]", graph)

    def test_invalid_track_timing_or_gain_is_rejected(self):
        with self.assertRaises(AudioMixError):
            build_audio_filter([{"source": "x.wav", "start": 5}], 5)
        with self.assertRaises(AudioMixError):
            build_audio_filter([{"source": "x.wav", "gain": 5}], 5)
        with self.assertRaises(AudioMixError):
            build_audio_filter([{"source": "x.wav", "duration": 0}], 5)

    def test_relative_audio_source_resolves_from_spec_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            audio_file = root / "voice.wav"
            audio_file.write_bytes(b"placeholder")
            resolved = resolve_audio_tracks([{"source": "voice.wav"}], root)
            self.assertEqual(resolved[0]["source"], str(audio_file.resolve()))

    def test_missing_audio_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(AudioMixError):
                resolve_audio_tracks([{"source": "missing.wav"}], Path(temp_dir))

    def test_audio_track_spec_validation(self):
        spec = {
            "title": "Audio test",
            "profile": "developer_workflow",
            "creative_brief": {
                "visual_mood": "Test",
                "pacing": "Measured",
                "transitions": "Cuts",
                "rationale": "Test",
                "approval": {"status": "approved"},
            },
            "audio": {"tracks": [{"source": "voice.wav", "start": -1}]},
            "scenes": [{"type": "title", "duration": 1, "headline": "Test"}],
        }
        self.assertTrue(any("start must be a finite non-negative" in e for e in validate_spec(spec)))


if __name__ == "__main__":
    unittest.main()
