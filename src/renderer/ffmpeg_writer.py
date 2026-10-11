"""FFmpeg video encoder interface using stdin rawvideo pipe."""

from pathlib import Path
import shutil
import subprocess
from typing import Optional
from PIL import Image


class FFmpegError(Exception):
    """Raised when FFmpeg encoding fails or FFmpeg is missing."""
    pass


class FFmpegWriter:
    """Streams raw RGB frames directly to FFmpeg process over stdin pipe."""

    def __init__(
        self,
        output_path: Path,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        codec: str = "libx264",
        crf: int = 20,
    ):
        self.output_path = Path(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec
        self.crf = crf
        self.process: Optional[subprocess.Popen] = None
        self.frames_written = 0

        # Ensure ffmpeg executable is found
        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            raise FFmpegError(
                "FFmpeg executable not found in system PATH. "
                "Please install FFmpeg (e.g. `brew install ffmpeg` or `apt install ffmpeg`)."
            )

        # Ensure parent output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Spawn the FFmpeg subprocess."""
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output without asking
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "rgb24",
            "-framerate", str(self.fps),
            "-i", "-",  # Read from stdin
            "-c:v", self.codec,
            "-crf", str(self.crf),
            "-preset", "medium",
            "-pix_fmt", "yuv420p",  # Wide hardware compatibility
            "-movflags", "+faststart",  # Web/player streaming optimization
            "-loglevel", "error",
            str(self.output_path),
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            raise FFmpegError(f"Failed to start FFmpeg process: {e}") from e

    def write_frame(self, image: Image.Image):
        """Write a single PIL Image frame to FFmpeg's stdin."""
        if not self.process or not self.process.stdin:
            raise FFmpegError("FFmpeg process is not running or stdin closed.")

        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))

        if image.mode != "RGB":
            image = image.convert("RGB")

        try:
            self.process.stdin.write(image.tobytes())
            self.frames_written += 1
        except Exception as e:
            _, stderr = self.process.communicate()
            err_msg = stderr.decode("utf-8", errors="replace") if stderr else str(e)
            raise FFmpegError(f"Failed writing frame to FFmpeg: {err_msg}") from e

    def write_frame_repeated(self, image: Image.Image, count: int):
        """Write the same frame count times efficiently."""
        if count <= 0:
            return
        if not self.process or not self.process.stdin:
            raise FFmpegError("FFmpeg process is not running or stdin closed.")

        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))
        if image.mode != "RGB":
            image = image.convert("RGB")

        frame_bytes = image.tobytes()
        for _ in range(count):
            try:
                self.process.stdin.write(frame_bytes)
                self.frames_written += 1
            except Exception as e:
                _, stderr = self.process.communicate()
                err_msg = stderr.decode("utf-8", errors="replace") if stderr else str(e)
                raise FFmpegError(f"Failed writing repeated frame to FFmpeg: {err_msg}") from e

    def close(self):
        """Finish streaming and wait for encoding to complete."""
        if not self.process:
            return

        stdout, stderr = self.process.communicate()
        return_code = self.process.returncode
        self.process = None

        if return_code != 0:
            err_msg = stderr.decode("utf-8", errors="replace") if stderr else f"Exit code {return_code}"
            raise FFmpegError(f"FFmpeg process failed with error: {err_msg}")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
