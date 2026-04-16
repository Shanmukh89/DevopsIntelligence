# Auditr — Design Requirements
### Automated DevOps Intelligence Platform
**Version:** 1.0 · **Status:** Design Phase · **Last Updated:** March 2026

---

## 1. Design Philosophy

Auditr occupies the intersection of intelligence and infrastructure — it must feel like a tool engineers *trust*, not one they merely tolerate. The visual language should communicate precision, depth, and calm authority.

**Core Principle:** Every design decision should reduce cognitive load. Developers using Auditr are already managing complexity; the interface must never add to it.

**Aesthetic Direction:** Dark-first, data-dense, terminal-influenced — but refined. Think Bloomberg Terminal meets Linear. Monospaced accents alongside clean sans-serif prose. High-contrast status indicators. Zero decorative noise.

---

## 2. Brand Identity

### 2.1 Naming & Voice

| Attribute | Value |
|---|---|
| **Product Name** | Auditr |
| **Tagline** | *Ship with confidence.* |
| **Voice** | Direct. Technical. Precise. Never corporate. |
| **Tone** | Like a senior engineer who's seen everything — calm, specific, never alarmist. |

The product name is always written as **Auditr** — no trademark symbol, no tagline suffix in the UI. One word, one weight.

### 2.2 Logo

The wordmark uses a monospaced typeface (e.g. `JetBrains Mono` or `IBM Plex Mono`) with the `r` optionally rendered as a stylised cursor block (`▌`) to nod toward terminal heritage. The logomark, if used standalone, is a minimal square with a diagonal audit-tick motif — no rounded corners, no gradients.

---

## 3. Color System

### 3.1 Palette

The palette is built on a near-black base with a single electric accent. Semantic colours handle all status communication.

```
Background Scale
  --bg-base:        #0A0B0D   /* primary surface */
  --bg-raised:      #111318   /* cards, panels */
  --bg-overlay:     #181C23   /* modals, dropdowns */
  --bg-subtle:      #1E2330   /* hover states, striped rows */

Border Scale
  --border-subtle:  #232940   /* dividers */
  --border-default: #2E3650   /* card edges */
  --border-strong:  #3D4A6B   /* focus rings, selected state */

Text Scale
  --text-primary:   #E8EAF0   /* headings, important data */
  --text-secondary: #8A92A8   /* body copy, labels */
  --text-muted:     #525C75   /* metadata, disabled */
  --text-inverse:   #0A0B0D   /* text on light bg */

Accent (Electric Blue)
  --accent-500:     #3B82F6   /* primary interactive */
  --accent-400:     #60A5FA   /* hover */
  --accent-600:     #2563EB   /* pressed */
  --accent-glow:    rgba(59, 130, 246, 0.15)

Semantic — Status
  --critical:       #EF4444   /* severity: critical */
  --warning:        #F59E0B   /* severity: warning */
  --success:        #22C55E   /* build passed, clean review */
  --info:           #3B82F6   /* informational */
  --neutral:        #525C75   /* dismissed, resolved */
```

### 3.2 Severity Colour Mapping

All severity indicators use a consistent system across every feature — PR reviews, vulnerability alerts, anomaly detections, and cost warnings.

| Severity | Colour | Use Case |
|---|---|---|
| Critical | `#EF4444` Red | CVEs 9.0–10.0, security bugs in PRs |
| High | `#F97316` Orange | CVEs 7.0–8.9, performance blockers |
| Warning | `#F59E0B` Amber | CVEs 4.0–6.9, style issues, cost anomalies |
| Info | `#3B82F6` Blue | Style suggestions, documentation gaps |
| Clean | `#22C55E` Green | Passing builds, resolved alerts |
| Neutral | `#525C75` Grey | Dismissed, no-ops |

---

## 4. Typography

### 4.1 Typefaces

```
Display / Headings:   Geist (by Vercel) — clean, modern, technical credibility
Body / Prose:         Geist — same family, lighter weight for legibility
Code / Monospaced:    JetBrains Mono — all code blocks, diffs, terminal output,
                      log lines, file paths, line numbers, CVE IDs
```

### 4.2 Type Scale

```
--text-xs:    11px / 1.5  (metadata, badge labels, timestamps)
--text-sm:    13px / 1.6  (secondary body, table rows)
--text-base:  15px / 1.65 (primary body)
--text-lg:    17px / 1.5  (section leads, card summaries)
--text-xl:    20px / 1.4  (panel headings)
--text-2xl:   26px / 1.3  (page titles)
--text-3xl:   34px / 1.2  (dashboard hero numbers)
```

### 4.3 Type Rules

