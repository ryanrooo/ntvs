# Feature Specification: Stitch-Matched Club Analytics Experience

**Feature Branch**: `002-stitch-club-analytics`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "I want to create the same exact web pages I exported from google stitch an ai webpage creater and I want to hook my postgres tables to what makes sense in all the screenshots and html code in the stitch_ntvs folder in the project root. I should be able to check club teams performance on saturday pool days, compare clubs, compare match histories of clubs if they faced off against eachother etc"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Tournament and Pool Results (Priority: P1)

A volleyball parent, coach, or club director opens the NTVS site and can move from the
homepage into Saturday pool-day results to see how teams performed by tournament,
division, age group, and pool.

**Why this priority**: This is the core value of the product because the current data
set already centers on tournaments, pools, standings, and match results, and this flow
turns that data into an immediately useful public experience.

**Independent Test**: Can be fully tested by opening the homepage, applying pool-result
filters, and confirming that pool standings and match summaries update to the selected
tournament context without needing rankings or club comparison features.

**Acceptance Scenarios**:

1. **Given** tournament data exists for a selected Saturday event, **When** a user opens
   the homepage and selects a tournament result view, **Then** the site shows the
   matching pool-day summaries and featured tournament content using real stored data.
2. **Given** multiple pools exist within a selected division, **When** a user filters by
   age group or division, **Then** only pools and standings that match the selected
   filters are shown.
3. **Given** pool standings exist for a selected pool, **When** the user opens that pool
   result section, **Then** the ranking order, match record, and point-difference style
   performance indicators are shown for each team in that pool.

---

### User Story 2 - Evaluate Club Performance and Profiles (Priority: P2)

A user can search for a club, view a club-focused profile, and understand how that club
has performed across available tournaments and teams in the current data set.

**Why this priority**: Club-level discovery is the second major value in the Stitch
exports and is the main bridge from team-by-team tournament data to broader regional
analysis.

**Independent Test**: Can be fully tested by searching for a known club and opening its
profile to confirm the site shows the club's participating teams, overall results, and
performance summaries derived from stored tournaments and matches.

**Acceptance Scenarios**:

1. **Given** multiple teams belong to the same club, **When** a user searches for that
   club, **Then** the site returns one club view that aggregates the club's teams rather
   than treating each team as an unrelated entity.
2. **Given** a club has participated in tournaments in the available data set, **When**
   a user opens the club profile, **Then** the site shows that club's participating
   teams, win-loss style summaries, and recent tournament performance indicators.
3. **Given** a user is reviewing clubs at a high level, **When** the user sorts or scans
   club ranking results, **Then** the list surfaces clubs using consistent, explainable
   regional performance metrics derived from stored match and tournament outcomes.

---

### User Story 3 - Compare Clubs Side by Side (Priority: P3)

A user can pick two clubs and compare them side by side using the same analytical
dimensions shown in the Stitch comparison design, including overall performance trends
and shared head-to-head history when those clubs have faced each other.

**Why this priority**: Comparison is a high-value analytical workflow for recruiting,
scouting, and club benchmarking, but it depends on the foundational tournament and club
views already being trustworthy.

**Independent Test**: Can be fully tested by selecting two clubs with existing results
and confirming that the comparison view shows side-by-side metrics plus shared match
history without requiring homepage navigation.

**Acceptance Scenarios**:

1. **Given** two clubs each have teams in the stored data, **When** a user selects both
   clubs for comparison, **Then** the site displays the two clubs in a side-by-side
   comparison view with equivalent metrics for both clubs.
2. **Given** teams from the selected clubs have played each other in stored matches,
   **When** the comparison view is opened, **Then** the site shows the shared matchup
   history and the results attributable to each club.
3. **Given** the selected clubs have no direct match history in the stored data, **When**
   the user opens the comparison view, **Then** the site still shows side-by-side club
   performance metrics and clearly indicates that no direct head-to-head history is
   available.

---

### User Story 4 - Preserve the Exported Page Experience (Priority: P4)

A user experiences the production pages as faithful recreations of the exported Stitch
homepage, Saturday pool results page, club rankings/profile page, and club comparison
page, while seeing real NTVS data in the areas that correspond to those designs.

**Why this priority**: The user explicitly wants the exported pages recreated as-is, but
this should follow the data-backed workflows rather than precede them.

**Independent Test**: Can be fully tested by reviewing the implemented pages against the
exported HTML and screenshots and confirming that each page's major sections, content
grouping, and primary callouts are represented with live data in the expected places.

**Acceptance Scenarios**:

1. **Given** the exported Stitch files exist in the repository, **When** a reviewer
   compares the implemented pages to those exports, **Then** each exported page has a
   corresponding production page with the same primary information hierarchy and user
   intent.
2. **Given** a design section in the export uses example values that are not present in
   the database, **When** the production page is rendered, **Then** that section is
   populated with the closest matching real NTVS data rather than fabricated sample
   values.

### Edge Cases

- What happens when a selected tournament has pools but is missing some match-result
  rows needed for full summaries?
- How does the system handle clubs whose teams appear under inconsistent team-name
  formatting but share the same club identifier logic?
- What happens when multiple source club names normalize to the same candidate club key?
- What happens when a user selects filters that return no tournaments, no pools, or no
  clubs?
- How does the system handle clubs that have tournament participation but no direct
  head-to-head history against the comparison target?
