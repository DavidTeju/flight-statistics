# Flight Statistics — TSA Passenger Volumes Explorer

## Vision

A focused, polished data-viz app for navigating ~7.4 years of daily TSA passenger volumes (2019-01-01 → present). Two views:

1. **Calendar heatmap** (default) — see seasonality, COVID, and recovery at a glance.
2. **Sliding-window weekly bar chart** — drill into trends, scroll horizontally through time.

## Decisions locked in

| Decision        | Choice                                             |
| --------------- | -------------------------------------------------- |
| Tech stack      | SvelteKit (Svelte 5, runes) + TypeScript           |
| Calendar layout | GitHub-contributions style, one row block per year |
| Color scale     | Absolute volume, sequential single-hue             |
| Code location   | `/root/Flight Statistics/` (alongside CSV)         |

## Data

- Source: `tsa_passenger_volumes.csv` in this folder
- 2,691 daily rows from 2019-01-01 through 2026-05-14
- Columns: `date` (ISO `YYYY-MM-DD`), `passenger_volume` (int)
- Loaded once at app start, parsed into a typed array and a `Map<iso, value>` for O(1) lookup
- A refresh script will re-scrape TSA on demand (curl-cffi Chrome impersonation already works — see chat history)

## Views

### Calendar view (route `/`)

- GitHub-contributions style heatmap: weeks are columns, days-of-week are rows (7 tall), one block per year
- Each year labeled on the left; month labels along the top of each block
- Cells colored by absolute passenger volume on a **quantile-based** 7-bin sequential scale (quantile, not linear — keeps COVID's outliers from crushing the rest)
- Hover → tooltip with: formatted date, day of week, exact passenger count, percentile/bin
- Click a cell → navigate to weekly view centered on that date
- **Legend** in bottom-right: gradient swatch with low → high values labeled
- Missing days (none currently, but defensive): outlined empty cell

### Weekly sliding window (route `/week?date=YYYY-MM-DD&size=N`)

- **Bar chart** (spaced bars, not a histogram — histograms are for distributions; this is a time series)
- X axis: dates as e.g. `Mon May 12`, year shown when window crosses a year boundary
- Y axis: passenger volume, formatted with commas at full scale, abbreviated (`2.4M`) on small screens
- Hover bar → tooltip with exact value + day of week
- **Window size selector**: 7 / 14 / 20 days
- **Responsive default**: < 768px → 7, 768–1280 → 14, ≥ 1280 → 20
- **Sliding window** controls:
  - Horizontal mouse-wheel / trackpad scroll
  - Click-and-drag
  - Arrow keys (← / →), Shift+arrow for single-day steps
  - Prev / Next buttons that advance by full window size
  - Date picker to jump to any date
- **URL state** for window size + center date → reload-safe, shareable
- Back button (or ESC) returns to calendar, preserving the originating date

### Cross-view interactions

- Date is the universal anchor; clicking anywhere with a date jumps to weekly view
- Keyboard: arrow keys move selection in calendar, Enter opens weekly view
- ESC always returns to calendar from weekly view

## Design / polish

- Dark mode by default with light-mode toggle (persisted in localStorage)
- Smooth-but-restrained transitions on view change; respect `prefers-reduced-motion`
- Type: Inter for UI, JetBrains Mono (or tabular nums) for numbers
- Apply `frontend-design` skill principles — distinctive, not generic-AI looking
- Color scale must be colorblind-safe (test viridis / cividis as alternatives if blue gradient fails)

## Nice-to-have (prioritized, post-MVP)

1. **Annotations layer** — COVID milestones, US holidays as markers on the calendar/chart
2. **YoY overlay** in weekly view — ghost bars showing same week from prior year(s)
3. **Stats sidebar** in weekly view — window avg, vs 2019 same week, all-time rank
4. **Calendar mode toggle** — switch absolute heatmap ↔ "vs 2019 same-day" diverging colors
5. **Refresh script** — re-scrape TSA, update CSV, show staleness banner in app
6. **Quick-stats footer** on calendar — highest day, lowest day, latest value, YTD total
7. **Compare mode** — pick two windows, view side-by-side or overlaid
8. **Export view as PNG**
9. **Touch / mobile pass** — gestures for sliding window on phones

## File structure (target)

```
Flight Statistics/
├── tsa_passenger_volumes.csv          (canonical data; symlinked into static/)
├── REQUIREMENTS.md                    (this file)
├── scripts/
│   └── refresh.ts                     (re-scrape TSA → CSV)
├── src/
│   ├── routes/
│   │   ├── +layout.svelte             (header, theme provider)
│   │   ├── +page.svelte               (calendar view)
│   │   ├── +page.ts                   (load CSV)
│   │   └── week/
│   │       ├── +page.svelte           (weekly view)
│   │       └── +page.ts               (parse query string)
│   ├── lib/
│   │   ├── data.ts                    (CSV parse + index)
│   │   ├── colorScale.ts              (quantile scale)
│   │   ├── format.ts                  (number/date formatters)
│   │   ├── components/
│   │   │   ├── CalendarHeatmap.svelte
│   │   │   ├── WeeklyChart.svelte
│   │   │   ├── Tooltip.svelte
│   │   │   ├── Legend.svelte
│   │   │   ├── WindowSizeControl.svelte
│   │   │   └── ThemeToggle.svelte
│   │   └── stores/theme.ts
│   └── app.css
├── static/
│   └── tsa_passenger_volumes.csv      (symlink to ../)
├── svelte.config.js
├── vite.config.ts
├── tsconfig.json
├── package.json
└── .gitignore
```

## Build order (to-do)

1. Scaffold SvelteKit + TS in this folder (without clobbering the CSV)
2. Wire `@davidteju/dev-config` for ESLint, Prettier, TSConfig, Vitest
3. Symlink CSV into `static/`
4. `lib/data.ts` — parse CSV at load, expose sorted array + `Map<iso, value>` index, min/max/quantiles
5. `lib/colorScale.ts` — 7-bin quantile sequential scale, returns CSS color
6. `CalendarHeatmap.svelte` — SVG grid, year blocks, hover state
7. `Tooltip.svelte`, `Legend.svelte`
8. Wire calendar → `/week?date=…` on click
9. `WeeklyChart.svelte` — spaced bar chart with axes, hover
10. `WindowSizeControl.svelte` — 7/14/20 toggle + responsive default
11. Sliding window controls — wheel / drag / arrows / prev-next
12. URL state sync (window size + center date)
13. Theme (dark/light) toggle + persistence
14. Polish pass — fonts, transitions, color scale fine-tuning, a11y
15. README with how-to-run + how-to-refresh
16. Nice-to-haves in priority order above

## Assumptions / open questions

- Local dev only for now; not planning deployment unless asked
- CSV is source of truth; not re-scraping at page load (refresh is explicit)
- Mouse + keyboard are primary; touch works but isn't a primary target
- "Sliding window" defaults to centered on selected date; tell me if you'd rather it start at that date
