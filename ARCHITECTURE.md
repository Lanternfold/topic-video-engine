# Architecture

## Pipeline
Content specification
  -> Topic art-direction profile
  -> Scene components
  -> Shared renderer
  -> Validation
  -> MP4 export

## Shared renderer responsibilities
- Canvas dimensions and frame rate
- Scene timing and transitions
- Narration and audio synchronisation
- Captions
- Encoding and export
- Output validation

## Topic-specific responsibilities
- Palette and typography
- Composition and pacing
- Scene layout and motion
- Chart, terminal and callout styling

## Initial scope
Build only what is required to render two contrasting prototypes.
No automatic publishing, cloud rendering or autonomous research pipeline.
