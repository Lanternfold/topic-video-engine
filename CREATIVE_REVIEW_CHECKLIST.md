# Short-Form Video Creative Direction & Quality Review Checklist

This checklist operationalises the creative-direction principles for vertical short-form videos (Instagram Reels & YouTube Shorts) rendered by **Topic Video Engine**.

> **Purpose:** Use this checklist during the human-approval gate before final export. It ensures videos interrupt scrolling, communicate clearly on mobile screens, preserve credibility, and leave viewers with a memorable idea.

---

## 1. Opening Hook & Immediate Comprehension (0.0s – 1.5s)
- [ ] **First Frame Impact:** Does the opening frame establish an immediately understandable visual idea before the viewer scrolls past?
- [ ] **Single Focal Point:** Is there exactly one dominant visual element competing for attention?
- [ ] **Curiosity or Contradiction:** Does the hook present a compelling question, surprising contradiction, or tension rather than generic greeting or filler?
- [ ] **Text Budget:** Is the opening headline brief enough to be read and understood in under 1.5 seconds?

---

## 2. Visual Hierarchy & Composition
- [ ] **Hierarchy Stack:** Is there a clear distinction between the hook headline, supporting context, primary evidence, and annotations?
- [ ] **Progressive Reveal:** Does information unfold in a sequence that guides curiosity rather than dumping all facts simultaneously?
- [ ] **Absence of Clutter:** Are decorative animations, redundant badges, and competing secondary visuals stripped away?
- [ ] **Card & Canvas Breathing Room:** Does the composition have adequate margin to prevent visual claustrophobia on small mobile screens?

---

## 3. Mobile Readability & Safe-Area Constraints
- [ ] **Top Safe Area (≥ 120px):** Is all vital text placed below top platform overlays (account names, audio search pills, status bar)?
- [ ] **Bottom Safe Area (≥ 160px):** Is essential content and callouts positioned above caption text, audio tickers, and scrubbers?
- [ ] **Right Side Safe Area (≥ 72px):** Does text remain clear of like, comment, share, and remix platform button columns?
- [ ] **Font Contrast & Scale:** Are body sizes at least 22px and headlines at least 42px on the 1080 × 1920 canvas?

---

## 4. Contrast, Colour & Semantic Meaning
- [ ] **WCAG AA Contrast Ratio:** Does text-to-background contrast achieve at least 4.5:1 (3.0:1 for large display titles)?
- [ ] **Palette Discipline:** Is the foundation strictly anchored in dominant ink or paper, with at most one primary accent and a purposeful secondary accent?
- [ ] **Semantic Consistency:**
  - **Coral (`#FF5C35`):** Reserved for defects, contradictions, warnings, or reveals.
  - **Signal Yellow (`#FFD447`):** Reserved for key numbers, questions, or moments of discovery.
  - **Mint (`#65D6C4`):** Reserved for verified facts, test passes, or contrasting data categories.
- [ ] **Accessible Communication:** Is meaning communicated through text and shape in addition to colour (not relying on colour alone)?

---

## 5. Narrative Progression & Payoff (Hook → Context → Development → Payoff → Exit)
- [ ] **Hook:** Establishes the tension, contradiction, or core premise immediately.
- [ ] **Context:** Provides the minimum essential framing required to understand the problem.
- [ ] **Development:** Staging of audited evidence, technical logs, or comparative patterns.
- [ ] **Payoff:** Delivers the discovery, resolution, or explanation without artificial withholding.
- [ ] **Exit:** Concludes with an insightful takeaway or natural resolution rather than an abrupt cliffhanger.
- [ ] **Cadence & Pauses:** Are deliberate pauses inserted before major reveals to let critical information register?

---

## 6. Sound & Audio Design
- [ ] **Mute Independence:** Can a viewer follow and comprehend 100% of the core story with sound muted?
- [ ] **Audio Hierarchy:** Do narration, atmospheric sound design, and music beds have distinct frequency separation?
- [ ] **Licensing Verification:** Is background music verified as royalty-free or platform-native audio rather than unlicensed commercial audio?
- [ ] **Sound Effect Purpose:** Are sound cues reserved for meaningful transitions and reveals rather than fired on every frame?

---

## 7. Factual Credibility & Evidence Traceability
- [ ] **Auditable Sources:** Does every factual claim link to a verifiable URL, benchmark, or official documentation in the brief?
- [ ] **Verification Status:** Are all data points marked as `verified` (with any estimates or unverified items clearly flagged)?
- [ ] **No Exaggerated Hooks:** Does the story strictly substantiate every claim made in the opening hook?

---

## 8. Creator Personal Signature (~5% Presence)
- [ ] **Subtlety:** Does creator personality contribute a small recognizable fingerprint (~5%) without overwhelming the subject?
- [ ] **Tone Alignment:** Is the signature curious, observant, precise, and understated (or quietly funny)?
- [ ] **Not Forced:** Has the video avoided forced poetry, catchphrases, unrelated anecdotes, or rigid motifs?
- [ ] **Story First:** Does the story remain the hero of the video?

---

## 9. Technical & Stream Correctness
- [ ] **Resolution:** Exact 1080 × 1920 (9:16 vertical orientation).
- [ ] **Frame Rate:** Consistent 30 fps (or configured target) with zero dropped frames.
- [ ] **Codec:** Valid H.264 video stream playable on standard iOS and Android players.
- [ ] **Duration:** Total video runtime strictly matches the sum of scene durations (typically 15s to 60s).

---

## 10. Human Review & Approval Gate
- [ ] **Review Tooling:** Generated contact sheet reviewed:
  ```bash
  python src/renderer/render.py --spec <spec_path> --contact-sheet output/review_sheet.png
  ```
- [ ] **Automated Audit Run:** Pre-flight checks executed:
  ```bash
  python src/renderer/render.py --spec <spec_path> --audit
  ```
- [ ] **Approval Status Updated:** Set `approval.status = "approved"` in the creative brief with reviewer name and notes.
