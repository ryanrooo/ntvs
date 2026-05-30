# Feature Specification: NTVS Coach & Club Hub (NTVS-2 Handoff)

**Feature Branch**: `003-ntvs-coach-club-hub`
**Created**: 2026-05-29
**Status**: Draft
**Input**: User description: "Add NTVS coach profiles with verified coaching resumes, positive-only coach endorsements, and a club-director verification workflow, plus enhanced club comparison (up to 4 clubs with radar), tournament schedule (list/calendar/map) and tournament results/brackets, recreating the NTVS-2 design handoff in the existing app"

## Overview

NTVS is an independent stats hub for club volleyball across the DFW metroplex. This feature adds a
**coach scouting and verification layer** on top of the existing club/tournament analytics, plus
upgrades to club comparison and tournament browsing. The audience is volleyball **families,
coaches, recruiters, and club directors**. The work recreates a hi-fi design handoff (10 screens)
as new capabilities in the existing NTVS application.

## Clarifications

### Session 2026-05-29

- Q: Where do coach career totals (wins, win rate, commits) and the club-profile "head coach" link
  come from? → A: Seeded/stored on the coach — standalone fields, not derived from canonical match
  data; coaches link to a club but not to specific team match records.
- Q: How should the handoff's amber/navy hi-fi visuals reconcile with the existing cyan/black design
  system? → A: Re-theme the whole app to the handoff's amber/navy tokens (apply to existing pages too)
  as a single design system.
- Q: With authentication out of scope, how open are the write actions (endorsement, claim profile,
  director approval)? → A: Fully open (demo) — anyone can perform them; rely only on positive-only
  screening and idempotency. No gating/rate-limiting in this feature.
- Q: Is the Compare view's "Export PDF" action in scope? → A: Out of scope — omit it from this feature.
- Q: What is the deployment target for this feature? → A: Public production from day one
  (internet-facing, untrusted users).
- Q: Given a public-production target, what write-access posture should ship? → A: Gating ON by default
  in production — per-client rate limit + honeypot on endorsement/position submissions and a shared
  director token on verification resolve; configurable OFF for local/demo. This **supersedes the earlier
  "fully open (demo)" posture** for production environments.
- Q: How should platform hardening be scoped? → A: Critical subset in this feature (write-path safety +
  shim removal + app workers/healthcheck); migration runner, dependency upgrade, TLS/Adminer/log
  durability, and DB backups are tracked as a separate hardening backlog.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scout coaches via verified résumés (Priority: P1)

A recruiter or parent wants to evaluate coaches across North Texas clubs. They browse a directory of
coaches, filter to verified coaches only, search by coach or club name, and open a coach profile to
read a full coaching résumé: career history (clubs, roles, years, records), teams coached, career
totals, certifications, and specialties — with a clear "verified" indicator when a club director has
confirmed the coach's affiliation.

**Why this priority**: This is the headline new capability of the handoff and the single largest gap
versus the existing app (which has no coach data at all). It delivers standalone value to families
and recruiters even if nothing else in the feature ships, using seeded/imported coach data.

**Independent Test**: Load the coaches directory with seeded coaches, search and filter, open a
profile, and confirm the résumé sections and verification badge render correctly from stored data.

**Acceptance Scenarios**:

1. **Given** seeded coaches exist, **When** a visitor opens the coaches directory, **Then** they see
   a grid of coach cards each showing name, role, club, verification badge (if verified), and summary
   stats (wins, win %, commits, rating, endorsement count).
2. **Given** the directory is open, **When** the visitor types part of a coach or club name, **Then**
   the list narrows to matching coaches and shows an empty state if nothing matches.
3. **Given** the directory is open, **When** the visitor enables "Verified only", **Then** only
   verified coaches remain.
4. **Given** a coach profile, **When** the visitor opens it, **Then** they see the coach's identity,
   verification state, career totals, certifications, specialties, a career timeline, teams coached,
   and an endorsements tab with a count.