- What happens when a homepage feature section expects a highlighted or "live" result
  but only completed historical results are available?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide production pages corresponding to the exported
  homepage, Saturday pool results page, club rankings/profile page, and club comparison
  page found in `stitch_ntvs`.
- **FR-002**: The system MUST populate those pages with real NTVS tournament, pool,
  standings, team, and match data wherever a matching data concept exists in the
  current data set.
- **FR-003**: Users MUST be able to browse tournament and pool-day results by tournament
  context and narrow those results using filters such as age group and division when
  that information exists in the stored data.
- **FR-004**: The system MUST present pool standings in rank order and show each team's
  pool-day performance using consistent summary indicators derived from stored standing
  and match data.
- **FR-005**: Users MUST be able to search for and open a club-focused view that groups
  all relevant teams belonging to the same club.
- **FR-006**: The system MUST provide a club rankings or discovery view that orders clubs
  using a documented, repeatable performance model derived from available tournament and
  match outcomes.
- **FR-007**: The system MUST show a club profile summary with the club's participating
  teams, recent tournament activity, and aggregate performance indicators based on the
  stored data set.
- **FR-008**: Users MUST be able to select two clubs and view them side by side in a
  comparison experience that uses the same metric definitions for both clubs.
- **FR-009**: The system MUST display shared match history between selected clubs when
  teams from those clubs have faced each other in stored match results.
- **FR-010**: The system MUST clearly state when direct matchup history is unavailable
  rather than leaving comparison sections blank or implying missing data is a loss.
- **FR-011**: The system MUST provide meaningful empty, partial-data, and no-results
  states for homepage modules, pool result sections, club profiles, and club comparison
  views.
- **FR-012**: The system MUST use only real stored results and derived summaries in
  user-visible analytics, and MUST NOT invent tournament outcomes, club records, or
  matchup histories.
- **FR-013**: The system MUST make the ranking and comparison summaries internally
  consistent so the same underlying stored result contributes the same way across
  homepage callouts, club profiles, and comparison views.
- **FR-014**: The system MUST allow users to move from high-level discovery pages into
  deeper result or comparison views without re-entering the same club or tournament
  selection context.
- **FR-015**: The system MUST resolve club-key slug collisions deterministically when
  multiple source club names normalize to the same candidate key.
- **FR-016**: The system MUST preserve each original source club name even when a unique
  stable club key is generated to resolve a slug collision.
- **FR-017**: The system MUST ensure that collision handling produces unique, stable club
  identities that remain consistent across rankings, profiles, comparisons, and direct
  matchup history.
- **FR-018**: The system MUST keep club normalization and supporting migrations safe to
  rerun without causing unique-constraint failures or changing an already assigned club
  identity unless the underlying source club name changes.

### Key Entities *(include if feature involves data)*

- **Tournament**: A named event that organizes pool-day results and acts as the primary
  entry point for homepage highlights and Saturday results views.
- **Pool**: A tournament subdivision defined by division and pool name that groups
  standings and match activity for a specific Saturday results context.
- **Pool Standing**: A team's placement and performance summary within a pool, including
  ranking, win-loss totals, and point-difference style indicators.
- **Team**: A club-affiliated competitive entry that appears in pools, standings, and
  match results.
- **Club**: The parent organization inferred from grouped teams and used as the main
  analytical entity for rankings, profile summaries, and comparison.
- **Club Alias Mapping**: A stable mapping from each original source club name to a
  unique analytical club key and preferred display name, including collision-resolution
  status when multiple names would otherwise normalize to the same key.
- **Match Result**: A recorded contest between two teams that supports pool summaries,
  recent-form indicators, and club head-to-head history.
- **Club Comparison Summary**: A derived analytical view that aggregates each selected
  club's results and, when available, the direct matchup history between the two clubs.

## Assumptions

- The exported Stitch HTML, screenshots, and design document in `stitch_ntvs` are the
  visual and structural reference for the production pages.
- Existing NTVS tournament, team, pool, standings, and match tables are the initial
  source of truth for the first release of this feature.
- Club-level analytics can be derived by grouping teams under a shared club name from
  the stored team records.
- When multiple source club names would normalize to the same slug, the product will
  assign stable unique keys using a deterministic collision-resolution rule rather than
  merging those clubs silently.
- Homepage "live" or spotlight areas may use the most relevant available recent result
  when true live event data is not present in the current data set.
- Ranking and comparison metrics will be limited to what can be defensibly derived from
  the current stored results; sections requiring unavailable data will show a clear
  unavailable or partial-data state rather than placeholder fiction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can map 100% of the exported Stitch pages in `stitch_ntvs` to a
  corresponding production page with the same primary user purpose and major content
  sections.
- **SC-002**: Users can reach a relevant Saturday pool result view from the homepage and
  locate a selected pool's standings in under 3 interactions.
- **SC-003**: Users can search for a club and reach its profile summary in under 2
  minutes on first attempt.
- **SC-004**: Users can select two clubs and reach a side-by-side comparison view in
  under 4 interactions from the club discovery experience.
- **SC-005**: In validation using known sample tournaments and clubs from the stored data
  set, 100% of displayed win-loss, ranking-order, and head-to-head summaries match the
  underlying stored records.
- **SC-006**: When requested data is missing or unavailable, 100% of affected views show
  an explicit no-data or partial-data state instead of empty sections with no
  explanation.
- **SC-007**: In validation using known slug-collision cases, 100% of source club names
  are assigned unique stable club identities without migration failure or ambiguous
  merging in rankings, profiles, or comparisons.
