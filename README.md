# Topic Video Engine

A local video-production engine with shared rendering infrastructure and topic-specific visual identities, targeting **9:16 vertical video (1080 × 1920)** for Instagram Reels and YouTube Shorts.

## Target Publishing Format
- **Orientation**: Vertical 9:16 (1080 × 1920)
- **Frame Rate**: Configurable, defaults to 30 fps
- **Platform Targets**: Instagram Reels & YouTube Shorts

## Visual Direction & Creative Briefs
Each video supports its own **creative brief** to define:
- Target visual mood and art direction
- Scene cadence and pacing recommendations
- Transition style
- Optional palette and typography overrides on top of the base profile
- Sound design cues and background music recommendations
- Strategic rationale
- Auditable evidence (source URLs, retrieved timestamps, notes)
- Human review and approval status (`approved`, `pending_review`, `draft`, `rejected`)

> **Approval Requirement:** The engine enforces human approval (`approval.status == "approved"`) before final export. Use `--allow-unapproved` only during early preview drafting.

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

#### CLI Options
```bash
# Custom output path
python src/renderer/render.py --spec prototypes/developer_workflow/sample.json --output output/custom_vertical.mp4

# Provide external creative brief
python src/renderer/render.py --spec prototypes/developer_workflow/sample.json --brief path/to/brief.json

# Draft preview (allows unapproved briefs)
python src/renderer/render.py --spec prototypes/developer_workflow/sample.json --allow-unapproved
```

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
```

---

## Schemas
- Content specification schema: [`config/schemas/content-spec.example.json`](config/schemas/content-spec.example.json)
- Creative brief schema: [`config/schemas/creative-brief.example.json`](config/schemas/creative-brief.example.json)