5. **Given** a coach is linked to a club, **When** the visitor clicks the club name on the profile,
   **Then** they navigate to that club's existing profile page.

---

### User Story 2 - Leave a positive-only endorsement for a coach (Priority: P2)

A parent, player, fellow coach, or club staff member wants to publicly endorse a coach. They open the
endorsements area of a coach profile and submit a supportive endorsement: a star rating (restricted to
a positive 4–5 range), their relationship to the coach, selected "what stood out" tags, and a short
written note. The system screens the note for negative wording and blocks submission of clearly
negative content, keeping the space supportive for young athletes. Posted endorsements appear
immediately in the coach's endorsement list and update the coach's average rating and strength tags.

**Why this priority**: The positive-only endorsement system is the distinctive, differentiating
feature of the product and drives engagement, but it depends on coach profiles (US1) existing first.

**Independent Test**: On a seeded coach profile, submit a valid positive endorsement and confirm it
appears at the top of the list and updates the summary; attempt a negative-worded note and confirm it
is blocked with guidance.

**Acceptance Scenarios**:

1. **Given** the endorsement composer, **When** a user selects a rating, **Then** only 4 and 5 stars
   are selectable and 1–3 are visibly disabled.
2. **Given** the composer, **When** the note contains flagged negative wording, **Then** the field is
   marked invalid, a "keep it positive" message appears, and submission is blocked.
3. **Given** a valid positive note, relationship, and rating, **When** the user submits, **Then** the
   endorsement is persisted and prepended to the list, and the coach's average rating, endorsement
   count, and "most mentioned strengths" update accordingly.
4. **Given** an endorsement is submitted, **When** the user views the list, **Then** the new entry
   shows the author label, relationship/season, rating, date, body text, and selected tags.
5. **Given** the composer, **When** the note exceeds the character limit, **Then** the user is
   prevented from exceeding it and sees remaining-character feedback.

---

### User Story 3 - Claim and build a coaching résumé (Priority: P2)

A coach wants to create or claim their own profile. They use a guided résumé builder to add coaching
positions (club, role, age group/team, years), review a live preview of how recruiters will see the
profile, and submit a request to a club director to verify each claimed position. Newly added
positions appear as "pending" until a director approves them; the live preview reflects verified vs.
pending counts and an overall profile-strength indicator.

**Why this priority**: Self-service profile creation grows the coach dataset and feeds the
verification workflow (US4). It is valuable but secondary to read-only scouting (US1) and the
endorsement experience (US2).

**Independent Test**: Open the editor, add a position, see it appear as pending in the live preview
with profile strength increasing, and submit a verification request that lands in the director queue.

**Acceptance Scenarios**:

1. **Given** the résumé editor, **When** the coach adds a position with at least a club and role,
   **Then** the position is saved as unverified/pending and appears in both the form and live preview.
2. **Given** a position is missing a club or role, **When** the coach tries to add it, **Then** they
   are warned and the position is not added.
3. **Given** positions exist, **When** the coach views the live preview, **Then** the preview shows a
   mirrored career timeline, a live verified-position count, and a profile-strength indicator that
   increases as more positions and steps are completed.
4. **Given** an unverified position, **When** the coach requests verification, **Then** a verification
   request is created for the relevant club's director and the coach is notified it was sent.

---

### User Story 4 - Approve or deny coach verification (club director) (Priority: P2)

A club director needs to confirm which coaches are genuinely affiliated with their club. They open a
verification dashboard showing pending requests, each with the coach's name, claimed role and years, a
match-strength indicator comparing the claim against club records, and a note. The director approves
("verify & link") or denies each request. Approved coaches become verified and linked to the club;
the queue and verification counts update immediately.

**Why this priority**: Verification is what makes "verified coach" trustworthy and is the counterpart
to US3. It is gated by coach profiles and claimed positions existing.

**Independent Test**: With seeded pending requests, approve one and confirm the coach becomes verified
and linked and the request leaves the queue; deny another and confirm it is removed without linking.

**Acceptance Scenarios**:

