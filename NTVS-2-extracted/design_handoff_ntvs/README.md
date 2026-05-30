# Handoff: NTVS — North Texas Volleyball Stats

## Overview

NTVS ("North Texas Volleyball Stats") is an independent stats hub for club volleyball
across the DFW metroplex (Denton to Plano). This handoff covers a set of **new features**
built as an interactive design prototype — they are **not yet in your existing project repo**
and need to be implemented there.

The product lets families, coaches, and recruiters:
- Browse and rank clubs, and compare programs head-to-head
- Follow tournament schedules and final results/brackets
- Scout coaches via verified coaching résumés
- Build/claim a coach profile (résumé builder with live preview)
- Leave **positive-only** endorsements for coaches
- (For club directors) approve coach verification requests

There are **10 distinct screens/routes** in the prototype.

---

## About the Design Files

The files in `prototype/` are a **design reference created in HTML + React (via in-browser Babel)**.
They are a prototype demonstrating the intended **look, layout, and behavior** — **not production
code to copy directly**.

Your task is to **recreate these designs inside your existing project's environment**, using its
established framework, component library, routing, state management, and styling conventions. The
prototype uses inline styles and a single global stylesheet purely for speed of prototyping — in the
real codebase you should translate these into whatever the project already uses (CSS modules,
Tailwind, styled-components, design-system components, etc.).

Because these are **new features being added to an existing repo**, lean on the existing app's
patterns wherever they exist (nav shell, page layout, buttons, cards, typography). Only introduce
new tokens/components where the design genuinely calls for something the repo doesn't have yet
(e.g. the radar chart, the bracket layout, the positive-only endorsement composer).

### How the prototype is structured (for reference only)
- `prototype/NTVS Prototype.html` — entry point; loads React 18 + Babel and the `proto/*.jsx` files.
- `prototype/styles.css` — all CSS tokens + component classes.
- `prototype/proto/`:
  - `store.jsx` — all mock data (clubs, coaches, tournaments, reviews, verification requests).
  - `ui.jsx` — shared primitives: Nav, Toast, VerifiedBadge, Stars, StarPicker, Bar, Sparkline, Radar, ClubMark, and the `NavCtx` router/store context.
  - `home.jsx` — Home page.
  - `clubs.jsx` — Clubs directory + Club profile.
  - `compare.jsx` — Compare (head-to-head).
  - `schedule.jsx` — Tournament schedule (list/calendar/map) + Results.
  - `coach.jsx` — Coach profile (tabbed) + Endorsements composer.
  - `editor.jsx` — Coach profile editor (stepper + live preview).
  - `director.jsx` — Club director verification dashboard.
  - `app.jsx` — Coaches directory + the App shell (client-side router + in-memory store).

---

## Fidelity

**High-fidelity (hi-fi).** Colors, typography, spacing, component states, and interactions are all
final and intentional. Recreate the UI pixel-accurately using your codebase's existing libraries and
patterns. Exact values are documented under **Design Tokens** below.

---

## Navigation & Routing

A single top nav (`ui.jsx → Nav`) persists across all screens. The prototype uses an in-memory
router (`route = { page, ...params }`) — in your app, map these to real routes.

| Nav label | Route key | Params | Screen |
|---|---|---|---|
| Home | `home` | — | Home / landing dashboard |
| Clubs | `clubs` | — | Clubs directory (table) |
| (drill-in) | `club` | `id` | Club profile |
| Compare | `compare` | — | Head-to-head comparison |
| Schedule | `schedule` | — | Tournament schedule |
| Results | `results` | `id` | Tournament results/bracket |
| Coaches | `coaches` | — | Coaches directory (grid) |
| (drill-in) | `coach` | `id` | Coach profile (tabbed) |
| "Claim profile" CTA | `editor` | — | Coach profile editor |
| "Director" button | `director` | — | Club director dashboard |

**Nav active-state grouping:** `clubs` highlights for `clubs`/`club`/`director`; `coaches` highlights
for `coaches`/`coach`/`editor`. `results` only for `results`.

