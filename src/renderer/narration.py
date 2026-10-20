"""Optional Edge TTS narration generation with word-timed scene captions.

Install the optional dependency with: pip install 'edge-tts>=7.0.0'
The core renderer does not require this package unless narration generation is used.
"""
import argparse
import asyncio
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple


TICKS_PER_SECOND = 10_000_000


def group_word_boundaries(
    words: List[Dict[str, Any]],
    max_words: int = 5,
    max_duration: float = 2.5,
) -> List[Dict[str, Any]]:
    """Group TTS word-boundary events into readable caption chunks."""
    if max_words < 1 or max_duration <= 0:
        raise ValueError("max_words and max_duration must be positive")
    captions: List[Dict[str, Any]] = []
    chunk: List[Dict[str, Any]] = []

    def flush() -> None:
        if not chunk:
            return
        start = max(0.0, chunk[0]["offset"] / TICKS_PER_SECOND)
        end = max(start, (chunk[-1]["offset"] + chunk[-1]["duration"]) / TICKS_PER_SECOND)
        text = " ".join(item["text"].strip() for item in chunk if item["text"].strip()).strip()
        text = re.sub(r"\\s+([,.;:!?])", r"\\1", text)
        if text and end > start:
            captions.append({"start": round(start, 3), "end": round(end, 3), "text": text})
        chunk.clear()

    for word in words:
        if not word.get("text") or word.get("duration", 0) <= 0:
            continue
        if chunk:
            chunk_start = chunk[0]["offset"] / TICKS_PER_SECOND
            proposed_end = (word["offset"] + word["duration"]) / TICKS_PER_SECOND
            current_text = " ".join(item["text"].strip() for item in chunk if item["text"].strip())
            if (
                len(chunk) >= max_words
                or proposed_end - chunk_start > max_duration
                or current_text.rstrip().endswith((".", "!", "?", ";", ":"))
            ):
                flush()
        chunk.append(word)
    flush()
    return captions


async def synthesize_scene(text: str, voice: str, output_path: Path) -> Tuple[List[Dict[str, Any]], float]:
    """Synthesize one scene and return word-timed caption chunks and speech end time."""
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("Narration requires the optional dependency: pip install 'edge-tts>=7.0.0'") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicator = edge_tts.Communicate(text, voice)
    words: List[Dict[str, Any]] = []
    speech_end = 0.0
    with output_path.open("wb") as audio_file:
        async for event in communicator.stream():
            if event["type"] == "audio":
                audio_file.write(event["data"])
            elif event["type"] == "WordBoundary":
                data = event["data"]
                item = {
                    "text": data.get("text", ""),
                    "offset": int(data.get("offset", 0)),
                    "duration": int(data.get("duration", 0)),
                }
                words.append(item)
                speech_end = max(speech_end, (item["offset"] + item["duration"]) / TICKS_PER_SECOND)
    if not words or not output_path.stat().st_size:
        raise RuntimeError(f"TTS returned no speech audio or word timings for {output_path.name}")
    return group_word_boundaries(words), speech_end


async def prepare_narrated_spec(
    spec_path: Path,
    output_spec_path: Path,
    voice: str,
    max_words: int = 5,
) -> Path:
    """Create audio assets and a derived spec; never overwrite the approved source spec."""
    spec_path = spec_path.resolve()
    output_spec_path = output_spec_path.resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    scenes = spec.get("scenes", [])
    output_spec_path.parent.mkdir(parents=True, exist_ok=True)
    asset_dir = output_spec_path.parent / f"{output_spec_path.stem}_audio"
    tracks: List[Dict[str, Any]] = []
    timeline_cursor = 0.0

    for index, scene in enumerate(scenes):
        script = scene.get("narration")
        if not isinstance(script, str) or not script.strip():
            timeline_cursor += float(scene["duration"])
            continue

        audio_path = asset_dir / f"scene_{index + 1:03d}.mp3"
        captions, speech_end = await synthesize_scene(script.strip(), voice, audio_path)
        scene_duration = float(scene["duration"])
        if speech_end > scene_duration:
            audio_path.unlink(missing_ok=True)
            raise ValueError(
                f"Scene {index + 1} narration lasts {speech_end:.2f}s but its approved "
                f"duration is {scene_duration:.2f}s. Revise the script or approve a longer scene, "
                "then rerun narration generation."
            )
        if "captions" in scene:
            raise ValueError(
                f"Scene {index + 1} already has captions. Remove or revise them in the source spec "
                "before generating word-aligned captions."
            )
        scene["captions"] = captions
        relative_audio = Path(
            Path(output_spec_path.parent).name,
            asset_dir.name,
            audio_path.name,
        )
        # Keep paths relative to the derived spec, including when its parent is the repo root.
        relative_audio = Path(asset_dir.name, audio_path.name)
        tracks.append({
            "source": relative_audio.as_posix(),
            "start": round(timeline_cursor, 3),
            "gain": 1.0,
            "duration": round(speech_end, 3),
        })
        timeline_cursor += scene_duration

    if not tracks:
        raise ValueError("No scene contains a non-empty 'narration' script")
    audio_cfg = spec.setdefault("audio", {})
    if not isinstance(audio_cfg, dict):
        raise ValueError("Top-level 'audio' must be an object")
    existing_tracks = audio_cfg.get("tracks", [])
    if existing_tracks:
        raise ValueError(
            "Source spec already has audio tracks. Combine tracks intentionally rather than "
            "silently replacing them."
        )
    audio_cfg["tracks"] = tracks
    output_spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    return output_spec_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate narration and word-aligned captions from a content spec.")
    parser.add_argument("spec", type=Path, help="Approved source content spec JSON")
    parser.add_argument("--voice", default="en-US-AriaNeural", help="Edge TTS voice name")
    parser.add_argument("--output", type=Path, help="Derived spec path (source spec is never overwritten)")
    parser.add_argument("--max-words", type=int, default=5, help="Maximum words per caption chunk")
    args = parser.parse_args()
    output = args.output or args.spec.with_name(f"{args.spec.stem}.narrated.json")
    try:
        result = asyncio.run(prepare_narrated_spec(args.spec, output, args.voice, args.max_words))
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(f"Generated narration spec: {result}")
    print("Next: inspect the generated captions and render the derived spec for review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