1. **Given** pending requests exist, **When** the director opens the dashboard, **Then** each request
   shows coach name, role, claimed years, match-strength indicator and percentage, a note, and
   approve/deny actions.
2. **Given** a pending request, **When** the director approves it, **Then** the associated coach
   position becomes verified and linked to the club, the request is removed from the queue, and
   verified/pending counts update.
3. **Given** a pending request, **When** the director denies it, **Then** the request is removed from
   the queue without changing the coach's verification, and the coach's claim is recorded as denied.
4. **Given** no pending requests remain, **When** the director views the queue, **Then** an
   "all caught up" empty state is shown.

---

### User Story 5 - Compare up to four clubs head-to-head (Priority: P3)

A family deciding between programs pins clubs from the directory or a club profile and compares up to
four of them side by side: a metrics table (rank, win %, teams, medals, coaching staff, commits,
season fee, home city) that highlights the best value per metric, plus a radar/spider chart overlaying
each club's profile across five dimensions. Pins are shared across the directory, club profiles, and
the comparison view.

**Why this priority**: Enhances an existing 2-club comparison into a richer multi-club tool. Valuable
but an upgrade of existing functionality rather than a net-new capability.

**Independent Test**: Pin three clubs from the directory, open compare, confirm all three appear with
the metrics table highlighting best values and a radar chart overlaying all three; add a fourth and
confirm a fifth is refused.

**Acceptance Scenarios**:

1. **Given** the clubs directory, **When** a user pins a club, **Then** the pin is reflected wherever
   the pinned set is shown (directory, club profile, compare) and a pinned count is visible.
2. **Given** fewer than four pinned clubs, **When** the user pins another, **Then** it is added; at
   four pinned, **When** they attempt a fifth, **Then** it is refused with a clear message.
3. **Given** two or more pinned clubs, **When** the user opens compare, **Then** a metrics table shows
   each club's values and marks the best value per applicable metric (including "lower is better" for
   season fee), suppressing the "best" marker when all values tie.
4. **Given** pinned clubs, **When** the comparison renders, **Then** a radar chart overlays each
   club's normalized profile across the five defined dimensions with a color-keyed legend.
5. **Given** no pinned clubs, **When** the user opens compare, **Then** an empty state invites them to
   add clubs.

---

### User Story 6 - Browse the tournament schedule (Priority: P3)

A family or coach wants to find upcoming and past tournaments. They browse a schedule in three view
modes — list (grouped by month), calendar (month grid), and map (schematic DFW map with city pins) —
and filter by open registration, month, and proximity. Each tournament shows date, name, venue, city,
team count, age range, division, and registration status; completed tournaments link to results.

**Why this priority**: Improves discovery of tournaments and complements existing pool results, but is
an enhancement layered on tournament data the app already ingests.

**Independent Test**: Open the schedule, switch between list/calendar/map, apply a month and an
"open only" filter, and confirm the tournament set and counts update; click a completed tournament and
land on its results.

**Acceptance Scenarios**:

1. **Given** scheduled tournaments, **When** the user opens the schedule, **Then** the list view groups
   tournaments by month with date, name, venue, city, teams, age range, division, and a status chip.
2. **Given** the schedule, **When** the user toggles a filter (open only / month / proximity), **Then**
   the visible tournaments and the "N tournaments · N teams" count update, with a clear-all option.
3. **Given** the schedule, **When** the user switches view mode, **Then** the same filtered set is
   rendered as a calendar month grid or as positioned city pins on a map.
4. **Given** a completed tournament, **When** the user selects it, **Then** they navigate to that
   tournament's results.
5. **Given** filters match nothing, **When** applied, **Then** an empty state is shown.

---

### User Story 7 - View tournament results and brackets (Priority: P3)

After a tournament, a user wants final outcomes. They open a results page showing a medal podium, a
championship bracket, final standings, all match scores, and statistical leaders (kills/assists/digs),
switchable between bracket / standings / all-scores views, with winners clearly highlighted.

