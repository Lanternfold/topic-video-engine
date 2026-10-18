"""Audio track mixing and frame-clock-aligned muxing through FFmpeg."""

import math
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional


class AudioMixError(Exception):
    """Raised when configured audio tracks cannot be mixed into the video."""


def resolve_audio_tracks(
    tracks: List[Dict[str, Any]], base_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Resolve audio source paths relative to the spec directory and check files."""
    root = Path(base_dir) if base_dir is not None else Path.cwd()
    resolved = []
    for index, track in enumerate(tracks):
        source = track.get("source")
        if not isinstance(source, str) or not source.strip():
            raise AudioMixError(f"Audio track {index} requires a non-empty source path")
        path = Path(source)
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            raise AudioMixError(f"Audio track {index} source file not found: {path}")
        resolved.append({**track, "source": str(path.resolve())})
    return resolved


def build_audio_filter(
    tracks: List[Dict[str, Any]], video_duration: float
) -> str:
    """Build deterministic FFmpeg filters; start offsets are expressed in seconds."""
    if not math.isfinite(video_duration) or video_duration <= 0:
        raise AudioMixError("video duration must be positive and finite")
    filters = []
    labels = []
    for index, track in enumerate(tracks):
        start = float(track.get("start", 0.0))
        gain = float(track.get("gain", 1.0))
        remaining = video_duration - start
        requested_duration = track.get("duration")
        duration = min(
            remaining,
            float(requested_duration) if requested_duration is not None else remaining,
        )
        if start < 0 or start >= video_duration:
            raise AudioMixError(f"Audio track {index} start must be inside the video duration")
        if not math.isfinite(gain) or gain < 0 or gain > 4:
            raise AudioMixError(f"Audio track {index} gain must be between 0 and 4")
        if not math.isfinite(duration) or duration <= 0:
            raise AudioMixError(f"Audio track {index} duration must be positive")
        delay_ms = round(start * 1000)
        filters.append(
            f"[{index + 1}:a:0]atrim=duration={duration:.6f},"
            f"asetpts=PTS-STARTPTS,volume={gain:.6f},"
            f"adelay=delays={delay_ms}:all=1[a{index}]"
        )
        labels.append(f"[a{index}]")
    if len(labels) == 1:
        filters.append(f"{labels[0]}apad,atrim=duration={video_duration:.6f}[aout]")
    else:
        filters.append(
            f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:"
            f"dropout_transition=0:normalize=0,apad,atrim=duration={video_duration:.6f}[aout]"
        )
    return ";".join(filters)


def mux_audio_tracks(
    video_path: Path,
    tracks: List[Dict[str, Any]],
    video_duration: float,
    base_dir: Optional[Path] = None,
) -> Path:
    """Mix external audio files and mux them onto a rendered silent video.

    Track start times are relative to the start of the video. The video stream is
    copied without re-encoding; mixed audio is encoded to AAC. The final duration
    remains bounded to the rendered frame timeline.
    """
    video_path = Path(video_path)
    if not tracks:
        return video_path
    if not video_path.is_file():
        raise AudioMixError(f"Rendered video not found: {video_path}")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise AudioMixError("FFmpeg is required to mix audio tracks")
    resolved = resolve_audio_tracks(tracks, base_dir=base_dir)
    filter_graph = build_audio_filter(resolved, video_duration)
    temp_path = video_path.with_name(f"{video_path.stem}.audio-tmp{video_path.suffix}")
    command = [ffmpeg, "-y", "-i", str(video_path)]
    for track in resolved:
        command.extend(["-i", track["source"]])
    command.extend([
        "-filter_complex", filter_graph,
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{video_duration:.6f}", "-movflags", "+faststart",
        str(temp_path),
    ])
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown FFmpeg error").strip()
            raise AudioMixError(f"FFmpeg audio mix failed: {detail[-2500:]}")
        os.replace(temp_path, video_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return video_path
