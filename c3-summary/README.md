# C3 Nov 2026 Summary Video (HyperFrames)

Your edited summary video with graphics and text added on top: an opening title, 17
dimension cards (the recommended keywords, timed to the voiceover), photo slots for the
footage still to come, and the MENDAKI logo at the end.

## Photos

Where the original edit was black (60.3–91.9 s and 99.2–101.5 s), 18 HR photos play,
each timed to the narration line it illustrates, with the presenter keyed in front. They
are cropped to 16:9 around the people in `assets/photos/`; the list and timings are in
`tools/build-photos.mjs` (re-run it after editing).

## Editing the cards

The keywords, the timings and which side each card sits on are in the table at the top of
`tools/build-cards.mjs`. After editing it, run `node tools/build-cards.mjs`. The card
design is in `tools/dimension.template.html`.

## The presenter is never covered

`assets/character-track.json` records where the cartoon presenter stands in every camera
shot (found by face tracking). The keyword cards, the dark glow behind them and the
subtitles are all laid out in the free space beside him (`tools/presenter.mjs`); a card
that spans a cut where he moves switches side at the cut. If the edit changes, re-run the
tracking or correct the boxes in that file, then rebuild with `node tools/build-cards.mjs`
and `node tools/build-captions.mjs`.

## Sound

- `assets/voice.m4a`: the narration, separated from the original edit's music with Demucs.
- `assets/music/positive-background.m4a`: "Positive Background" by Soundrider/Dope (about
  118 BPM, upbeat corporate: piano, strings, light percussion), Creative Commons Attribution
  (CC BY), https://www.jamendo.com/track/1671032. Credited on the end card, as the licence
  requires.

## Media

`assets/footage.mp4` and `assets/presenter-*.webm` are too large for git. Rebuild them
from the original edit:

    tools/prepare-media.sh "C3 Nov 2026 Summary Video.mp4"

Preview: `npx hyperframes preview`. Render: `npx hyperframes render`.