**Why this priority**: The app already stores bracket and placement data, so this surfaces existing
data in a richer form. Valuable but dependent on completed-tournament data.

**Independent Test**: Open results for a completed tournament with bracket data and confirm the
podium, bracket rounds with highlighted winners, standings table, all-scores list, and stat leaders
render from stored data.

**Acceptance Scenarios**:

1. **Given** a completed tournament, **When** the user opens results, **Then** a three-place podium
   shows the top finishers.
2. **Given** the results page, **When** the user selects the bracket view, **Then** rounds are shown
   left-to-right through to a champion, with the winning team highlighted in each match.
3. **Given** the results page, **When** the user selects standings, **Then** a ranked table of teams
   with pool and overall results is shown.
4. **Given** the results page, **When** the user selects all scores, **Then** every match is listed
   with both teams, the set scores, and the winner highlighted.
5. **Given** the results page, **When** it loads, **Then** statistical leaders for kills, assists, and
   digs are shown, or a clear indication when leader data is unavailable.

---

### User Story 8 - Refreshed home and club browsing (Priority: P3)

A visitor lands on a home dashboard that orients them with live activity, power rankings, upcoming
tournaments, and featured coaches, and browses an upgraded clubs directory and club profile with
tiers, form trends, medals, and college commits — consistent with the hi-fi design.

**Why this priority**: Visual and informational upgrade of pages that already exist; lowest risk and
can ship incrementally without blocking other stories.

**Independent Test**: Open home and confirm the hero, stats strip, power rankings, upcoming
tournaments, and featured coaches render from data; open the clubs directory and a club profile and
confirm the upgraded sections render.

**Acceptance Scenarios**:

1. **Given** the home page, **When** it loads, **Then** it shows a hero, a season stats strip, a
   power-rankings list of top clubs, upcoming tournaments, and featured coaches, each linking to the
   relevant detail page.
2. **Given** the clubs directory, **When** it loads, **Then** clubs are listed with rank, name, tier,
   win %, form trend, team count, and medals, and can be sorted (rank/win %/teams) and filtered (tier,
   name/city).
3. **Given** a club profile, **When** it loads, **Then** it shows club identity with tier, season
   stats, teams for the season, a performance trend, a medal cabinet, recent commits, and an about
   section.

---

### Edge Cases

- A coach has no verified positions (entirely unverified): profile must clearly show "unverified ·
  pending" and must not display a verified badge.
- A coach is linked to a club that does not exist in the canonical club set: the profile must degrade
  gracefully (show the claimed club name without a broken link).
- An endorsement note contains borderline wording (e.g., a negation like "never bad"): the tone gate
  behavior must be deterministic and documented; false positives are acceptable in favor of caution.
- Two coaches share the same name: they must remain distinct entities with stable identifiers.
- A verification request references a position that was already removed or decided: resolving it must
  not error and must not double-apply verification.
- A club has no fee, medals, or radar dimensions recorded: comparison and profile views must show a
  neutral placeholder rather than implying a zero value where data is simply missing.
- A tournament has no bracket or placement data: results must show available sections and clearly mark
  unavailable ones rather than erroring.
- Concurrent endorsements or verification decisions must not corrupt counts or produce duplicates.
- In production, a client exceeding the endorsement/position rate limit (or tripping the honeypot) is
  rejected with a clear message and no data is written; a verification resolve without a valid director
  token is refused. In local/demo these protections are disabled.

## Requirements *(mandatory)*

### Functional Requirements

**Coaches & profiles (US1)**

- **FR-001**: System MUST provide a browsable directory of coaches showing, per coach, name, role,
  affiliated club, verification state, and summary stats (wins, win rate, college commits, average
  rating, endorsement count). Coach career totals (wins, win rate, commits, gold finishes, seasons)
  are stored/seeded values on the coach and are NOT derived from the canonical match/standings data.
- **FR-002**: Users MUST be able to search the coach directory by coach name or club name and filter
  to verified coaches only, with an empty state when no coaches match.
