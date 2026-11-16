# C3 Nov 2026 Summary Video (HyperFrames)

Your edited summary video with graphics and text added on top: an opening title, 17
dimension cards (the recommended keywords, timed to the voiceover), photo slots for the
footage still to come, and the MENDAKI logo at the end.

## Adding the HR photos

The black stretches in the edit (60.3–91.9 s and 99.2–101.5 s) now show photo slots,
with the presenter keyed in front of them. Replace each placeholder with a real
landscape photo **using the same file name**:

| File | Time | Dimension |
| --- | --- | --- |
| `assets/photos/photo-1.jpg` | 60.3–64.9 s | Reward & Recognition |
| `assets/photos/photo-2.jpg` | 64.9–70.0 s | Reward & Recognition |
| `assets/photos/photo-3.jpg` | 70.0–74.5 s | Well-Being |
| `assets/photos/photo-4.jpg` | 74.5–78.2 s | Safety |
| `assets/photos/photo-5.jpg` | 78.2–81.5 s | Safety |
| `assets/photos/photo-6.jpg` | 81.5–86.7 s | Performance Enablement |
| `assets/photos/photo-7.jpg` | 86.7–91.9 s | Performance Enablement |
| `assets/photos/photo-8.jpg` | 99.2–101.5 s | Agility & Innovation |

## Editing the cards

The keywords, the timings and which side each card sits on are in the table at the top of
`tools/build-cards.mjs`. After editing it, run `node tools/build-cards.mjs`. The card
design is in `tools/dimension.template.html`.

## Media

`assets/footage.mp4` and `assets/presenter-*.webm` are too large for git. Rebuild them
from the original edit:

    tools/prepare-media.sh "C3 Nov 2026 Summary Video.mp4"

Preview: `npx hyperframes preview`. Render: `npx hyperframes render`.