- Page titles: `--text-2xl`, weight 500, `--text-primary`
- Section headings: `--text-xl`, weight 500, `--text-primary`
- Card labels: `--text-xs`, weight 600, `--text-muted`, UPPERCASE, letter-spacing 0.08em
- Body copy: `--text-base`, weight 400, `--text-secondary`
- Code, file paths, commit SHAs: always `JetBrains Mono`, `--text-sm`
- Large metric numbers (e.g. `₹2.4L saved`): `--text-3xl`, weight 600, `--text-primary`

---

## 5. Layout & Spacing

### 5.1 Grid

The dashboard uses a **fixed left sidebar + main content area** layout. No top navigation bar.

```
Sidebar:       240px fixed width, collapsible to 56px (icon-only mode)
Main content:  fluid, max-width 1440px, centred with 32px side padding
Top bar:       56px height, repo selector + search + notification bell
```

### 5.2 Spacing Scale

```
4px  — micro gaps (icon-to-label)
8px  — tight (badge padding, small gaps within components)
12px — default (list item padding, field labels)
16px — comfortable (card padding, form fields)
24px — section gap (between cards in a row)
32px — page margin (outer padding)
48px — section break (between major dashboard sections)
64px — hero spacing (top of empty states)
```

### 5.3 Content Density

Auditr is designed for **data-dense screens** — engineers expect to see a lot of information without scrolling. Cards should not be padded like a marketing site. Aim for 16px internal padding on cards, 12px on table rows. Comfortable but not spacious.

---

## 6. Component Library

### 6.1 Sidebar Navigation

- Items: icon (18px) + label + optional badge
- Active state: `--accent-glow` left border (3px) + `--bg-subtle` background
- Grouped by section with a `--text-xs` uppercase label above each group
- Bottom-pinned: Settings, Docs, keyboard shortcut hint

**Navigation Sections:**
```
─── OVERVIEW
    Dashboard
    Repositories

─── CODE INTELLIGENCE
    PR Reviews
    Code Q&A
    Clone Detector
    Documentation

─── OPERATIONS
    Build Monitor
    Log Anomalies
    Performance Traces

─── SECURITY & COST
    Vulnerabilities
    SQL Optimizer
    Cloud Costs
```

### 6.2 Cards

Two variants:

**Metric Card** — used on the main dashboard for at-a-glance numbers
```
Background: --bg-raised
Border:     1px solid --border-default
Padding:    20px 24px
Contents:   label (--text-xs, uppercase, muted) → large number (--text-3xl) → delta / subtitle
Hover:      border transitions to --border-strong, subtle scale(1.01)
```

**Content Card** — used for PR reviews, build records, vulnerability alerts
```
Background: --bg-raised
Border:     1px solid --border-default
Padding:    16px
Header:     label + severity badge + timestamp (right-aligned)
Body:       content-specific
Footer:     action links in --accent-500
```

### 6.3 Severity Badges

Compact, pill-shaped, no border.

```
[CRITICAL]  bg: rgba(239,68,68,0.15)   text: #EF4444   mono font
[HIGH]      bg: rgba(249,115,22,0.15)  text: #F97316
[WARNING]   bg: rgba(245,158,11,0.15)  text: #F59E0B
[INFO]      bg: rgba(59,130,246,0.15)  text: #60A5FA
[CLEAN]     bg: rgba(34,197,94,0.15)   text: #22C55E
```

All badge text: `JetBrains Mono`, `--text-xs`, weight 600, uppercase, 4px padding vertical, 8px horizontal.

### 6.4 Code Diff Viewer

Used in PR Reviews and Clone Detector.

```
Font:           JetBrains Mono, 13px
Line numbers:   right-aligned, --text-muted, min-width 40px, non-selectable
Added lines:    bg rgba(34,197,94,0.08), left border 2px solid #22C55E
Removed lines:  bg rgba(239,68,68,0.08), left border 2px solid #EF4444
Comment markers: blue dot at gutter + tooltip on hover
Scrollbar:      custom, 4px wide, --border-subtle thumb
```

### 6.5 Chat Interface (Codebase Q&A)

```
Layout:         two-column — chat thread (60%) + cited code panel (40%)
User messages:  right-aligned, --bg-overlay bg, --text-primary
AI messages:    left-aligned, no background, --text-secondary
Code citations: inline monospaced blocks with file path + line range as header
                clicking a citation highlights it in the right panel
Streaming:      character-by-character, blinking cursor ▌ at stream end
Input:          full-width, --bg-overlay, border on focus, CMD+Enter to send
```

### 6.6 Flame Graph (Performance Tracer)

```
Container:      full-width, horizontally scrollable
Time axis:      top-pinned, tick marks every 10ms
Spans:          height 24px, rounded 2px, colours by service (distinct hues from a
                12-colour service palette — no semantic meaning, just differentiation)
Labels:         service name + duration, truncated with ellipsis if span too narrow
Hover state:    tooltip with: service, operation, duration, status, trace ID
Selected span:  outlined in white, detail panel slides in from right
Error spans:    red diagonal stripe pattern overlaid on span colour
```