- **FR-003**: System MUST provide a coach profile showing identity, verification state, affiliated
  club (linking to the existing club profile when the club is canonical), city, career totals,
  certifications, specialties, a career timeline, teams coached, and endorsements.
- **FR-004**: System MUST assign every coach a stable, unique identifier and MUST keep coaches with
  identical display names distinct (canonical coach identity), consistent with existing club-name
  normalization practice.
- **FR-005**: System MUST record, for each coach, which club affiliation(s) are verified versus
  claimed/pending and reflect this in the verification badge and verified-position count.

**Endorsements (US2)**

- **FR-006**: Users MUST be able to submit an endorsement for a coach consisting of a star rating, a
  relationship, selected strength tags, and a written note.
- **FR-007**: System MUST restrict endorsement ratings to a positive range (4 or 5 stars only) and
  prevent selection of lower ratings.
- **FR-008**: System MUST screen endorsement notes for negative wording and block submission of notes
  that match the defined negative-tone criteria, returning clear guidance; the matching rule MUST be
  deterministic and documented.
- **FR-009**: System MUST limit endorsement note length to the defined maximum and provide remaining-
  character feedback.
- **FR-010**: System MUST persist accepted endorsements and immediately reflect them in the coach's
  endorsement list, average rating, endorsement count, and most-mentioned-strengths summary.
- **FR-011**: System MUST display each endorsement with author label, relationship/season, rating,
  date, body, and tags, and MUST present endorsements as public, positive-only content.

**Résumé builder & verification (US3, US4)**

- **FR-012**: Coaches MUST be able to add coaching positions (club, role, age group/team, years), with
  club and role required, and MUST be able to remove positions before they are verified.
- **FR-013**: System MUST mark newly added positions as unverified/pending until approved by a club
  director.
- **FR-014**: System MUST present a live preview of the coach profile that reflects current positions,
  a verified-position count, and an overall profile-strength indicator derived from completeness.
- **FR-015**: Coaches MUST be able to submit a verification request for a claimed club affiliation,
  creating a request for that club's director.
- **FR-016**: Club directors MUST be able to view pending verification requests with coach name,
  claimed role and years, a match-strength indicator and percentage (a heuristic affiliation-confidence
  signal — seeded for demo rows and assigned heuristically for submitted claims, NOT derived from
  canonical match data), and a note.
- **FR-017**: Club directors MUST be able to approve a request — marking the coach's position verified
  and linked to the club — or deny it, with the request leaving the queue in both cases and counts
  updating; resolving an already-decided or missing request MUST be safe (idempotent) and MUST NOT
  double-apply verification.

**Club comparison (US5)**

- **FR-018**: Users MUST be able to pin and unpin clubs for comparison from the clubs directory and
  club profile, with a maximum of four pinned clubs and a clear refusal when exceeding the limit.
- **FR-019**: The pinned set MUST be shared/consistent across the clubs directory, club profiles, and
  the comparison view.
- **FR-020**: The comparison view MUST present a metrics table across the defined club metrics and MUST
  highlight the best value per applicable metric, honoring "lower is better" for season fee and
  suppressing the highlight when all pinned clubs tie.
- **FR-021**: The comparison view MUST present a radar/spider chart overlaying each pinned club across
  the five defined comparison dimensions with a color-keyed legend, and MUST show an empty state when
  no clubs are pinned.

**Tournament schedule & results (US6, US7)**

- **FR-022**: System MUST present scheduled tournaments with date, name, venue, city, team count, age
  range, division, and registration status, grouped by month in a list view.
- **FR-023**: Users MUST be able to filter the schedule (at minimum by open registration, month, and
  proximity — a static per-tournament distance band from a fixed metro reference, not per-user
  geolocation) and MUST see an updating "N tournaments · N teams" count and a clear-all control.
- **FR-024**: System MUST offer calendar (month-grid) and map (city-pin) views of the same filtered
  tournament set, and MUST show an empty state when filters match nothing.
