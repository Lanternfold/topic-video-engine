# Production Pipeline

## Intended flow

1. **Idea inbox**: accept a topic, a rough idea, or a desired look/feel in natural language. Do not require the user to choose from a fixed template menu.
2. **Interpretation and research**: clarify the central question, audience, angle, and factual claims. Record source URLs and the exact passages or data that support claims.
3. **Creative planning**: recommend a suitable format and produce a creative brief with premise, hook, story beats, visual language, sound, pacing, and exit.
4. **Human approval**: pause for an explicit decision on the brief. Revisions return to planning. Rejected briefs do not proceed.
5. **Script and scene plan**: map the approved story to scenes, narration, captions, evidence, durations, and visual assets.
6. **Production adapters**: render scenes and assemble the timeline, motion, transitions, narration, music, and captions.
7. **Validation and preview**: run structural checks, evidence checks, visual audit, media probing, and contact-sheet or video review.
8. **Export**: produce the target vertical format and a reviewable artifact.
9. **Manual publication**: publish manually during the initial pilot phase.
10. **Performance feedback**: record reach, watch time/retention, shares, saves, comments, and qualitative lessons when available.

## Human approval gate

The creative planner may make recommendations, but creative production must not begin until the user approves the brief. Approval should be explicit and traceable in the spec or brief. Preview-only exceptions must remain clearly labeled and must not be mistaken for a production approval.

## Evidence gate

For every factual claim:

- Store the claim and its source URL.
- Record the exact source passage, timestamp, table, or dataset location when possible.
- Require an explicit verification status.
- Distinguish confirmed fact, attributed claim, disputed claim, and unresolved interpretation.
- Do not label a claim verified solely because the sample spec says so.
- Treat precise statistics and benchmark claims as high-risk until directly substantiated.

## Production and validation gaps to close

- Current renderer is known to render a still image per scene and hold it for the scene duration; this is not equivalent to implemented motion design.
- Motion, pacing, and transition fields must drive actual timeline behavior rather than act only as descriptive metadata.
- Narration, audio mix, caption timing, and scene timing need a shared timeline model.
- Safe-area constraints need to be applied consistently by rendering and audit code.
- Audit should run the relevant validation checks or clearly report which checks it omits.
- Final export should be validated with automated tests and media inspection, then reviewed at phone size.

## Initial output target

- Vertical 9:16, 1080 × 1920
- 30 fps target
- Instagram Reels and YouTube Shorts
- Natural Hinglish when appropriate to the idea and intended audience

## Operating constraints

- Start local and low-cost.
- Benchmark render speed and hands-on production time before choosing hosting or paid services.
- Keep publishing automation out of scope until the first Reel has been published and reviewed.
