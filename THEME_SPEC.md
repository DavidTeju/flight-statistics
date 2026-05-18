# Flight Statistics — Theme Re-skin Spec

## 1. Aesthetic name + elevator pitch

**"Meadow Tarmac"** — a daylit, almost botanical take on aviation data. Where the current theme reads as a 3 a.m. arrivals board, this one reads as a printed almanac left open on a sunlit table: warm off-white paper, a confident moss-green as the anchor, and a single cut of vermilion that snaps the eye to the points that matter. It's playful but composed: no scan lines, no glow, no perforated boarding-pass theatrics — just careful typography, generous air, and color that does the storytelling.

The data arc (2019 baseline → 2020 crater → 2024 surpassing 2019) gets a green ramp tuned so the COVID floor reads as pale, drained almost-paper, and the recovery surge reads as ripe, saturated forest — a literal "things grew back" gradient.

---

## 2. Color palette

### Surfaces & ink

| Token           | Hex                      | Role                                                |
| --------------- | ------------------------ | --------------------------------------------------- |
| `--bg`          | `#F4F1E8`                | Page background — warm oat paper, never pure white  |
| `--bg-2`        | `#FBF9F2`                | Card / surface — one tick brighter than page        |
| `--bg-3`        | `#E9E4D2`                | Recessed wells, hover surface, calendar empty cells |
| `--rule`        | `rgba(46, 64, 43, 0.10)` | Hairline borders                                    |
| `--rule-strong` | `rgba(46, 64, 43, 0.28)` | Emphasized dividers, focused cell outline           |
| `--ink`         | `#1E2A1B`                | Primary text — almost-black with a green undertone  |
| `--ink-dim`     | `#5A6457`                | Secondary text, labels                              |
| `--ink-faint`   | `#9AA095`                | Faint metadata, axis ticks                          |

### Brand color (the centerpiece — light moss/sage green)

| Token            | Hex       | Role                                   |
| ---------------- | --------- | -------------------------------------- |
| `--green`        | `#7BA05B` | Primary accent — calm, plant-leaf moss |
| `--green-bright` | `#A8C97F` | Lighter sage for hover / highlight     |
| `--green-deep`   | `#3F5A36` | Pressed state, dense text on green     |

### Sharp accents (1–2, used sparingly to spike the green)

| Token         | Hex       | Role                                                                                                                      |
| ------------- | --------- | ------------------------------------------------------------------------------------------------------------------------- |
| `--vermilion` | `#E8553A` | THE accent — hero number, peaks, "now" markers. One job: snap the eye.                                                    |
| `--clay`      | `#D49B5C` | Secondary accent — a softer terracotta for tertiary detail (legend mid-step, axis emphasis). Optional, used like a comma. |

### Semantic

| Token            | Hex       | Role                                                                                        |
| ---------------- | --------- | ------------------------------------------------------------------------------------------- |
| `--amber`        | `#E8553A` | **Mapped to vermilion** so existing `--amber` references keep working as the primary accent |
| `--amber-bright` | `#F47A60` | Hover/peak of accent                                                                        |
| `--amber-dim`    | `#9C3622` | Pressed accent / accent on light bg                                                         |
| `--ember`        | `#D49B5C` | Mapped to `--clay` — the secondary accent                                                   |
| `--danger`       | `#B23A24` | Errors / true negative deltas — deeper, grounded red                                        |

### 7-step heatmap RAMP (replaces `colorScale.ts` RAMP array)

A perceptually monotonic green ramp, tuned so step 0 reads as drained / barely-there (COVID crater) and step 6 reads as ripe forest (peak 2024). Steps are chosen by L\* roughly evenly stepped from ~92 down to ~28, so 0 vs 6 is unmistakable even at thumbnail size.

```
0  #EDEBD8   pale lichen — empty / near-zero (April 2020)
1  #D6DDB6   sun-bleached sage
2  #B9C98F   young leaf
3  #97B468   meadow
4  #739A4B   moss
5  #4F7A35   deep moss
6  #2E5023   forest floor — peak summer 2024
```

This is a single-hue sequential scale (good colorblind safety, reads as one story), with the optional `--vermilion` available to overlay annotations (e.g., a ring around the lowest-ever cell, or the "first day above 2019" marker).