- **FR-025**: System MUST link completed tournaments to a results view.
- **FR-026**: The results view MUST present a medal podium, a championship bracket with winners
  highlighted, final standings, all match scores, and statistical leaders, switchable between bracket,
  standings, and all-scores, and MUST clearly mark any section whose data is unavailable.

**Home & club browsing (US8)**

- **FR-027**: The home page MUST present a hero, a season stats strip, a power-rankings list of top
  clubs, upcoming tournaments, and featured coaches, each linking to the relevant detail page.
- **FR-028**: The clubs directory MUST present rank, name, tier, win rate, form trend, team count, and
  medals per club, and MUST support sorting (rank/win %/teams) and filtering (tier, name/city).
- **FR-029**: The club profile MUST present club identity with tier, season stats, season teams, a
  performance trend, a medal cabinet, recent college commits, and an about section.

**Cross-cutting**

- **FR-030**: All new read endpoints and pages MUST report a data-completeness state (complete /
  partial / empty) consistent with the existing analytics pattern, and MUST degrade gracefully when
  optional data (medals, fees, radar dimensions, brackets, stat leaders) is missing.
- **FR-031**: All new write actions (endorsements, positions, verification requests, verification
  decisions, club pins) MUST validate input and MUST be safe to retry without creating duplicates or
  corrupting counts.
- **FR-032**: New data MUST preserve canonical identity for coaches and clubs, define source-of-truth
  ownership and duplicate-handling, and MUST keep coach–club links consistent with the existing
  canonical club identifiers.
- **FR-033**: New screens MUST be reachable through the application's primary navigation consistent
  with the existing site structure.