### 6.7 Buttons

```
Primary:   bg --accent-500, text white, hover --accent-400, 8px v-pad, 16px h-pad
Secondary: bg transparent, border 1px --border-default, text --text-secondary, same padding
Ghost:     no bg/border, text --accent-400, hover --bg-subtle bg
Danger:    bg rgba(239,68,68,0.1), border rgba(239,68,68,0.3), text #EF4444
Disabled:  opacity 0.4, cursor not-allowed on all variants

Border-radius: 6px on all buttons
Font:          --text-sm, weight 500
```

### 6.8 Tables

Used in vulnerability lists, build history, cost recommendations.

```
Header row:     --bg-overlay bg, --text-xs uppercase label, --text-muted
Body rows:      --bg-raised bg, 12px vertical padding, --border-subtle bottom border
Striped option: alternate rows use --bg-subtle
Hover row:      --bg-overlay
Sorted column:  header accent + chevron icon
Clickable rows: full-row click area, cursor pointer
```

### 6.9 Toast Notifications

Slide in from bottom-right. Auto-dismiss after 5s. Stack vertically.

```
Width:    320px
Bg:       --bg-overlay, border 1px --border-default
Icon:     severity-coloured, 18px, leftmost
Title:    --text-primary, --text-sm, weight 500
Body:     --text-secondary, --text-sm
Action:   optional text link, --accent-400
Dismiss:  × button, top-right
```

---

## 7. Feature-Specific Design Specs

### 7.1 Main Dashboard

The dashboard is the single-pane-of-glass. It should answer *"what needs my attention right now?"* in under 3 seconds.

**Layout — top to bottom:**

```
1. Repository selector bar (full width, switches context for all panels below)
2. Four metric cards in a row:
   [ Open PRs ]  [ Build Health (7d) ]  [ Vulnerabilities ]  [ Potential Savings ]
3. Two-column section:
   Left (60%):  Recent PR Reviews — last 5, with severity badges and author avatars
   Right (40%): Build Activity — sparkline + last 10 builds with status dots
4. Two-column section:
   Left (50%):  Security Alerts — top 3 critical/high, "View all →" link
   Right (50%): Cloud Cost Recommendations — top 3 by savings, "View all →" link
5. Full-width: Log Anomaly Timeline — past 24h, time on x-axis, severity on y-axis
```

### 7.2 PR Reviews Page

- List view: each row shows PR number, title, author, opened time, review status badge, issue count
- Detail view: two columns — original diff left, AI review right
  - Each AI issue anchors to the corresponding diff line via scroll sync
  - Issue list at top right: filter by severity
  - "Post to GitHub" button if review hasn't been pushed yet

### 7.3 Build Monitor

- Build list: status icon (✓/✗/○), repo, branch, commit SHA (mono), author, duration, time ago
- Build detail:
  - AI explanation in a highlighted callout box at top — most important, most visible
  - Stack Overflow results as 3 linked cards below, showing vote count + answer snippet
  - Full log in collapsible monospaced block, last 150 lines highlighted on open

### 7.4 Vulnerability Scanner

- Table of packages with: name, installed version, severity, CVE ID, patched version, status
- Row expansion reveals: full description, affected range, patch instructions
- Filter bar: by severity, by ecosystem (pip/npm/maven), by status
- "Mark resolved" and "Dismiss" actions inline per row

### 7.5 SQL Optimizer

- Two-panel layout: original query left, optimised query right
- Diff highlighting on the right (changed tokens highlighted in --accent-glow)
- EXPLAIN output as a collapsed section with key metrics surfaced: seq scans, exec time, buffer hits
- Numbered change list below — plain English, each item maps to a highlighted token
- Recommended `CREATE INDEX` statements in a separate code block with copy button

### 7.6 Cloud Cost Dashboard

- Sunburst / treemap for cost breakdown by service (D3.js — colours from the service palette)
- Recommendations table sorted by potential saving descending
- Each row: resource ID (mono), type, current cost/mo, potential saving/mo, action button
- Summary bar at top: Total spend · Analysed resources · Total identified savings

---

## 8. Motion & Interaction

### 8.1 Animation Principles

- Duration: 120–200ms for UI feedback, 300–400ms for panel transitions
- Easing: `cubic-bezier(0.16, 1, 0.3, 1)` (Expo out) for reveals, `ease-out` for dismissals
- No animation should block user action or feel slow
- Preference for CSS transitions over JS animation for performance

### 8.2 Specific Interactions