---

## 3. Typography

No Inter, no Roboto, no Space Grotesk, no system stack.

| Role            | Family                                                                                                              | Why                                                                                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Display         | **Reckless** (or Google fallback: **Instrument Serif**)                                                             | High-contrast modern serif with a slightly literary, almost-magazine feel. Real character in the italic.                                                                                                 |
| Body            | **Söhne** (or Google fallback: **DM Sans** weight 400 only — chosen for its slightly warm, less-engineered g and a) | Wait — DM Sans is too common. Use **Newsreader** at 16/1.55 for body. It's a variable serif with optical sizing, gives the "almanac" feel, and pairs cleanly with Instrument Serif.                      |
| Mono / numerals | **JetBrains Mono** — too common. Use **Geist Mono** — also trendy. Final pick: **Departure Mono**                   | A pixel-grid-flavored monospace with a touch of utility-flight-strip personality. For tabular numerals in the bar chart and tooltip. Fallback: **IBM Plex Mono** (already loaded, fine as a safety net). |

### Final stack

```
--display: 'Instrument Serif', 'Reckless', 'Fraunces', Georgia, serif;
--serif:   'Newsreader', 'Source Serif 4', Georgia, serif;
--mono:    'Departure Mono', 'IBM Plex Mono', ui-monospace, monospace;
```

### Google Fonts URL

```
https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500;6..72,600&display=swap
```

Departure Mono is hosted at https://departuremono.com — self-host the woff2.

### Usage rules

- Display: hero number, section titles, the big year labels. Italic Instrument Serif on the eyebrow for a tiny editorial wink.
- Body: all paragraph copy and tooltip prose in Newsreader at 16–17px, line-height 1.55.
- Mono: every number that needs to align (bar chart axis, tooltip passenger count, weekly totals, window-size pill).

---

## 4. Component visual language

**Hero number.** Instrument Serif at ~140px, `--ink` weight 400, with the digits in `--vermilion` and the "passengers" label small-caps in `--ink-dim` Departure Mono. No glow, no shadow — the size is the drama.

**Calendar heatmap cells.** 12px squares with 2px gutters, rounded 2px, filled from the green RAMP. No border on filled cells; empty cells get `--bg-3` fill. Hovered cell: 1px `--ink` outline, no scale transform. Selected cell: 1.5px `--vermilion` outline.

**Legend.** Horizontal strip of the 7 RAMP swatches, each 14×14 with hairline gaps, bookended by mono labels "fewer" / "more" in `--ink-faint`. Sits below the calendar, not floating.

**Weekly bar chart bars.** Bars filled in `--green` at 85% opacity with a 1px top cap in `--green-deep` for definition. The single highest bar in the visible window gets `--vermilion` fill — one bar, one accent, every frame. Baseline rule in `--rule-strong`. Y-axis ticks Departure Mono in `--ink-faint`.

**Tooltip.** Plain `--bg-2` card, 1px `--rule-strong` border, 12px radius, no perforations, no boarding-pass stub. Date in Newsreader italic, count in Departure Mono large, a one-line delta vs same-day-2019 in `--vermilion` (if positive surplus) or `--ink-dim` (if deficit). Soft shadow only: `0 12px 32px -16px rgba(46, 64, 43, 0.25)`.

**Header.** Left-aligned wordmark in Instrument Serif italic ("Flight Statistics") preceded by a 28×28 rounded mark — a miniature 5×5 calendar-heatmap grid sampling the green RAMP with one `--vermilion` cell at the center. A thin `--rule` underline runs the full width; the eyebrow date range sits in Departure Mono uppercase tracking 0.22em in `--green-deep`. The mark is also the favicon.

**Window-size pill toggle (7d / 14d / 20d).** A single rounded pill, `--bg-3` background, 1px `--rule` border, three segments with the active segment filled `--green` and text `--bg`. Inactive segments: `--ink-dim` Departure Mono. Sliding indicator transitions 220ms ease-out — the one bit of motion that earns its keep.

---

## 5. Motion / decoration