- **FR-034**: The application MUST adopt a single design system based on the NTVS-2 handoff's visual
  language (amber primary accent, deep-navy surfaces, and the handoff's display/body/mono type roles).
  This re-theme MUST be applied consistently across both the new screens and the existing pages so the
  app presents one coherent look.
- **FR-035**: In production, the system MUST apply abuse protection to write actions: rate-limit
  endorsement and position submissions per client and reject a honeypot-tripped submission, and require
  a shared director credential to resolve verification requests. These protections MUST be configurable
  — enabled by default in production and disabled for local/demo — and MUST return a clear message
  (without persisting data) when a request is throttled or rejected.

### Key Entities *(include if feature involves data)*

- **Coach**: A person with a coaching résumé. Identity (stable id, display name, normalization status),
  affiliated club link, role, city, verification state, career totals (matches won, win rate, college
  commits, gold finishes, seasons), certifications, specialties, an about summary, average rating, and
  endorsement count. Source of truth: user-claimed and/or seed-imported; not produced by the existing
  match scraper. **Career totals are standalone stored fields on the coach, NOT computed from match
  data**, and a coach is linked to a club but not to specific team match records. Where a club profile
  shows a team's "head coach", that name is matched to a coach by identity for linking only (it does
  not recompute the coach's totals).
- **Coaching Position (career entry)**: One row of a coach's career — club (and its canonical link),
  role, age group/team, years, record, an optional note, and a verification status (verified / pending
  / denied). Belongs to a Coach.
- **Endorsement**: Public, positive-only feedback for a coach — author label, relationship, rating
  (4–5), strength tags, body note, and date. Belongs to a Coach.
- **Verification Request**: A coach's claim to a club affiliation awaiting a director's decision —
  references a Coach and a Club (and the relevant Position), with claimed role/years, a match-strength
  indicator and percentage, a note, and timestamp. Resolves to approved/denied.
- **Club (extended)**: The existing canonical club, extended with presentation/comparison attributes
  needed by the handoff — tier, brand color, medal counts (gold/silver/bronze), college commits,
  coaching staff count, season fee, founding year, an about summary, and five radar dimensions. Season
  performance and ranking remain derived from existing match/standings data.
- **Tournament (extended)**: The existing tournament, extended with schedule attributes — date, venue,
  city, team count, age range, division, registration status, and featured/completed flags.
- **Tournament Result / Bracket**: Final outcomes for a tournament — podium finishers, bracket matches
  by round with winners, final standings, all match scores, and statistical leaders. Bracket and
  placement data reuse the existing bracket tables.
- **Club Pin Set**: The set of clubs (max four) a user has pinned for comparison, shared across the
  directory, club profiles, and the comparison view.

## Assumptions

- **Authentication is out of scope for this feature.** Mirroring the design prototype, identity and
  roles (visitor, coach claiming a profile, club director) are simulated rather than enforced by real
  accounts/login. "This is me" profile editing, endorsement authorship, and the director dashboard
  operate without authenticated sessions. Real authentication and authorization are a deliberate
  follow-up; this feature defines the data and workflows they will later secure.
- **Deployment target is public production from day one** (internet-facing, untrusted users). This
  raises the operability and abuse bars accordingly and is the reason write gating ships enabled in
  production (see below and FR-035).
- **Write actions are coarsely gated in production (revised posture).** There is still no per-user
  authentication, but production enables lightweight abuse protection: a per-client rate limit plus a
  honeypot on endorsement/position submissions, and a shared director token required to resolve
  verification requests. These protections are configurable and OFF for local/demo so development
  mirrors the prototype, ON in production. The only content safeguards remain positive-only screening
  (rating floor + tone gate) and idempotent writes. Real per-user identity, fine-grained authorization,
  and human moderation remain a deliberate follow-up (the authentication feature).
- **Compare "Export PDF" is out of scope.** The prototype's export control (a mock toast) is omitted;
  no PDF/print export is built in this feature.
- **Coach, endorsement, and verification data are user-generated and/or seed-imported**, not produced
  by the existing tournament scraper. Initial coach/endorsement/verification content is seeded for
  demonstration; the canonical match/standings/bracket data remains the source of truth for club and
  tournament performance.
- **Club presentation attributes** (tier, brand color, medals, fee, founding year, about, radar
  dimensions) and **tournament schedule attributes** (date, venue, city, age range, status, featured/
  completed) are new canonical fields owned by NTVS, seeded initially, and editable as data later;
  where unset they render as neutral placeholders rather than zeros.
- The negative-tone screen is a deterministic keyword/pattern check intended to keep the space
  supportive; it favors caution (may flag borderline-negative phrasing) and is not a substitute for
  human moderation.
- The pinned-clubs comparison set persists for the duration of a user's session/visit and does not
  need to survive across devices.
- The app will be re-themed to the handoff's amber/deep-navy design system, applied to existing pages
  as well as the new screens (one coherent visual system) — see FR-034. The exact token-by-token
  mapping and CSS approach are a planning (HOW) concern.
- Endorsements and coach profiles are public; no private messaging or director-mediated negative
  feedback channel is built in this feature beyond directing concerns offline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A recruiter can find a specific coach and open their full résumé in under 30 seconds
  using search/filter, with the verification state visible without scrolling.
- **SC-002**: 100% of endorsements visible to the public satisfy the positive-only policy (rating ≥ 4
  and no note matching the negative-tone criteria); no negative-rated or flagged-note endorsement is
  ever published.
- **SC-003**: A coach can add a coaching position and submit a verification request in under 2 minutes,
  and the request appears in the relevant director's queue immediately.
- **SC-004**: A club director can clear a queue of pending requests with one decision per request, and
  approved coaches show as verified everywhere they appear within the same session.
- **SC-005**: A family can pin and compare up to four clubs and identify the best club per metric at a
  glance, with the comparison reflecting pins made on any of the directory, profile, or compare views.
- **SC-006**: A user can locate tournaments for a chosen month and switch between list, calendar, and
  map views without losing their active filters, and reach results for any completed tournament in one
  click.
- **SC-007**: Every new page renders a meaningful state (complete, partial, or empty) for any data
  condition — including missing medals, fees, brackets, or stat leaders — with no error pages.
- **SC-008**: Re-running any write action (submitting the same endorsement, position, or verification
  decision) does not create duplicates or change counts beyond the first successful application.
