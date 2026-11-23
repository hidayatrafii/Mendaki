# MENDAKI MOU carousel design spec

Reference: MENDAKI x Ngee Ann Polytechnic MOU post (18 Nov 2026), slides in this folder (`slide1.jpg` to `slide5.jpg`).
Canvas: **4:5 portrait**, references are 1280x1600 (export 1080x1350 for Instagram). All measurements below are px on the 1280x1600 canvas.

## Colours

| Token | Hex | Use |
|---|---|---|
| Navy (background) | `#0E1D46` | Full-bleed background, every slide, no gradient or texture |
| Navy card | `#192A60` | Info boxes, stat cards, quote box |
| Yellow | `#F2CE46` (to `#F3CF45`) | Pills, second headline line, numbers, highlights, quote attribution |
| White | `#F8F8FA` / `#FFFFFF` | Headline line 1, body text |
| Muted blue-grey | `#ACB8E0` | Secondary description text inside stat cards |
| Black | `#000000` | Text inside yellow pills |

Two colours only, plus navy tints. No other accent colours.

## Fonts (files in `exports/assets/fonts/`)

| Role | Font | Weight / style |
|---|---|---|
| Headlines, big numbers, tagline, section caps | **Playfair Display** (`PlayfairDisplay-VF.ttf`) | Black 900. Numbers use its default old-style figures (the 3 and 5 drop below the line). Section label is ALL CAPS, Black, tracked about +5%. "MOU" on slide 2 is Black Italic. |
| Pill labels | **Outfit** (`Outfit-VF.ttf`) | Medium 400-500, black text |
| Body, card text, quote | **Questrial** (`Questrial-Regular.ttf`) | Regular. Lead paragraphs are tracked open (about +2.5px at 31px). Card labels are normal tracking. |
| Quote marks "66 / 99" | Thin handwritten script | Yellow, small, at top-left and bottom-right of the quote box |

## Recurring components

- **Yellow pill**: fully rounded (radius = half the height), height about 68, padding about 28 left/right, Outfit about 40px black. It sits top-left at x≈88 and acts as the kicker/date label. Used on slides 1, 2 (mid-slide), 3 and 4.
- **Two-tone headline**: Playfair Black about 160px, tight leading (about 1.05). Line 1 is white and line 2 is yellow, ending in a full stop ("Pathways, / together.", "Learning / by doing."). Left-aligned at x≈90.
- **Lead paragraph**: Questrial about 31px, white, centred, 3 lines max, line height about 1.45, open tracking.
- **Info bar (slide 2)**: navy card `#192A60`, full content width, centred Questrial text. Top and bottom edges bow slightly (a cushion shape).
- **Numbered list (slide 2)**: yellow Playfair numerals (1-4) in a left column at x≈180, each beside a navy-card bar (x 248-1145, height about 88, gap about 45) with centred Questrial text.
- **Stat cards (slide 3)**: 2x2 grid, cards about 535x400, radius about 30, gutter about 26. Inside: yellow Playfair number about 110px, white Questrial label about 30px, muted `#ACB8E0` description about 27px centred.
- **Quote box (slide 5)**: navy card with yellow script quote marks breaking out of the top-left and bottom-right corners. White quote text in Questrial about 30px, line height about 1.9, then the yellow attribution "Mr Name, Title, Organisation".

## Logo and margins

- Yayasan MENDAKI logo (white, with "Sentiasa Bersamamu") in the top-right corner at about x 1075-1235, y 40-150. It appears **on the cover only**.
- Side margin is about 88-90px. The content column is roughly x 88-1195.
- Plenty of empty navy at the top and bottom. Content is vertically balanced, not crammed.

## Slide-by-slide structure

1. **Cover.** Logo top-right, yellow pill "MOU Signing - [date]", two-tone headline, 3-line centred lead paragraph (who + what + why), then a wide group photo (x 82-1198, y 845-1472, **square corners**, about 16:9).
2. **What is an MOU?** Headline "What is an *MOU* ?" (MOU yellow italic), info bar with a plain-English definition, pill "MENDAKI x [Partner] MOU", a paragraph with the years highlighted in yellow, the caps label "FOUR KEY AREAS OF COLLABORATION", and a numbered list of 4 bars.
3. **Impact numbers.** Pill "Over 3 years", huge yellow headline number "3,000", white headline "youths and adults will benefit", then a 2x2 stat-card grid.
4. **Side activity.** Pill "[Activity] at [Partner]", two-tone headline, two side-by-side photos (about 535x580 each, radius about 25, gutter about 26), and a centred 3-line caption in Questrial.
5. **Quote / close.** Signatories photo (x 120-1160, y 295-880, square corners), quote box with attribution, and the Playfair Bold tagline "With You, Every Step Forward." bottom-right in white.

## Copy style

- Headlines: 2-3 words per line, punchy, ending in a full stop.
- Lead text: one sentence naming both organisations, the length of the MOU and its purpose.
- Use "&" in short list items, sentence case everywhere except the one caps section label.
- Name the partner in full once, then use its abbreviation, for example "Ngee Ann Polytechnic (NP)".

## Slips in the reference to avoid

- Faint leftover "ghost" text behind the pills on slides 3 and 4 ("Over three years", "Learning journey at NP").
- A typo, "educational athways".
- Double spaces ("to  explore", "Officer,  Yayasan").
- Inconsistent tracking within the quote (line 1 tracked, lines 2-3 not).