**Atmosphere.** One subtle decoration only: a faint paper-grain noise overlay at ~3% opacity on the body (SVG turbulence or a 256×256 noise PNG). NO gradients, NO vignettes, NO organic blobs. The warmth of `--bg` plus grain is the entire "texture story."

**Transitions.**

- Hover on cells / bars: 120ms ease-out opacity + outline. No scale, no translate.
- Pill toggle indicator: 220ms cubic-bezier(.2,.7,.2,1) on `transform`.
- Page-load: a single staggered reveal of calendar rows top-to-bottom, 40ms per row, 180ms duration, opacity + 4px translate-y. Done once, never repeats. Respects `prefers-reduced-motion`.

**No.** No glow, no parallax, no decorative SVG flourishes, no cursor effects, no scroll-triggered choreography.

---

## 6. What to remove (minimalism pass)

Cut these from the current implementation:

- The **scan-line** `repeating-linear-gradient` on body (the 2px/3px stripe pattern).
- Both **radial-gradient vignettes** at top and bottom of body.
- Any **amber glow** / box-shadow with amber tint (`rgba(255,176,0,...)` shadows).
- The **"boarding pass perforated stub"** in the tooltip — replace with a plain rounded card.
- **Major Mono Display** entirely — it's the single biggest source of the rejected aesthetic. Replace with Instrument Serif for display.
- The `--shadow-lg` heavy double-shadow — replace with a single soft green-tinted shadow.
- Any **departures-board flicker** or LED-style number animations.
- Decorative **dotted rules** or **dashed underlines** if present — use solid 1px hairlines only.
- Any **color-scheme: dark** declaration — switch to `light`.

---

## 7. CSS variables (copy-paste)

Drop this into `src/app.css` replacing the current `:root` block. Every existing variable name is preserved so components keep working unchanged.

```css
:root {
	/* "Meadow Tarmac" — light, botanical, one sharp accent */
	--bg: #f4f1e8; /* warm oat paper */
	--bg-2: #fbf9f2; /* card surface */
	--bg-3: #e9e4d2; /* recessed well / empty cells */

	--rule: rgba(46, 64, 43, 0.1);
	--rule-strong: rgba(46, 64, 43, 0.28);

	--ink: #1e2a1b; /* near-black, green undertone */
	--ink-dim: #5a6457;
	--ink-faint: #9aa095;

	/* Green centerpiece — referenced directly AND aliased onto legacy names */
	--green: #7ba05b;
	--green-bright: #a8c97f;
	--green-deep: #3f5a36;

	/* Sharp accents */
	--vermilion: #e8553a;
	--clay: #d49b5c;

	/* Legacy aliases — keep existing components working.
	   "amber" is now vermilion (the new primary accent),
	   "ember" is now clay (the secondary). */
	--amber: var(--vermilion);
	--amber-bright: #f47a60;
	--amber-dim: #9c3622;
	--ember: var(--clay);

	--danger: #b23a24;

	--shadow-lg: 0 18px 40px -22px rgba(46, 64, 43, 0.25), 0 6px 16px -10px rgba(46, 64, 43, 0.12);

	--display: 'Instrument Serif', 'Reckless', 'Fraunces', Georgia, serif;
	--serif: 'Newsreader', 'Source Serif 4', Georgia, serif;
	--mono: 'Departure Mono', 'IBM Plex Mono', ui-monospace, 'SFMono-Regular', monospace;

	color-scheme: light;
}
```

### Replacement `RAMP` for `src/lib/colorScale.ts`

```ts
export const RAMP = [
	'#EDEBD8', // 0 — pale lichen (COVID floor)
	'#D6DDB6', // 1
	'#B9C98F', // 2
	'#97B468', // 3
	'#739A4B', // 4
	'#4F7A35', // 5
	'#2E5023' // 6 — forest floor (2024 peaks)
] as const;
```

### Recommended body update (also for `app.css`)

```css
body {
	min-height: 100vh;
	background-color: var(--bg);
	/* one decoration only: faint paper grain at ~3% */
	background-image: url('/grain.png');
	background-repeat: repeat;
	background-size: 256px 256px;
}
```

(No vignettes, no scan lines, no radial gradients.)