| Interaction | Animation |
|---|---|
| Sidebar collapse/expand | Width transition 200ms + icon label fade |
| Card hover | `transform: scale(1.01)` + border colour transition 150ms |
| Toast appear | Slide up from bottom + fade in 250ms |
| Toast dismiss | Slide right + fade out 200ms |
| Chat stream | Character reveal + cursor blink at 530ms interval |
| Build status badge | Pulse ring animation on `running` state |
| Severity badge | No animation — must be instantly readable |
| Flame graph span hover | Tooltip fade in 100ms |
| Page transition | Fade 150ms — never slide or zoom |

### 8.3 Loading States

- Skeleton loaders (not spinners) for all content that loads asynchronously
- Skeleton colour: `--bg-overlay` shimmer animation
- Inline spinner (16px) only for button-triggered actions where content area doesn't change

---

## 9. Iconography

Use [Lucide Icons](https://lucide.dev) throughout. 18px default size, 20px in navigation, 14px in badges.

**Feature → Icon mapping:**

| Feature | Icon |
|---|---|
| PR Reviews | `git-pull-request` |
| Code Q&A | `message-square-code` |
| Clone Detector | `copy` |
| Documentation | `file-text` |
| Build Monitor | `workflow` |
| Log Anomalies | `activity` |
| Performance Tracer | `flame` |
| Vulnerabilities | `shield-alert` |
| SQL Optimizer | `database-zap` |
| Cloud Costs | `cloud` |
| Settings | `settings` |
| Repositories | `git-branch` |
| Slack integration | `slack` (brand icon) |

---

## 10. Empty & Error States

### 10.1 Empty States

Every feature must have a considered empty state — shown on first use before data exists.

```
Structure:
  64px top padding
  Icon (32px, --text-muted)
  Heading (--text-xl, --text-primary)  e.g. "No vulnerabilities found"
  Subtext (--text-base, --text-secondary)  e.g. "Connect a repository to begin scanning"
  CTA button (primary) if an action can create data
```

Empty states should be honest and minimal — no illustrations, no decorative elements.

### 10.2 Error States

```
Inline error (field level): --critical colour, --text-xs, below the field
Card error: red left border (3px) + error icon + message in card body
Full-page error: centered, status code in --text-3xl mono, short message, retry button
API failure toast: auto-appears, "Something went wrong — try again" + retry link
```

---

## 11. Responsive Behaviour

Auditr is primarily a **desktop application** used on large monitors (1440px+). However:

- **1280px:** Sidebar collapses to icon-only mode by default
- **1024px:** Two-column layouts stack to single column
- **< 768px:** Not supported — show a "Auditr works best on a larger screen" message

No native mobile app in v1. Engineers use Auditr at their desks.

---

## 12. Accessibility

- Colour contrast: minimum **4.5:1** for body text, **3:1** for large text and UI components (WCAG AA)
- Keyboard navigation: all interactive elements reachable by Tab, focus ring always visible (`--border-strong` outline)
- Screen reader: all icon-only buttons have `aria-label`, all status badges have `role="status"`
- Severity is never communicated by colour alone — always paired with a text label or icon
- Motion: `prefers-reduced-motion` disables all transitions and animations

---

## 13. Notification Design (Slack)

Auditr's Slack messages are as important as the dashboard UI — engineers often act on them directly.

### Message Structure

```
[Auditr] · repository-name/branch-name

*Build Failed* — main · 3 minutes ago
Commit: `a3f2c1d` by @developer-name

*What happened:*
The build failed because a required environment variable `STRIPE_SECRET_KEY`
was missing from the CI environment. The test suite detected this on line 47
of `tests/test_payments.py`.

*Fix:*
Add `STRIPE_SECRET_KEY` to your GitHub Actions secrets under Settings → Secrets.

*Stack Overflow:*
• [How to add secrets to GitHub Actions](link) — 847 votes
• [Missing env variable in CI/CD pipeline](link) — 412 votes

[View Build] [Dismiss]
```

**Formatting rules:**
- Always include repo + branch context at top
- Bold section headers (`*What happened:*`, `*Fix:*`)
- Inline code for file paths, variable names, commit SHAs
- Stack Overflow results as bullet links, always include vote count
- Action buttons at bottom

---

## 14. Design Deliverables Checklist

Before development begins, the following design assets should be completed:

- [ ] Component library (Figma) with all components in light-hover, dark-default, focused, disabled, error states
- [ ] Dashboard layout (all 11 feature pages)
- [ ] Empty states for all 11 features
- [ ] Slack message templates (PR review, build failure, vulnerability alert, anomaly alert)
- [ ] Onboarding flow (connect GitHub → connect Slack → connect AWS)
- [ ] Mobile "unsupported" screen
- [ ] Favicon, og:image, product logo in SVG

---

*Design Requirements · Auditr v1.0 · Maintained by Antigravity · March 2026*