**Nav layout:** 56px tall, `padding: 0 28px`, `gap: 28px`, bottom border `1px var(--border)`,
background `rgba(10,16,32,0.85)` with `backdrop-filter: blur(10px)`, `flex-shrink:0`.
Left→right: logo (`N` mark in an amber 28×28 rounded-6 square + "NTVS" + muted subtitle "North Texas
Volleyball Stats") · nav links · a 260px search field (placeholder "Search clubs, coaches,
tournaments…" with a `⌘K` hint, currently routes to `clubs` on click) · ghost "Director" button ·
amber "Claim profile" CTA.

**Page transition:** on navigation the scroll container plays `page-exit` (opacity→0,
translateY 6px, 120ms) then `page-enter` (`pageEnter` keyframe: opacity 0→1, translateY 8px→0, 260ms,
`cubic-bezier(.2,.7,.3,1)`), with a 130ms swap delay and a scroll-to-top. The outer `.app-scroll`
owns scrolling; inner `.page` just grows.

---

## Screens / Views

> Layout convention: most pages use `.page` = `padding: 32px 40px 56px`. Hero/profile pages override
> to `padding: 0` and pad their own sections (typically `56px` horizontal). Headers use a flex
> row with `justify-content: space-between; align-items: flex-end` — a left title block
> (a `.kicker` eyebrow + an `h1` at `font-size: 40px`) and right-aligned actions.

### 1. Home (`home.jsx → PHome`)
**Purpose:** Landing dashboard — orient the user and surface live activity, rankings, and featured content.

**Layout (top to bottom):**
1. **Hero** — `padding: 52px 56px 40px`, bottom border, with a subtle radial amber glow background
   (`radial-gradient(1100px 380px at 82% -10%, rgba(245,197,24,0.10), transparent 60%)`). Flex row,
   `gap: 56px`:
   - Left (`max-width: 680px`): kicker with a `● LIVE` (amber) label + "2025–26 Club Season · Week 14";
     `h1` at **68px**, `line-height: 0.95` — "Every set, every spike, *tracked across* **North Texas.**"
     ("tracked across" in `--muted`, "North Texas." in `--accent`). Sub-paragraph at 17px `--fg-2`,
     `max-width: 540px`. Two buttons: primary "Compare clubs →" (→ compare), default "Browse
     tournaments" (→ schedule).
   - Right: a 320px **live-scores card** (hoverable, clickable → `results` id `lsc`): "Live now" label +
     amber chip "Lone Star Classic", then 3 score rows (team / score – score / team), winner side bold
     and amber; footer "View full bracket →" in cyan.
2. **Stats strip** — 4-column grid, each cell `padding: 24px 28px` with right borders: label, big
   number (`stat-num`, 40px), sub-line. Values: Clubs tracked **84** (+6 this season) · Active teams
   **612** (12s through 18s) · Coach profiles **1,247** (418 verified) · Matches logged **9,302**
   (season-to-date).
3. **Body** — 2-col grid `1.7fr / 1fr`, `gap: 40px`, `padding: 36px 56px 56px`:
   - Left: **Power Rankings** (`h2` 26px + "18 Open · Week 14"). A card listing top 6 clubs; each row
     is a grid `32px 1fr auto 120px auto`: rank number (top 3 amber), club (color dot + name + tier
     pill + "city · N teams"), win% (mono), an animated `Bar` in club color, and a `Sparkline`.
     Rows are `row-hover`, clickable → club profile. Footer row "See full rankings (84 clubs) →" (cyan)
     → clubs.
   - Right column (`gap: 24px`): **Upcoming tournaments** (3 hoverable cards: mono date / name / "city,
     TX · N teams" → schedule) and **Featured coaches** (2 hoverable cards: gradient initials avatar /
     name + verified badge / club · role / "View") → coach profile.

### 2. Clubs directory (`clubs.jsx → PClubs`)
**Purpose:** Browse/sort/filter all clubs; pin clubs to compare.

**Layout:** Header ("Directory · 84 clubs" kicker, "North Texas clubs" h1) with a primary "Compare"
button (shows a small amber count chip when clubs are pinned) → compare.

**Controls row** (`gap: 12px`, wraps): a 300px search input (icon + "Search clubs or cities…");
a segmented tier filter (`All tiers / Tier 1 / Tier 2 / Tier 3`, styled as `nav-link` pills inside a
bordered container); right-aligned sort chips (`Rank / Win % / Teams`).

**Table** — a `.card` with `overflow:hidden`. Header row grid
`60px 1fr 90px 130px 90px 110px 120px` on `--bg-2` background. Data rows (same grid, `row-hover`,
clickable → club profile): rank (`#N`, top-3 amber), club (`ClubMark` + name + tier pill + "city,
TX"), win% (mono), `Sparkline` (form), teams (mono), medals ("🥇N 🥈N"), and a compare toggle chip
("+ Compare" / "✓ Pinned", amber when pinned; `e.stopPropagation()` so it doesn't navigate).
Empty state: centered "No clubs match "{q}".".

**Sorting:** rank asc / win desc / teams desc. **Filtering:** by tier + by name/city substring.

### 3. Club profile (`clubs.jsx → PClub`)
**Purpose:** Deep dive on one club.

**Layout:**
- **Header** (`padding: 28px 56px`, bottom border, background `linear-gradient(180deg, {clubColor}14, transparent)`):
  breadcrumb "Clubs / North Texas / {name}"; then a row with a 76px `ClubMark` (radius 16), title block
  (h1 40px + "TIER N" pill, then "📍 city, TX · Est. YYYY · N teams · 12s–18s"), and two buttons:
  "＋ Compare"/"✓ Pinned to compare" (toggles pin, turns amber when pinned) and "Follow" (toast).
  Below: a 5-stat row (`gap: 40px`): #rank (National rank) · win% (Win rate) · gold (Gold medals) ·
  commits (College commits) · coaches (Coaches), each `stat-num` 32px + label.
- **Body** — 2-col grid `1.7fr / 1fr`, `gap: 40px`, `padding: 32px 56px 56px`:
  - Left: **Teams · 2025–26** table (grid `1.4fr 1.6fr 0.9fr 0.7fr 1.2fr`: Team / Head coach (cyan +
    clickable → coach if matched) / Record (mono) / Finish (medal chip 🥇/🥈/🥉) / Division). Then
    **Performance trend** card — a paired bar chart of Win % by season (this club in club color vs
    region avg in `--surface-2`), 6 seasons '20–'25, bars use the `grow-bar` scaleY animation.
  - Right (`gap: 24px`): **About** card (prose), **Medal cabinet** card (Gold/Silver/Bronze each a
    label + `Bar` + count), **Recent commits** card (position chip + name + school rows).

### 4. Compare (`compare.jsx → PCompare`)
**Purpose:** Side-by-side head-to-head of up to 4 pinned clubs.

**Layout:** Header ("Comparison" kicker, "Club head-to-head" h1) + actions: "＋ Add club" (disabled at
4), "Reset" (clears pins), primary "Export PDF" (toast). The pinned set is shared app state (defaults
to `["tav","drv","trn"]`); max 4 (attempting a 5th fires a warn toast).

- **Add picker** (toggled): a card of club chips (color dot + name) for all unpinned clubs; clicking
  pins it.
- **Empty state** (no pins): centered card "No clubs pinned yet" + "＋ Add a club" / "Browse directory".
- **Populated:**
  - **Header cards row** — grid `220px repeat(N,1fr)`: first cell a "Pinned · N of 4" label, then one
    `pop-in` card per club (top border 3px in club color): `ClubMark`, an "✕" to unpin, name (→ profile),
    city, and two big stats (#rank in club color, win%).
  - **Comparison body** — 2-col grid `1.55fr / 1fr`:
    - Left: a metrics table. Each row grid `200px repeat(N,1fr)`; label cell on `--bg-2`. The
      **best** value per highlighted row is bolded, amber, and gets a tiny "BEST" chip. Rows: National
      rank, Win percentage, Active teams, Gold finishes, Silver/Bronze, Coaching staff, College commits,
      **Season fee** (lower is better — `dir = -1`), Home city. "Best" is suppressed when all picks tie.
    - Right: **Profile overlay** card — a custom **Radar/spider chart** (`ui.jsx → Radar`, 5 axes:
      Win % / Depth / Gold / Dev / Alumni) overlaying each club's normalized `vals` polygon in its
      color at 12% fill, plus a color-keyed legend.

### 5. Tournament schedule (`schedule.jsx → PSchedule`)
**Purpose:** Browse upcoming/past tournaments with 3 view modes + filters.

**Layout:** Header ("Spring 2026 · Region 9" kicker, "Tournament schedule" h1) + a segmented view
switch: **List / Calendar / Map**.

**Filter chips row:** "Open only", "March", "April", "Within 30mi" (toggle chips, amber when active),
a "Clear" link when any active, and a right-aligned "N tournaments · N teams" count.

- **List view** — grouped by month ("March 2026", "April 2026" with a divider). Each tournament is a
  hoverable card, grid `72px 1fr auto auto auto`: a date block (mono month + big day), name (+ amber
  "FEATURED" chip if `feat`, cyan "RESULTS IN" chip if `done`) + "📍 venue · city, TX", teams count,
  age range + division, and a status chip (Open=win/green, Filling=amber, Waitlist=loss/red) + "Results
  →"/"Details →". Featured cards get a 3px amber left border. Clicking a `done` event → results.
- **Calendar view** (`CalendarView`) — a March 2026 month grid (7 cols, Sun-first; Mar 1 2026 is a
  Sunday). Day cells with events get a `--surface-2` background + the event name; clicking a `done`
  event → results.
- **Map view** (`MapView`) — a schematic DFW map (460px tall, dotted grid background) with positioned
  pins per city (Allen, Plano, Dallas, Frisco, Arlington, Denton, Fort Worth), each a dot (amber if
  featured, cyan otherwise, with a soft glow ring) + a small label card (city + short name).
- Empty state when filters match nothing.

### 6. Tournament results (`schedule.jsx → PResults`)
**Purpose:** Final results for one tournament — podium, bracket, standings, scores, stat leaders.

**Layout:** Breadcrumb "Results / {name} 2026"; header ("Final · MO D · 18 Open" kicker, name h1) +
a segmented tab switch **Bracket / Standings / All scores**.

- **Podium** — 3-col grid of cards (top border in 🥇amber/🥈cyan/🥉muted): big medal emoji + team + city.
- **Bracket tab** — "Championship bracket": a horizontal flow (`gap: 48px`, scrollable) of rounds
  (Round of 16 → Quarterfinals → Semifinal → Champion). Each match is a 200px `MatchCell` card (two
  team rows, winner highlighted amber with a faint amber tint). The Champion column is a highlighted
  card (🏆, team, "6–0 on the weekend", mono "def. … 25–19, 25–22").
- **Standings tab** — a table (grid `40px 1fr 100px 100px`: # / Team / Pool / Overall), top-3 amber.
- **All scores tab** — a flat list of every match (team — score – score — team, winner bold/amber).
- **Statistical leaders** (always shown, below tabs) — 3 cards (Kills / Assists / Digs leaders), each
  ranked rows: rank (1st amber) + name + club + mono value.

### 7. Coaches directory (`app.jsx → PCoaches`)
**Purpose:** Browse coaches in a card grid; search + filter to verified.

**Layout:** Header ("Directory · 1,247 coaches" kicker, "Coaches" h1) + primary "Claim your profile"
→ editor. Controls: a 300px search ("Search coaches or clubs…") + a "✓ Verified only" toggle chip
(amber when on). A 3-col card grid; each card (hoverable, → coach profile): gradient initials avatar
(52px, radius 12) + name (+ verified badge) + role; a club row (color square + club name); and a
footer stat row (Wins / Win% / Commits) plus a right-aligned star rating + "rating · endorseCount".

### 8. Coach profile (`coach.jsx → PCoach`)
**Purpose:** Full coaching résumé with tabs + endorsements.

**Layout:** 2-col grid `300px / 1fr`, full height.
- **Left rail** (`--bg-2` background, right border, `padding: 36px 28px`): 96px gradient initials tile
  (radius 20); name (h1 28px); verified state (`VerifiedBadge` + "Verified coach" in cyan, OR
  "Unverified · pending club"); role + club (club name in club color, → club) + "city, TX". Buttons:
  primary "Contact" + "Follow" (both toast), then a ghost "This is me — edit profile" → editor. Then
  divider-separated sections: **Career totals** (Matches won / Win rate / College commits / Gold
  finishes / Seasons), **Certifications** (cyan ✓ list), **Specialties** (chips).
- **Body** (`padding: 28px 48px 56px`): a tab bar **Overview / Career / Teams / Endorsements · N**
  (active tab gets a 2px amber bottom border).
  - **Overview / Career** (share content): if verified, a cyan-left-border banner "Profile connected
    to {club}" + "Verified by club director · N linked programs". Then "Coaching career" + a vertical
    **timeline** (left rail line at x=7; each entry a dot in club color + a card: club (color dot +
    name) + role, right-aligned mono year + amber record, then a note).
  - **Teams** — a 3-col grid of small cards: team + medal emoji, club · year, mono record.
  - **Endorsements** — see below.

### 8b. Endorsements (`coach.jsx → Endorsements`) — **positive-only review system**
**Purpose:** Collect supportive, screened feedback for coaches (a deliberate, distinctive feature).

**Layout:** 2-col grid `1.5fr / 1fr`.
- **Left:** a summary card (big average rating in amber + 5 stars + "N endorsements"; "Most mentioned
  strengths" as cyan count chips). Then the list of endorsement cards: avatar + author ("Parent of an
  OH", etc.) + relationship/season; right-aligned stars + date; body text; tag chips. A newly posted
  endorsement animates in (`pop-in`) at the top.
- **Right (sticky):** "Leave an endorsement" composer card (cyan top border):
  - A cyan info banner: endorsements are **positive-only**; concerns go through the club director privately.
  - **Your rating** — `StarPicker`, **locked to a 4–5 minimum** (stars 1–3 are disabled/dimmed,
    `cursor: not-allowed`). Hover scales the star 1.15×. Label reads "Outstanding" (5) / "Excellent" (4).
  - **Your relationship** — chips: Parent / Player / Fellow coach / Club staff (amber when selected).
  - **What stood out?** — multi-select tag chips from `ENDORSE_TAGS` (selected get cyan style + "✓").
  - **Your endorsement** — a 500-char textarea. **Tone gate:** a regex
    (`/\b(bad|awful|terrible|hate|worst|rude|unfair)\b/i`) flags negative wording — the border turns
    red, the helper shows "⚠ Please keep it positive", and submit is dimmed/blocked (warn toast on try).
    Otherwise shows green "Positive tone detected" + a char counter.
  - Submit posts the endorsement to app state (prepended), resets the form, and fires a success toast.
  - Footer fine print: "Posts publicly under your name. Endorsements are screened to keep NTVS
    supportive for young athletes."

### 9. Coach profile editor (`editor.jsx → PEditor`)
**Purpose:** Build/claim a coaching résumé — a 5-step flow with a live preview.

**Layout:** Vertical flex.
- **Top bar** (`--bg-2`): "Editing your profile · Draft" kicker + "Build your coaching resume" h2;
  right side "Saved just now" + "Preview" (→ coach) + primary "Publish profile" (toast → coach).
- **Stepper** — 5 steps: **Basics / Link clubs / Career history / Credentials / Review**. Each step
  bullet is a 24px circle (done = cyan ✓, current = amber number, future = muted), connected by lines
  (cyan up to current). Steps are clickable. Prototype defaults to step 2 (Career history).
- **Body** — 2-col grid `1.25fr / 1fr`, full height:
  - **Left (form):** On **Career history** (step 2), a live résumé builder: existing positions render
    as cards (3px left border in club color; "✓ VERIFIED" cyan chip or "PENDING" amber chip; club /
    role / mono years; an "✕" to remove). An inline "+ New position" form (appears via "＋ Add another
    position") with fields **Club** (datalist of club names), **Role**, **Age group / team**, **Years**
    (mono). "Add position" validates club+role (else warn toast), appends an unverified entry, fires a
    toast. Below: a "Request club verification" callout card with a "Send request" button (toast). Other
    steps show a placeholder that routes back to Career history.
    Footer nav: "← Back" (disabled at step 0) / "Continue →" (or "Publish" on last step).
  - **Right (live preview, `--bg-2`):** "Live preview" / "How recruiters see it" chip. A mini coach
    card (60px gradient tile, name + verified badge, role line; a 4-stat row Wins/Win rate/Commits/
    **Verified count** which updates live; a "Career · N positions" timeline mirroring the form, pending
    entries at 0.75 opacity with a "● pending" marker). Below the card: a **Profile strength** meter
    (`Bar`) computed as `min(100, 40 + positions*14 + (step>=3 ? 10 : 0))`, with guidance text.

### 10. Club director dashboard (`director.jsx → PDirector`)
**Purpose:** Let a club director approve/deny coach verification requests.

**Layout:** Vertical flex.
- **Top bar** (`--bg-2`): a club tile ("TA" amber) + "Club Director · Texas Advantage" kicker +
  "Coaching staff & verification" h2; right side "Manage teams" + primary "＋ Invite coach" (both toast).
- **Body** — 2-col grid `1.7fr / 1fr`, `gap: 36px`:
  - **Left:** "Pending requests" + an amber "N awaiting review" chip. Each request is a card: initials
    tile (in request color), name + role + mono claim years + relative time; a **match strength** row
    ("✓ STRONG MATCH" win-chip or "◐ PARTIAL MATCH" amber-chip + a `Bar` + mono %); a note; and actions:
    primary "✓ Verify & link", "View records" (toast), and a right-aligned red ghost "Deny". On decide,
    the card dims (opacity 0.55), border turns green/red, shows "✓ Verified & linked" / "✕ Request
    denied", then is removed from the queue after ~650ms (with a toast). Empty state: "All caught up".
  - **Right (`gap: 24px`):** a 2×2 stat grid (Coaches **14** / Verified (live count) / Pending (live) /
    Match rate **96%**); a **Current staff** card (avatar + name + role + status; "Verified" shows the
    badge, others e.g. "Invite sent"); and a "How verification works" explainer card.

---

## Interactions & Behavior

- **Client-side routing** via `go(page, params)` with the exit→swap→enter transition (see Navigation).
- **Toasts** (`ui.jsx → ToastHost`): bottom-center, auto-dismiss after 2600ms, `toastIn` animation,
  two kinds — `ok` (green check) and `warn` (amber). Fired on follow/contact/export/publish/invite, and
  for validation failures.
- **Compare pinning** is global app state shared between Clubs directory, Club profile, and Compare.
  Toggling is idempotent; capacity is 4 (5th attempt → warn toast).
- **Endorsement tone gate** — see §8b. Live regex check drives border color, helper text, and submit
  enablement.
- **Star picker** — locked to a 4–5 minimum (positive-only), hover preview + scale.
- **Editor live preview** — verified count, position timeline, and profile-strength meter all update
  as the user edits.
- **Director decisions** — optimistic dim + colored border, then removal from queue after ~650ms.
- **Filters/sorts** are all client-side (substring match, tier, status, month, proximity flag).

### Animations (CSS, in `styles.css`)
- `pageEnter` — 260ms, `cubic-bezier(.2,.7,.3,1)`, opacity + translateY(8→0).
- `.app-scroll.page-exit` — opacity→0, translateY 6px, 120ms.
- `popIn` — 300ms, `cubic-bezier(.2,.8,.3,1)`, scale(.96)+translateY(4)→1 (used on newly added cards).
- `toastIn` — 250ms.
- `growBar` — 700ms scaleY from bottom (season bars).
- `Bar` component animates width from 0 → value over 700ms `cubic-bezier(.2,.7,.3,1)`.
- `.hoverable` — `translateY(-2px)` + shadow `0 10px 30px rgba(0,0,0,0.3)` on hover, 140ms.
- `.row-hover` — background → `--surface-2`, 120ms.
- `.btn` — `filter: brightness(1.12)` on hover, `scale(0.97)` on active.

---

## State Management

In the prototype, all state lives in the `App` component (`app.jsx`) and is passed via `NavCtx`:

| State | Shape | Notes |
|---|---|---|
| `route` | `{ page, ...params }` | Current screen. Map to your router. |
| `compare` | `string[]` (club ids) | Pinned clubs; default `["tav","drv","trn"]`; max 4. |
| `reviews` | `{ [coachId]: Review[] }` | Seeded from `SEED_REVIEWS`; `addReview` prepends. |
| `requests` | `Request[]` | Verification queue; seeded from `SEED_REQUESTS`; `resolveRequest` removes by id. |
| (local) editor `positions` | `Position[]` | Résumé entries; add/remove; drives preview + strength. |
| (local) results `tab`, schedule `view`/`filters`, coach `tab`, etc. | — | Per-screen UI state. |

**Store methods:** `go`, `setCompare`, `toggleCompare`, `reviewsFor`, `addReview`, `requests`,
`resolveRequest`, `toast`.

**Data fetching:** the prototype is fully mocked. In your app these become API calls — clubs, coaches,
tournaments/results, reviews, and verification requests are the obvious resources. The data shapes in
`store.jsx` are a good starting point for response schemas (see below).

### Data shapes (from `store.jsx`)
- **Club:** `{ id, name, city, tier(1–3), win(0–1), teams, gold, silver, bronze, color(hex), est, rank, commits, coaches, fee, vals[5](0–1 radar), about }`
- **Coach:** `{ id, name, init, verified, clubId, grad(css gradient), role, city, totals{wins,winRate,commits,gold,seasons}, certs[], specialties[], about, career[{yr,club,clubColor,role,rec,note}], teams[[team,yr,club,rec,medal]], rating, endorseCount }`
- **Review (endorsement):** `{ who, rel, body, tags[], when, stars }`
- **Tournament:** `{ id, d, mo, monthKey, name, venue, city, teams, ageLo, ageHi, div, status(Open|Filling|Waitlist), within(mi), feat?, done? }`
- **Verification request:** `{ id, name, init, color, role, claim, match(Strong|Partial), matchPct, note, when }`

---

## Design Tokens

All defined in `prototype/styles.css` under `:root`.

### Colors
| Token | Hex | Use |
|---|---|---|
| `--bg` | `#0a1020` | App background (deep navy) |
| `--bg-2` | `#0f1729` | Secondary surfaces / rails / table headers |
| `--surface` | `#131c33` | Cards |
| `--surface-2` | `#1a2440` | Chips, inset elements, empty bars |
| `--border` | `#25324f` | Default borders |
| `--border-soft` | `#1d2640` | Inner dividers / row separators |
| `--fg` | `#e9ecf5` | Primary text |
| `--fg-2` | `#c5cbdb` | Secondary text |
| `--muted` | `#7a849e` | Muted text / labels |
| `--muted-2` | `#586581` | Faintest text / placeholders |
| `--accent` | `#f5c518` | **Volleyball amber** — primary brand/action color |
| `--accent-2` | `#ffd84a` | Lighter amber |
| `--cyan` | `#5bb8ff` | Verification / links / secondary accent |
| `--win` | `#4ade80` | Positive/success (green) |
| `--loss` | `#f87171` | Negative/error (red) |
| `--neutral` | `#94a3b8` | Neutral gray |

Per-club accent colors (used for dots, bars, radar, gradients) live on each club object's `color`.

### Typography
| Token | Stack | Use |
|---|---|---|
| `--font-display` | **"Bricolage Grotesque"**, "Helvetica Neue", sans-serif | Headings, big numbers, logo, avatars |
| `--font-sans` | **"IBM Plex Sans"**, "Helvetica Neue", Arial, sans-serif | Body text |
| `--font-mono` | **"JetBrains Mono"**, ui-monospace, "SF Mono", Menlo, monospace | Stats, scores, dates, years (with `tnum`) |

Loaded from Google Fonts. Headings: weight 600, `letter-spacing: -0.025em`, `line-height: 1.05`.
Body: `letter-spacing: -0.005em`, antialiased. `.stat-num`: display font, 600, `letter-spacing: -0.03em`.
`.tabular` / `.mono` use tabular-nums. Common sizes: h1 **40px** (hero 68px, home stats 40px), h2
**22–26px**, h3 **16–18px**, body **13–14px**, labels **11px**.

### Spacing & radii
- Page padding: `32px 40px 56px` (hero/profile pages pad sections at ~56px horizontal).
- Card radius: **12px**. Buttons/inputs/search: **8px**. Chips: **999px** (pill). Avatars: 8–20px.
  Tier pills: 4px. Logo mark: 6px.
- Common gaps: 8 / 10 / 12 / 14 / 16 / 18 / 22 / 24 / 36 / 40 / 56.

### Components / classes (in `styles.css`)
- `.nav`, `.nav-logo`, `.nav-link(.active)`, `.nav-search`, `.nav-cta`
- `.btn`, `.btn-primary` (amber), `.btn-ghost`
- `.chip`, `.chip-amber`, `.chip-cyan`, `.chip-win`, `.chip-loss`
- `.card`, `.divider`, `.kicker`, `.label`, `.stat-num`
- `.tier`, `.tier-1` (amber), `.tier-2` (cyan), `.tier-3` (gray)
- `.placeholder` (dashed diagonal-hatch placeholder strip)
- Custom React primitives (in `ui.jsx`): `VerifiedBadge`, `Stars`, `StarPicker`, `Bar`, `Sparkline`,
  `Radar`, `ClubMark`. These are SVG/markup — reimplement with your charting/UI libraries as appropriate.

### Shadows
- Card hover: `0 10px 30px rgba(0,0,0,0.3)`
- Toast: `0 8px 30px rgba(0,0,0,0.4)`

---

## Assets

No raster image or icon-library assets are used. Everything is:
- **Fonts:** Bricolage Grotesque, IBM Plex Sans, JetBrains Mono (Google Fonts).
- **Icons:** small inline SVGs (search, check, link, person, etc.) drawn in the components.
- **Emoji:** used sparingly for medals (🥇🥈🥉🏆) and location/pins (📍). Replace with your icon set if
  the existing app avoids emoji.
- **Club marks / avatars:** generated from initials + a per-entity color or CSS gradient — no image files.

---

## Files (in this bundle)

```
design_handoff_ntvs/
  README.md                  ← this document
  screenshots/               ← reference captures of each screen
    01-home.png
    02-clubs-directory.png
    03-club-profile.png
    04-compare.png
    05-schedule.png
    06-results.png
    07-coaches-directory.png
    08-coach-profile.png
    09-coach-endorsements.png
    10-editor.png
    11-director.png
  prototype/
    NTVS Prototype.html      ← entry point (open in a browser to view the live prototype)
    styles.css               ← all tokens + component classes
    proto/
      store.jsx              ← mock data + shapes
      ui.jsx                 ← shared primitives + router/store context
      home.jsx               ← Home
      clubs.jsx              ← Clubs directory + Club profile
      compare.jsx            ← Compare (head-to-head + radar)
      schedule.jsx           ← Schedule (list/calendar/map) + Results (bracket/standings/scores)
      coach.jsx              ← Coach profile (tabbed) + Endorsements composer
      editor.jsx             ← Coach profile editor (stepper + live preview)
      director.jsx           ← Club director verification dashboard
      app.jsx                ← Coaches directory + App shell (router + store)
```

To view the prototype live, open `prototype/NTVS Prototype.html` in a browser (it loads React + Babel
from a CDN, so it needs an internet connection).
