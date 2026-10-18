# Decisions and Constraints Log

This file records decisions so future changes do not accidentally reopen settled questions. Revisit a decision when new evidence justifies it.

| Decision | Current choice | Rationale / boundary |
|---|---|---|
| First pilot | Skinwalker Ranch, titled “The Ranch That Attracted a Pentagon Investigation” | A focused Paranormal Case File pilot can test the storytelling and production workflow end to end |
| Initial production scope | One reviewed Reel before scaling | Validate quality and effort before investing in automation |
| Creative approval | Human approval required for every creative brief before production | Automation can recommend; it must not silently decide the creative direction |
| Idea input | Arbitrary ideas and rough look/feel in natural language | Template choice should assist the user, not constrain what they can submit |
| Language | Natural Hinglish where suitable | Match the intended audience without forcing Hinglish into every topic |
| Output | Vertical 1080 × 1920 at 30 fps | Initial target for Reels and Shorts |
| Template strategy | Shared rendering infrastructure with distinct template identities | Templates should differ in narrative grammar and actual visual/audio behavior, not only color |
| Evidence | Claim-level source traceability and explicit verification status | A source URL or a self-declared status alone is insufficient for precise factual claims |
| Infrastructure | Local-first and low-cost until measured needs justify hosting | Avoid recurring spend before render speed, workload, and workflow are understood |
| Publishing | Manual until the first Reel is published and reviewed | Avoid automating an unproven workflow |

## Explored, not selected

- n8n and similar workflow orchestration
- Hosted video tools such as InVideo or Canva as possible production aids
- A sub-90-minute production target
- Cloudflare Pages, VPS hosting, or other deployment choices
- A broader online portfolio and services website
- App generators that scaffold and deploy from a natural-language requirement

These are options discussed, not implementation commitments. Revisit them only when the immediate production workflow gives us a concrete requirement.

## Change discipline

When a decision changes, add the new choice and its rationale. Keep historical context when it helps explain the trade-off, but make the current choice unmistakable.
