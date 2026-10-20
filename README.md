# Topic Video Engine

A local video-production engine with shared rendering infrastructure and topic-specific visual identities, targeting **9:16 vertical video (1080 × 1920)** for Instagram Reels and YouTube Shorts.

## Target Publishing Format
- **Orientation**: Vertical 9:16 (1080 × 1920)
- **Frame Rate**: Configurable, defaults to 30 fps
- **Platform Targets**: Instagram Reels & YouTube Shorts

## Visual Direction & Creative Briefs
Each video supports its own **creative brief** to define:
- Target visual mood, premise, target audience, and chosen art direction
- 5-stage short-form narrative cadence (Hook → Context → Development → Payoff → Exit)
- Single dominant focal points per scene
- Palette with semantic role mappings (Ink, Paper, Coral, Signal Yellow, Mint)
- Mobile safe-area constraints (avoiding Instagram & YouTube UI overlays)
- Optional subtle creator personal signature (~5% presence, understated aside or observation)
- Sound design cues, music licensing status, and audio mix notes
- Auditable evidence with source URLs, claims, and verification statuses
- Human review and approval status (`approved`, `pending_review`, `draft`, `rejected`)

> **Approval Requirement:** The engine enforces human approval (`approval.status == "approved"`) before final export. Use `--allow-unapproved` only during early preview drafting.
> **Review Checklist:** Review creative treatments against [`CREATIVE_REVIEW_CHECKLIST.md`](CREATIVE_REVIEW_CHECKLIST.md).

---

## Installation & Prerequisites

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg & ffprobe** installed and available in `PATH`:
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 2. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Render Sample Videos (9:16 Vertical)

#### 1. Developer Workflow Video
```bash
python src/renderer/render.py --spec prototypes/developer_workflow/sample.json
```
Output: `output/developer_workflow_demo.mp4` (1080 × 1920 @ 30fps)

#### 2. Editorial Data Story Video
```bash
python src/renderer/render.py --spec prototypes/editorial_data_story/sample.json
```
Output: `output/editorial_data_story_demo.mp4` (1080 × 1920 @ 30fps)

#### 3. Kinetic Editorial Investigation (Creative Direction Upgrade Showcase)
```bash
python src/renderer/render.py --spec prototypes/kinetic_editorial/sample.json
```
Output: `output/kinetic_editorial_demo.mp4` (1080 × 1920 @ 30fps)

---

### Creative Direction Review & Preview Tools

#### 1. Generate High-Resolution Contact Sheet
Review all scene hero frames, focal points, safe areas, and narrative progression in a single glance:
```bash
python src/renderer/render.py --spec prototypes/kinetic_editorial/sample.json --contact-sheet output/review_sheet.png
```

#### 2. Pre-flight Quality & UX Audit
Check contrast ratios (WCAG AA), safe area margins, focal points, and evidence verification without rendering:
```bash
python src/renderer/render.py --spec prototypes/kinetic_editorial/sample.json --audit
```

#### CLI Options
```bash
# Custom output path
python src/renderer/render.py --spec prototypes/kinetic_editorial/sample.json --output output/custom_vertical.mp4

# Provide external creative brief
python src/renderer/render.py --spec prototypes/kinetic_editorial/sample.json --brief path/to/brief.json

# Draft preview (allows unapproved briefs)
python src/renderer/render.py --spec prototypes/kinetic_editorial/sample.json --allow-unapproved

# Contact sheet preview
python src/renderer/render.py --spec prototypes/kinetic_editorial/sample.json --contact-sheet

# Pre-flight audit
python src/renderer/render.py --spec prototypes/kinetic_editorial/sample.json --audit
```

---

## Optional Narration Generation

Install the optional speech-generation dependency:

```bash
pip install -r requirements-narration.txt
```

Add a `narration` string to scenes in an **approved** content spec, then create a derived spec with narration audio and word-timed captions:

```bash
python -m src.renderer.narration path/to/approved-spec.json --voice en-US-AriaNeural
```

This writes `approved-spec.narrated.json` plus an adjacent audio-assets directory. The approved source file is not overwritten. Inspect the generated voice, caption timing, and audio assets, then render the derived spec normally. If speech exceeds a scene's approved duration, the helper stops and asks you to revise the script or approve a longer scene. Edge TTS requires network access and its availability/terms should be reviewed before production use.

---

## Testing & Verification

### 1. Run Unit & Integration Tests
```bash
python -m unittest discover -s tests -v
```

### 2. Validate Generated Video Files with ffprobe
Verify that generated vertical videos contain valid H.264 video streams, exact dimensions (1080 × 1920), 30 fps, and expected duration:
```bash
# Verify developer workflow video
python tests/validate_video.py output/developer_workflow_demo.mp4 --width 1080 --height 1920 --fps 30 --duration 13.0

# Verify editorial data story video
python tests/validate_video.py output/editorial_data_story_demo.mp4 --width 1080 --height 1920 --fps 30 --duration 13.0

# Verify kinetic editorial investigation video
python tests/validate_video.py output/kinetic_editorial_demo.mp4 --width 1080 --height 1920 --fps 30 --duration 16.5
```

---

## Schemas & Guidelines
- Content specification schema: [`config/schemas/content-spec.example.json`](config/schemas/content-spec.example.json)
- Creative brief schema: [`config/schemas/creative-brief.example.json`](config/schemas/creative-brief.example.json)
- Human review checklist: [`CREATIVE_REVIEW_CHECKLIST.md`](CREATIVE_REVIEW_CHECKLIST.md)

---

## Project Planning & Progress

- [Roadmap and milestones](ROADMAP.md)
- [Template registry and status](docs/TEMPLATES.md)
- [Production pipeline and quality gates](docs/PIPELINE.md)
- [Decisions and constraints log](docs/DECISIONS.md)

