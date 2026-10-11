"""Video verification utility using ffprobe."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, Optional


def probe_video(video_path: Path) -> Dict[str, Any]:
    """Inspect video file metadata using ffprobe."""
    video_path = Path(video_path)
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    ffprobe_bin = shutil.which("ffprobe")
    if not ffprobe_bin:
        raise RuntimeError("ffprobe executable not found in PATH.")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,duration,nb_frames",
        "-of", "json",
        str(video_path),
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse ffprobe JSON output: {e}") from e


def verify_video(
    video_path: Path,
    expected_width: Optional[int] = None,
    expected_height: Optional[int] = None,
    expected_fps: Optional[float] = None,
    expected_duration: Optional[float] = None,
    duration_tolerance: float = 0.25,
) -> Dict[str, Any]:
    """Verify video properties against expected parameters.

    Returns dict of extracted video properties if all checks pass.
    Raises AssertionError or RuntimeError if any check fails.
    """
    data = probe_video(video_path)
    streams = data.get("streams", [])
    fmt = data.get("format", {})

    if not streams:
        raise AssertionError(f"No streams detected in {video_path}")

    # Find primary video stream
    video_stream = next((s for s in streams if "width" in s and "height" in s), None)
    if not video_stream:
        raise AssertionError(f"No video stream found in {video_path}")

    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    codec = video_stream.get("codec_name", "")

    # Frame rate calculation
    r_frame_rate = video_stream.get("r_frame_rate", "0/1")
    if "/" in r_frame_rate:
        num, den = r_frame_rate.split("/")
        fps = float(num) / float(den) if float(den) > 0 else 0.0
    else:
        fps = float(r_frame_rate)

    duration = float(fmt.get("duration", 0.0))
    file_size = int(fmt.get("size", 0))

    if file_size <= 0:
        raise AssertionError(f"Video file size is zero bytes: {video_path}")

    if expected_width is not None and width != expected_width:
        raise AssertionError(f"Width mismatch: expected {expected_width}, found {width}")

    if expected_height is not None and height != expected_height:
        raise AssertionError(f"Height mismatch: expected {expected_height}, found {height}")

    if expected_fps is not None and abs(fps - expected_fps) > 0.5:
        raise AssertionError(f"FPS mismatch: expected {expected_fps}, found {fps:.2f}")

    if expected_duration is not None and abs(duration - expected_duration) > duration_tolerance:
        raise AssertionError(
            f"Duration mismatch: expected ~{expected_duration:.2f}s, found {duration:.2f}s "
            f"(tolerance +/- {duration_tolerance}s)"
        )

    return {
        "path": str(video_path),
        "codec": codec,
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "size_bytes": file_size,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate video file using ffprobe")
    parser.add_argument("video", type=Path, help="Path to video MP4 file")
    parser.add_argument("--width", type=int, help="Expected video width")
    parser.add_argument("--height", type=int, help="Expected video height")
    parser.add_argument("--fps", type=float, help="Expected video frame rate")
    parser.add_argument("--duration", type=float, help="Expected video duration in seconds")
    parser.add_argument("--tolerance", type=float, default=0.25, help="Allowed duration tolerance (seconds)")

    args = parser.parse_args()

    try:
        info = verify_video(
            video_path=args.video,
            expected_width=args.width,
            expected_height=args.height,
            expected_fps=args.fps,
            expected_duration=args.duration,
            duration_tolerance=args.tolerance,
        )
        print("✓ Video verification PASSED:")
        print(f"  File: {info['path']}")
        print(f"  Codec: {info['codec']}")
        print(f"  Dimensions: {info['width']}x{info['height']}")
        print(f"  FPS: {info['fps']:.2f}")
        print(f"  Duration: {info['duration']:.2f}s")
        print(f"  Size: {info['size_bytes'] / 1024:.1f} KB")
        sys.exit(0)
    except (AssertionError, FileNotFoundError, RuntimeError) as e:
        print(f"✗ Video verification FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
