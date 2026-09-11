# OneWay Sentinel — Design System & UI Specification (`design.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)
**Source documents:** `master-prd.md` (Master PRD v1.0), `oneway_sentinel_architecture.md` (System Architecture), `appflow.md` (Application Flow)
**Reference images:** two SOC-style dashboard screenshots ("Cyber Threat Monitor," light-mode reference for information density/layout patterns; "SENTINEL-X," dark-mode reference for the target visual language)
**Document status:** Implementation-ready design specification for a coding agent building the React + Tailwind frontend described in `architecture.md` §3/§23 (frontend/src/pages, frontend/src/components).

> **Scope discipline:** This document designs exactly the four page components named in `architecture.md`'s frontend folder tree — `MainDashboard.jsx`, `AlertDetail.jsx`, `AlertHistory.jsx`, `NetworkGraph.jsx` — plus the seven named components (`StatusBar`, `ZeroOutboundBadge`, `TrafficChart`, `ThreatBreakdown`, `LiveAlertFeed`, `SimulatorControls`, `FilterBar`). No additional pages are invented. Where `appflow.md` flags an `[ARCHITECTURE GAP]` or `[ASSUMPTION]` (e.g., top-level navigation mechanism, PCAP upload placement, loading/empty/error states), this document makes one concrete, documented design decision so the spec is implementable — each such decision is labeled **[DESIGN DECISION — fills a documented gap]** so it's traceable back to its source gap.

---

# 1. Design Overview

OneWay Sentinel's frontend is a single-page React application with four screens surfaced through a persistent sidebar: **MainDashboard** (default route), **AlertHistory**, **NetworkGraph** (P2, feature-flagged), and **AlertDetail** (reached only via alert click-through, never a nav item). The product is a SOC/NOC-style monitoring tool for a hackathon prototype demonstrating that real-time, explainable threat detection works on one-way flow metadata alone — so the UI's central job is to make three things instantly legible: **(1) is the link currently under threat, (2) can I trust why the system says so, and (3) can I prove this tool never sends anything back through the diode.**

The design draws its layout discipline and information density from the "Cyber Threat Monitor" reference (clear card grid, readable light-adjacent data density, explicit status badges) and its visual language — dark surface, restrained neon accent, glass panels, monospace technical data — from the "SENTINEL-X" reference. Neither is copied directly; both are synthesized into one original dark SOC aesthetic defined in Sections 7–14 below.

---

# 2. Product Design Philosophy

- **Evidence over assertion.** Every alert, every score, every "NORMAL" badge must be backed by visible, inspectable data (PRD §6.5 — explainability is P0, not decoration). The UI never shows a verdict without a path to the evidence behind it.
- **Passive, not paranoid.** This is a *detect-only* system (PRD Non-Goals: no active response). The UI must never imply the system can block, reset, or act on traffic — action buttons are limited to analyst triage (Acknowledge / False Positive / Notes), never network-level control.
- **The zero-outbound guarantee is a first-class UI citizen.** Per PRD §11 and FR-018, the "0 bytes sent back" signal is a *trust product*, not a footnote — it gets permanent, unmissable placement (Section 16).
- **Severity is never color-only.** Per PRD §12 and accessibility requirements (Section 36), every severity indicator pairs color with an icon and a text label.
- **Honest about gaps.** Where the source documents leave a UI question open (loading states, PCAP upload placement, inter-page navigation), this spec makes an explicit, minimal, professional default rather than inventing new functionality.

---

# 3. UX Goals

1. An analyst glancing at MainDashboard for 3 seconds should know: link status, whether anything critical is active, and roughly how much traffic is flowing.
2. A new alert should be visually unmissable within the 2-second latency target (PRD FR-020) without being alarmist (no full-screen takeovers, no sound assumptions).
3. Any alert's explanation should be readable and understood by someone without ML background (PRD "Usability" NFR) — plain language first, raw feature data available but secondary.
4. A security lead should be able to go from "I want last week's High+ alerts from one IP" to a filtered table in under three interactions.
5. The demo/simulator controls must be usable live, on stage, without ambiguity about what's about to happen (PRD §21 UC — presenter story).
6. Nothing in the UI should suggest the system can act on the network — visual language stays strictly "observe and explain."

---

# 4. Visual Direction

**Direction:** Professional futuristic SOC / network-threat-monitoring platform — deep dark navy-black canvas, glass-panel cards with thin translucent borders, a single disciplined cyan accent for "live/system" state, semantic severity colors reserved *only* for severity, monospace for all machine-readable identifiers (IPs, ports, protocols, hashes, timestamps), sans-serif for everything a human reads as prose. Glow is a severity/status signal, not a decoration — it appears on live indicators and Critical/High alerts, nowhere else.

**Explicitly avoided:** rainbow dashboards, decorative particle effects, gaming-style beveled buttons, cryptocurrency-ticker aesthetics, generic Bootstrap-admin card shadows, and unmodulated glassmorphism (every panel glows the same way it's not glass, it's noise).

---

# 5. Reference Analysis

### Reference A — "Cyber Threat Monitor" (light-mode SOC dashboard)
**What to take:** the KPI-row-then-detail-grid layout skeleton (four top stat cards → two-column chart row → wide live table → alert table); inline sparklines inside stat cards; a right-aligned donut with a centered aggregate number and a legend with percentages; a "TOP TALKERS" horizontal bar-in-table pattern; System Status and AI Model panels pinned to the bottom of the sidebar; per-row "Block IP" action pattern (**note:** OneWay Sentinel is detect-only per PRD Non-Goals — this pattern is adapted to "Acknowledge / False Positive," never an actual block action).
**What to leave behind:** light background, saturated indigo sidebar accent, default Tailwind card shadows — none fit the target dark SOC aesthetic.

### Reference B — "SENTINEL-X" (dark-mode AI threat intelligence dashboard)
**What to take:** near-black canvas with a very subtle top-lit gradient; glass stat cards with soft cyan-tinted shadow instead of a hard border; a labeled 5-step horizontal "Detection Pipeline" strip (maps almost exactly onto OneWay Sentinel's real pipeline: Ingest → Feature Extraction → Hybrid ML → Risk/Severity → Alert, PRD §10 / architecture.md §1); a donut chart with a large centered total and a colored-dot legend; a live "activity feed" pattern with small icon chips per event; severity badges as small filled pills (CRITICAL/HIGH/MEDIUM) rather than full-width banners; confidence values shown as a numeric % plus a thin progress bar inline in a table row.
**What to leave behind:** the world-map/flow-line hero visual (no destination-geography claim beyond the P1 "Approximate Location" badge — PRD makes no claim about a live global traffic map, and `appflow.md` explicitly notes geolocation is per-alert, not a dashboard hero); the "Live Traffic Overview" globe graphic overall (not supported by any PRD feature).

### Synthesis
OneWay Sentinel's MainDashboard = Reference A's grid discipline (KPI row → chart row → live table → alert list) rendered in Reference B's dark glass-and-cyan visual language, with the Detection Pipeline strip adopted directly as a way to visualize PRD §10's real pipeline (this reference concept maps onto documented functionality, so it is kept; the decorative globe does not map onto documented functionality, so it is dropped).

---

# 6. Design Principles

1. **One accent, semantic severity.** Cyan = system/live/informational only. Green/amber/red-family = severity only. Never mix the two roles.
2. **Monospace = machine data, sans = human data.** If a human typed it or reads it as a sentence, sans-serif. If it's an IP, port, protocol, hash, ID, or raw timestamp, monospace.
3. **Every card answers one question.** A KPI card shows one number and its trend. A panel groups one topic. No card mixes unrelated data to save space.
4. **Motion communicates state change, not decoration.** Animate only: new-alert arrival, live counters incrementing, connection status changes, chart data updates.
5. **Degraded is a visible state, not a silent failure.** Per FR-021 (ML degrades gracefully), the UI has an explicit "Degraded" status treatment, not just "Live" and gone.
6. **Never claim certainty the system doesn't have.** Per PRD §9's disclaimer, category labels and confidence are always shown as indicators, never as verdicts ("Category: Port Scanning · 87% confidence," never just "THREAT: Port Scanning").

---

# 7. Color System

All values are final hex tokens, chosen and adjusted from the reference direction (Section 5) against WCAG contrast requirements on the dark canvas (Section 36).

```
BACKGROUND
background            #0A0E17   Base app canvas
backgroundGradientTop  #131B2E   Radial gradient origin (top-of-viewport lightening)
surface                #101828   Card/panel base surface (glass base, ~60% opacity over background)
surfaceElevated        #16202F   Modals, dropdowns, popovers, elevated panels
surfaceSunken          #0C121C   Table row alt-stripe, input backgrounds, code blocks

SIDEBAR / HEADER
sidebarBg              #0B111C   Sidebar surface (very slightly darker than background)
headerBg                #0D1420   Header surface
navActiveBg             #14304A   Active nav item background (cyan-tinted)

BORDERS
border                  #FFFFFF14   (rgba white 8%) Default hairline border
borderStrong            #FFFFFF26   (rgba white 15%) Emphasized border, hover
borderFocus             #00D9E0     Focus ring / active input border

BRAND / ACCENT
primary                 #00D9E0   Cyan — live/system/informational accent
primaryMuted            #00D9E033 Cyan at 20% — backgrounds behind cyan badges/icons
secondary               #6C7BFF   Indigo — used only for secondary chart series / links
accent                  #00FFC2   Mint-cyan — "Normal traffic" positive accent (distinct from success-green so normal-traffic-volume ≠ generic "success")

TEXT
textPrimary             #E9EEF5   Headings, primary values, KPI numbers
textSecondary           #9AACC2   Body copy, descriptions, secondary labels
textMuted               #647089   Captions, timestamps, placeholder text
textDisabled            #3E4A5E   Disabled control text
textOnAccent            #04141A   Text placed on solid cyan/mint fills

SEVERITY (PRD §12 five-band scale)
informational            #6C7BFF   0–19  Informational
low                       #00C2A8   20–39 Low
medium                    #F5A524   40–59 Medium
high                      #FF7A45   60–79 High
critical                  #FF3B5C   80–100 Critical

SEMANTIC (non-severity)
success                   #2ED47A   Confirmation, "system healthy," positive deltas
warning                   #F5A524   Degraded state, non-critical operational warnings (shares hue with `medium` intentionally — both mean "pay attention," never overlaps on one screen)
danger                    #FF3B5C   Destructive-styled actions (rare in a detect-only product), errors
info                      #00D9E0   Informational banners, tooltips (shares `primary`)

CHART PALETTE (categorical, up to 6 series)
chart1 (TCP)              #00D9E0
chart2 (UDP)               #6C7BFF
chart3 (ICMP)               #F5A524
chart4 (Other/rare)          #9AACC2
chart5 (extra category)       #FF7A45
chart6 (extra category)        #2ED47A
```

**Contrast notes:** `textPrimary` on `background` = 13.9:1; `textSecondary` on `background` = 7.1:1; `critical` badge text uses `textOnAccent`-equivalent dark text on the filled critical background where filled, or `critical` text on `surface` (contrast 4.9:1, passes AA for the 14px+ badge text size used).

---

# 8. Typography System

**Primary (UI/sans) font:** `Inter` (fallback: `-apple-system, "Segoe UI", Roboto, sans-serif`) — all headings, body copy, labels, navigation, buttons.
**Monospace (technical) font:** `"JetBrains Mono"` (fallback: `"IBM Plex Mono", "SFMono-Regular", Menlo, monospace`) — all IPs, ports, protocols, threat/flow IDs, hashes, raw timestamps, log lines, table cells containing the above.

| Style | Font | Size | Weight | Line height | Letter spacing | Used for |
|---|---|---|---|---|---|---|
| H1 | Inter | 28px | 700 | 1.25 | -0.01em | Page titles ("Dashboard", "Alert History") |
| H2 | Inter | 20px | 600 | 1.3 | -0.005em | Panel/section headers ("REAL-TIME TRAFFIC MONITOR") |
| H3 | Inter | 16px | 600 | 1.35 | 0 | Card titles, subsection headers |
| H4 | Inter | 13px | 700 | 1.3 | 0.06em, uppercase | KPI card labels, table column headers ("TOTAL TRAFFIC") |
| Body | Inter | 14px | 400 | 1.55 | 0 | Descriptions, explanation text, form labels |
| Body Small | Inter | 13px | 400 | 1.5 | 0 | Secondary body copy, helper text |
| Caption | Inter | 12px | 500 | 1.4 | 0.02em | Timestamps (human-formatted), muted metadata |
| Nav Label | Inter | 14px | 500 | 1.4 | 0 | Sidebar navigation items |
| Button | Inter | 14px | 600 | 1 | 0.01em | All button text |
| KPI Number | JetBrains Mono | 34px | 700 | 1.1 | -0.01em | Large stat-card numbers |
| KPI Number (compact) | JetBrains Mono | 22px | 700 | 1.1 | -0.005em | Secondary/smaller KPI contexts |
| Table Text (data) | JetBrains Mono | 13px | 400 | 1.5 | 0 | IPs, ports, protocols, IDs in tables |
| Table Text (label) | Inter | 13px | 500 | 1.5 | 0 | Non-technical table cells (status, category name) |
| Chart Axis Label | JetBrains Mono | 11px | 400 | 1.2 | 0 | Numeric axis ticks |
| Chart Category Label | Inter | 12px | 500 | 1.2 | 0 | Legend text, category axis labels |
| Code/Log | JetBrains Mono | 12px | 400 | 1.6 | 0 | Explanation "evidence" blocks, raw feature dumps |

---

# 9. Spacing System

8px base unit, used consistently for padding, gaps, and margins.

```
xs:   4px    (icon-to-label gaps, badge internal padding)
sm:   8px    (compact card internal spacing, form field gaps)
md:   16px   (default card padding, gap between related cards)
lg:   24px   (gap between distinct sections, page gutters on tablet)
xl:   32px   (page gutters on desktop, gap between major page sections)
2xl:  48px   (top-of-page spacing below header)
```

---

# 10. Grid System

- **Base layout:** 12-column grid within the content area (excludes sidebar), 24px (`lg`) gutter, max content width 1440px, centered beyond that on very large monitors.
- **Desktop (≥1280px):** Sidebar fixed 260px. Content area uses full 12-column grid. KPI row = 4 columns × 3-span each (or 4×3-span for a 4-card row). Two-panel chart rows = 8-span + 4-span (primary chart + donut) or two 6-span panels.
- **Laptop (1024–1279px):** Sidebar collapses to icon-only 72px (expandable on hover/click). KPI row wraps to 2×2.
- **Tablet (768–1023px):** Sidebar becomes an overlay drawer (hidden by default, hamburger-triggered). Content is single-column stacked; charts go full-width.
- **Mobile (<768px):** Same as tablet, with KPI cards stacked 1-per-row, tables converted to stacked "card" rows (Section 35).

---

# 11. Border & Radius System

```
radius.xs:   4px   (badges, small chips)
radius.sm:   6px   (buttons, inputs, table cells)
radius.md:   10px  (standard cards/panels)
radius.lg:   16px  (large hero panels, modals)
radius.full: 999px (pills, avatar, status dots)

border.width.default: 1px
border.width.focus:   2px
border.style:          solid, using `border` / `borderStrong` / `borderFocus` tokens from Section 7
```

Cards use `radius.md` universally for consistency (matches the reference direction's rounded-2xl-equivalent restraint — not overly rounded, not sharp-cornered enterprise-generic).

---

# 12. Shadow & Glow System

Glow is reserved for **live/active state** and **High/Critical severity**, never applied decoratively to neutral cards.

```
shadow.sm:  0 1px 2px rgba(0,0,0,0.4)                          — default card resting shadow
shadow.md:  0 4px 16px rgba(0,0,0,0.35)                        — elevated panels, dropdowns
shadow.lg:  0 12px 32px rgba(0,0,0,0.45)                       — modals

glow.cyan:      0 0 0 1px rgba(0,217,224,0.25), 0 0 20px rgba(0,217,224,0.12)   — live status dot, active nav item, focus rings
glow.mint:      0 0 20px rgba(0,255,194,0.10)                                   — "Normal traffic" KPI card accent (subtle, on hover only)
glow.warning:   0 0 20px rgba(245,165,36,0.14)                                  — High-severity alert card left-edge glow
glow.critical:  0 0 24px rgba(255,59,92,0.18)                                   — Critical-severity alert card left-edge glow, pulsing (Section 37)
```

**Rule:** at most one glow per card. A Critical alert card gets `glow.critical` and nothing else. A live status dot gets `glow.cyan` and nothing else. Never stack glows.

---

# 13. Glass / Surface System

Glass is used for **elevated content panels only** (cards, modals, dropdowns) — never the sidebar, header, or full-page background, which stay flat/opaque for legibility and performance.

```
Standard card:
  background: surface (#101828) at 72% opacity
  backdrop-filter: blur(20px)
  border: 1px solid border (#FFFFFF14)
  border-radius: radius.md
  box-shadow: shadow.sm

Elevated panel (modal, dropdown):
  background: surfaceElevated (#16202F) at 88% opacity
  backdrop-filter: blur(24px)
  border: 1px solid borderStrong
  box-shadow: shadow.lg
```

Glass is applied at most two "layers" deep on any screen (e.g., a dropdown-over-a-card is fine; a card-over-a-card-over-a-card is not) to avoid the "everything glows" failure mode called out in the brief's Strict Rules.

---

# 14. Iconography

**Icon set:** `lucide-react` (consistent stroke-based icon family, matches the technical/precise tone; avoids filled/glyph icons that read as playful).
**Default stroke width:** 1.75px. **Default size:** 18px inline / 20px in nav / 16px in badges.
**Usage map:**
- Shield (`ShieldCheck` / `ShieldAlert`) — brand mark, zero-outbound badge, system-health indicators.
- `Activity` — live traffic / status pulse.
- `AlertTriangle` — Medium/High alerts.
- `AlertOctagon` — Critical alerts.
- `CheckCircle2` — Normal/Low, Acknowledged status.
- `XCircle` — False Positive status.
- `Radio` — beaconing/C2-style category icon.
- `Network` — scan categories, NetworkGraph nav.
- `Search` — search inputs, port-scan category icon.
- `Upload` — PCAP upload control.
- `Play` / `Square` — simulator start/stop.
- `MapPin` — Approximate Location (geolocation, P1).
- `Clock` — timestamps, history nav.
- `Filter` — FilterBar toggle.
- `WifiOff` — WebSocket disconnected / degraded-mode indicator.

Icons never carry meaning alone for severity (Section 36) — always paired with color + text label.

---

# 15. Application Shell

```
┌──────────┬──────────────────────────────────────────────────────────┐
│          │  Header (64px)                                           │
│ Sidebar  ├──────────────────────────────────────────────────────────┤
│ (260px)  │                                                          │
│          │  Page content (scrollable, max-width 1440px, xl gutters) │
│          │                                                          │
└──────────┴──────────────────────────────────────────────────────────┘
```

Fixed sidebar + fixed header, independently-scrolling content area. Background is `background` (#0A0E17) with a very subtle radial gradient lightening toward `backgroundGradientTop` centered at the top of the viewport (matches Reference B's top-lit canvas, at low intensity so it never competes with card content).

---

# 16. Sidebar Design

**Width:** 260px expanded / 72px collapsed (icon-only, laptop breakpoint default per Section 10).
**Structure, top to bottom:**
1. **Brand block** (72px tall): Shield icon (cyan) + "OneWay Sentinel" (H3, textPrimary) + tagline "AI Threat Detection · Unidirectional" (Caption, textMuted).
2. **Primary navigation** (Section 18): Dashboard, Alert History, Network Graph (P2, see below).
3. **Divider.**
4. **ZeroOutboundBadge** — pinned above the footer, always visible without scrolling, per FR-018's requirement that this indicator be persistent:
   ```
   ┌────────────────────────────┐
   │ ● 0 BYTES SENT BACK          │   ShieldCheck icon, mint/success color,
   │ Passive monitoring verified   │   Caption line beneath in textMuted.
   └────────────────────────────┘
   ```
   Background: `success` at 8% opacity, 1px `success`-at-30%-opacity border, `radius.md`. This is the single most important trust element in the product (PRD §11) — it never collapses, even in the icon-only sidebar state (icon-only mode shows just the shield glyph with a green dot, tooltip on hover reveals full text).
5. **System status footer**: connection state (Live / Degraded / Disconnected — Section 34), model status ("RF + IF · Active"), last-updated timestamp — mirrors the reference's "SYSTEM STATUS" panel pattern, scoped to what architecture.md's `GET /api/status` actually returns.

**NetworkGraph nav item:** rendered only when the P2 feature is enabled (feature flag `enableNetworkGraph`); when disabled it is simply omitted from the list rather than shown disabled, since it's not part of MVP scope (PRD §24).

---

# 17. Header Design

**Height:** 64px, `headerBg`, bottom border `border`.
**Layout (left to right):** Page title (H1, updates per route) → flexible spacer → global search input (400px, placeholder "Search IP, flow ID...") → notification bell (badge = count of unacknowledged Critical/High alerts, from `LiveAlertFeed`/`AlertHistory` data, not a separate endpoint) → live clock (monospace, HH:MM:SS, local time) → user/session indicator.

**[DESIGN DECISION — fills a documented gap, `appflow.md` §22 "No RBAC / role differentiation in MVP"]:** Since MVP has no authentication (PRD §24: auth is P2) and no distinct technical roles (`appflow.md` §2), the header shows a neutral **"Local Session"** indicator (icon + "Local Session" text) instead of a named user/avatar — this avoids implying a login/identity system that doesn't exist in MVP, while leaving a natural slot for a real user menu once P2 auth ships.

**Global search:** per `appflow.md`, no dedicated global-search API/behavior is specified anywhere in the source documents. This field is included because both reference images treat it as baseline SOC-tool chrome, but per Strict Rule #5 ("do not invent functionality"), **it is scoped to client-side filtering of already-loaded AlertHistory/LiveAlertFeed data only** (never a new backend endpoint) — typing an IP filters the currently visible alert list. This is documented here explicitly so the implementing agent does not invent a `/api/search` route.

---

# 18. Navigation Architecture

**[DESIGN DECISION — fills a documented gap, `appflow.md` §22 "Top-level navigation mechanism between pages"]:** `architecture.md` names four page components but no router/nav-bar. This spec defines the sidebar (Section 16) as that navigation, using React Router with three top-level routes plus one non-navigable detail route:

```
/                    → MainDashboard   (default/landing, per appflow.md §3)
/history             → AlertHistory
/graph               → NetworkGraph   (P2, feature-flagged nav item)
/alerts/:alertId     → AlertDetail    (never a sidebar item — reached only via
                                        click-through from LiveAlertFeed or
                                        AlertHistory row, per appflow.md §3/§4)
```

AlertDetail renders with a **Back** button (top-left, arrow-left icon + "Back") that uses browser history to return to whichever list the user came from, rather than a hardcoded destination — satisfying `appflow.md`'s note that AlertDetail's return navigation is otherwise unspecified.

Active nav item: `navActiveBg` background, `primary`-colored left border (3px), icon and label in `textPrimary` (inactive items use `textSecondary`).

---

# 19. Page-by-Page Design

The following four subsections (20, and this section's continuation in 22/26 below) cover every screen named in `architecture.md`'s `frontend/src/pages/` tree, per `appflow.md` §3–4. No additional pages are defined.

## MainDashboard
See Section 20 (Dashboard Design) for full detail — summarized here per the required page-by-page format.

**Purpose:** Single real-time view of link health and active threats (PRD §6.6).
**User goal:** In seconds, know whether the link is safe, and see any new threat as it happens.
**Layout:** StatusBar → KPI row (4 cards) → chart row (TrafficChart + ThreatBreakdown) → Detection Pipeline strip → two-column (LiveAlertFeed + SimulatorControls) → (optional) Top Talkers panel.
**Components:** StatusBar, ZeroOutboundBadge (sidebar-persistent, also referenced in StatusBar), 4× KPI Card, TrafficChart, ThreatBreakdown (donut), LiveAlertFeed, SimulatorControls.
**Data:** `GET /api/status`, `GET /api/stats/live`, `/ws/alerts` stream (per `appflow.md` §4).
**Primary actions:** None required (read-only surveillance); optional: start/stop simulator traffic, trigger attack scenario, click an alert.
**Secondary actions:** PCAP upload (see Section 20's dedicated subsection).
**Navigation:** Click alert row → AlertDetail. Sidebar → AlertHistory / NetworkGraph.
**Filters/Search:** None on this page (filtering lives on AlertHistory) — LiveAlertFeed shows the most recent N alerts only, unfiltered, by design (it's a feed, not a query surface).
**Charts:** TrafficChart (line), ThreatBreakdown (donut) — Section 22.
**Tables:** None (LiveAlertFeed is a list, not a table — see Section 20).
**Maps:** None on MainDashboard (Approximate Location is scoped to AlertDetail only, per `appflow.md`).
**Forms:** SimulatorControls (scenario select + start/stop), PCAP upload control.
**Empty/Loading/Error states:** Section 31–33.
**Responsive:** Section 35.
**Interactions:** Live-updating counters/charts (no manual refresh), click-through on alerts, simulator controls are the only writes on this page.

## AlertDetail
**Purpose:** Let an analyst understand exactly why a flow was flagged and review its full evidence (PRD §6.5).
**User goal:** Decide, with full evidence in view, whether to Acknowledge or mark False Positive.
**Layout:** Header (Back button + Severity badge + Category badge) → two-column body: left = Flow Metadata panel + Explanation panel + Recent Source History (P1); right = Risk Score gauge/panel + Approximate Location (P1) + Triage Actions panel.
**Components:** Severity badge, category Threat badge, flow metadata table, explanation text block, risk-score radial indicator, geolocation card, recent-history mini-list, Acknowledge/False-Positive buttons, Notes textarea.
**Data:** `GET /api/alerts/{id}`, `GET /api/geolocation/{ip}` (P1).
**Primary actions:** Acknowledge, Mark as False Positive.
**Secondary actions:** Add Notes.
**Navigation:** Back → previous list (browser history, Section 18).
**Filters/Search:** None (single-record view).
**Charts:** Risk score shown as a radial/gauge indicator (0–100), not a line/bar chart (Section 26).
**Tables:** Flow metadata as a labeled key-value table (not a data grid).
**Maps:** None — "Approximate Location" (P1) is a text/badge with a country/region label and flag icon, never an embedded interactive map (PRD explicitly disclaims attribution; a map would overstate certainty — see Section 24).
**Forms:** Notes textarea + submit.
**Empty/Loading/Error states:** Section 31–33 (notably: geolocation "unavailable for private/reserved IP ranges" empty state).
**Responsive:** Two-column collapses to single column stacked (Risk Score panel moves above Flow Metadata) below 1024px.
**Interactions:** Triage buttons update alert status inline (no full page reload); disabled state once an alert reaches a terminal status (Section 27).

## AlertHistory
**Purpose:** Durable, searchable record of past alerts for review and reporting (PRD §6.7).
**User goal:** Find and review a specific alert or pattern across time.
**Layout:** Page header (title + result count) → FilterBar → Alert table → pagination.
**Components:** FilterBar (date range, category, severity, source IP, status), CyberTable, inline row actions (Ack/FP), pagination control.
**Data:** `GET /api/alerts/history` with query filters.
**Primary actions:** Apply filters, click a row → AlertDetail.
**Secondary actions:** Row-level Acknowledge / False Positive (Section 27).
**Navigation:** Row click → AlertDetail.
**Filters/Search:** FilterBar — Section 28.
**Charts:** None on this page (history is a table-first surface; trend charts are out of PRD scope beyond MainDashboard's own charts).
**Tables:** Primary content — Section 27.
**Maps:** None.
**Forms:** FilterBar controls (Section 28).
**Empty/Loading/Error states:** Section 31–33 (notably: "no alerts match these filters" empty state with a "Clear filters" action).
**Responsive:** Table converts to stacked cards below 768px (Section 35); FilterBar collapses into a "Filters" drawer trigger.
**Interactions:** Filter apply re-queries; column header click sorts (client-side, on the currently loaded page) by Time/Score.

## NetworkGraph (P2)
**Purpose:** At-a-glance view of which source IPs are talking to which destinations and at what risk level (PRD §6.10).
**User goal:** Spot a high-risk source touching many destinations, visually, faster than scanning a table.
**Layout:** Full-bleed canvas panel with a floating legend (top-right) and a details drawer (right-side, appears on node click).
**Components:** Force-directed node/edge canvas, legend (risk-color key), node-details drawer, zoom/pan controls.
**Data:** Aggregated flow/alert data — **flagged as `[ARCHITECTURE GAP]` by `appflow.md`** (no `/api/graph` endpoint currently exists). This page's design is specified so it is ready to implement the moment that endpoint is defined; it is not built against a fabricated endpoint.
**Primary actions:** Click a node to see its detail drawer (source/destination IP, aggregate risk, flow count).
**Secondary actions:** Zoom, pan, filter by risk threshold (client-side slider).
**Navigation:** Node click opens drawer in place (no route change); "View Alerts" in drawer could deep-link to AlertHistory pre-filtered by that IP once the underlying endpoint exists.
**Filters/Search:** Risk-threshold slider (client-side over loaded data).
**Charts:** The graph itself; no additional charts.
**Tables:** None.
**Maps:** None (this is a logical topology graph, not a geographic map).
**Forms:** None beyond the slider.
**Empty/Loading/Error states:** "Network Graph is a post-MVP (P2) feature" placeholder state is the *default* rendered state until the backing endpoint exists — Section 32.
**Responsive:** Canvas is desktop/tablet-oriented; below 768px, render a message directing users to a larger screen rather than a cramped unusable graph.
**Interactions:** Standard pan/zoom/click; details drawer slides in from the right, dismiss via click-outside or close icon.

---

# 20. Dashboard Design

MainDashboard layout, top to bottom, desktop (≥1280px):

```
┌─────────────────────────────────────────────────────────────────────┐
│ StatusBar: [● LIVE MONITORING]  Last updated 22:14:32   [Search] [🔔]│
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│ TOTAL TRAFFIC│ NORMAL       │ SUSPICIOUS   │ THREAT LEVEL          │
│ 12,540 flows │ 11,930 (95%) │ 610 (4.9%)   │ HIGH                  │
├──────────────┴──────────────┴──────────────┴──────────────────────┤
│  TrafficChart (span 8)                    │  ThreatBreakdown (span 4)│
├─────────────────────────────────────────────────────────────────────┤
│  Detection Pipeline: Ingest ▸ Extract ▸ Hybrid ML ▸ Risk ▸ Alert     │
├───────────────────────────────────┬───────────────────────────────┤
│  LiveAlertFeed (span 8)            │  SimulatorControls (span 4)    │
├───────────────────────────────────┴───────────────────────────────┤
│  Top Talkers (optional, span 12 — derived from stats/live)          │
└─────────────────────────────────────────────────────────────────────┘
```

**StatusBar:** left = live/degraded/disconnected pill (Section 34) + "Last updated HH:MM:SS"; right = search input, notification bell, clock. This is the row-level home for `ZeroOutboundBadge`'s *summary* form — a compact `ShieldCheck` + "Zero Outbound" chip — while the full badge lives permanently in the sidebar (Section 16), so the guarantee is visible both persistently (sidebar) and in the page's own status context (header row).

**Detection Pipeline strip:** five equal segments, each a small icon-in-circle + label + one-line caption, connected by a thin dotted cyan line, directly reflecting the real pipeline (PRD §10): **1. Ingest** (traffic capture) → **2. Extract** (feature extraction) → **3. Hybrid ML** (RF + IF scoring) → **4. Risk & Severity** (score → band) → **5. Alert** (explanation + broadcast). This is decorative-but-honest: it visualizes real architecture, not an invented concept, and doubles as a subtle "how this works" explainer for demo audiences (useful given the target user includes hackathon judges).

**PCAP Upload:** `[DESIGN DECISION — fills a documented gap, appflow.md §22 "No frontend component named for PCAP upload"]` Placed as a compact "Upload PCAP" button inside the SimulatorControls panel (third control alongside "Start Normal Traffic" / "Trigger Attack Scenario"), opening a modal with a drag-and-drop `.pcap` dropzone, a file-name confirmation row, and an "Analyze" button. This groups it with the other alternate-ingestion-source controls rather than inventing a fifth top-level page, consistent with `appflow.md`'s own suggestion that it likely belongs inside SimulatorControls or a modal.

---

# 21. KPI Cards

Four-card row, each `radius.md` glass card, `md` padding, fixed min-height 132px.

**Anatomy:**
```
┌──────────────────────────────┐
│ LABEL (H4, uppercase)   [icon]│
│ 12,540                        │  ← KPI Number, textPrimary
│ ▲ 12.5% vs. last hour         │  ← Caption, success/danger colored
│ ▁▂▄▃▅▇▆▄▃▂  (sparkline)        │  ← optional, chart-token colored
└──────────────────────────────┘
```
- **Total Traffic:** icon `Activity`, cyan accent, sparkline in `primary`.
- **Normal Traffic:** icon `CheckCircle2`, `low`/`accent` mint color, sparkline in `accent`.
- **Suspicious/Threats:** icon `AlertTriangle`, color driven by current volume (uses `high` if >0 active, `textMuted` if zero), sparkline in `high`.
- **Threat Level:** not a count — renders the current *maximum active severity band* as a large text label (e.g., "HIGH") in that severity's color, with a one-line caption ("Threat level is high — review active alerts") instead of a numeric trend; background gets a very subtle severity-tinted tone (8% opacity) so this card visually differs from the three numeric cards.

Hover: `borderStrong` border, `shadow.md`, no scale/transform (avoid gimmicky lift effects).

---

# 22. Charts & Graphs

All charts render via `recharts` (per `architecture.md` §23's named option) with the following unified styling:

### Line Charts (TrafficChart)
- Stroke: 2px, `primary` (#00D9E0) for the main "traffic" series; secondary "anomalous/threat" series in `critical` at 2px.
- Glow: subtle `drop-shadow(0 0 6px rgba(0,217,224,0.35))` on the line itself, none on gridlines.
- Grid: horizontal only, 1px, `border` token, dashed (4 2).
- Axis: JetBrains Mono 11px, `textMuted`, ticks every ~10 min of the selected window; Y-axis abbreviated (12K not 12000).
- Tooltip: `surfaceElevated` background, `radius.sm`, `shadow.md`, monospace value + sans label, appears on hover with a vertical crosshair guide line in `border` token.
- Hover: crosshair + highlighted dot (6px, filled `primary`, 2px white-ish ring) at the nearest data point.
- Data points: hidden by default (line-only), revealed on hover per the point above.
- Area fill: linear gradient from `primary` at 18% opacity (top) to transparent (bottom), applied beneath the primary line only.

### Bar Charts (used in Top Talkers / category breakdowns where a bar-list fits better than a table)
- Bar width: dynamic to container, min 8px, max 32px, `radius.xs` on the leading (right) end only for horizontal bars.
- Radius: 4px on outer corners.
- Spacing: 8px (`sm`) between bars.
- Labels: value in JetBrains Mono 12px at the bar's end; category name in Inter 13px to the left (horizontal bar list) as seen in the Top Talkers pattern from Reference A.
- Hover: bar brightens by raising fill opacity from 85%→100% and shows a tooltip with exact value.

### Area Charts
- Same stroke/grid/tooltip system as line charts.
- Gradient: top-of-fill at 22% of the series color, fading to 0% by 70% of the chart height.
- Border: 1.5px solid at full series-color opacity along the top edge of the fill.
- Glow: none additional beyond the line-charts' subtle drop-shadow (avoid double-glow stacking, Section 12's "one glow per element" rule).

### Donut Charts (ThreatBreakdown, category distribution)
- Thickness: ring width = 18% of outer radius (matches Reference B's proportion — not too thin/technical, not too thick/childish).
- Center value: large JetBrains Mono number (28px, `textPrimary`) + small Inter caption beneath ("Total Flows"), replicating both references' centered-total pattern.
- Legend: right-aligned or below (responsive), each entry = colored dot (8px) + category label (Inter 13px) + value/percentage (JetBrains Mono 12px, `textMuted`).
- Labels: no on-slice labels for slices <5% (avoid clutter); larger slices may show a percentage inline in `textOnAccent`-appropriate contrast.
- Hover: slice lifts via 4% opacity increase + slight outward offset (6px max), tooltip shows exact count.

All charts share one rule: **only one visual accent glows at a time on a given chart** — the line/area glow is the only glow present; grid, axis, and legend never glow.

---

# 23. Network Visualization

Scoped to **NetworkGraph (P2)** only, per PRD §6.10 — no other screen gets a network topology visualization (avoiding the brief's "no decorative network visualizations" rule).

- **Nodes:** circle, radius scaled 8–24px by aggregate flow volume through that IP; fill color = the node's *current maximum risk severity* using the severity palette (Section 7); a thin `border` stroke separates nodes from the dark canvas.
- **Connections (edges):** line width scaled 1–6px by traffic volume between the pair; color = edge's own risk severity (may differ from either endpoint's overall color); default opacity 55%, rising to 100% on hover/selection.
- **Source/Destination distinction:** subtle directional arrowhead at the destination end (never implies a return path — this is a *display* of one-way flow direction, consistent with the product's unidirectional nature, not a UI suggesting bidirectionality).
- **Normal / Suspicious / Malicious traffic states:** mapped directly onto the severity palette — informational/low nodes render in muted `low` teal, medium in `medium` amber, high/critical in `high`/`critical` with a soft `glow.warning`/`glow.critical` respectively (the *only* place outside alert cards that severity glow appears).
- **Node states:** default, hover (border brightens to `borderFocus`), selected (persistent `borderFocus` + drawer open).
- **Animation:** on new-edge/new-node arrival (if graph is live), a brief 400ms fade-and-settle — no continuous idle animation (avoids a "busy/gamey" feel).
- **Labels:** IP address in JetBrains Mono 11px appears only on hover/selection (labels-always-on would clutter a graph of any real size).
- **Tooltips:** on edge hover, show src → dst, protocol, flow count, max severity.
- **Zoom/Pan:** standard scroll-to-zoom + drag-to-pan; a "Reset View" button in the top-left.
- **Selection:** click a node → right-side drawer (Section 19's NetworkGraph subsection).

---

# 24. Maps

Per PRD/appflow, the only geographic element in the entire product is **AlertDetail's P1 "Approximate Location"** field — there is no dashboard-wide geographic map, consistent with the source documents (no map component or endpoint beyond `GET /api/geolocation/{ip}` is specified anywhere).

**Design:** a compact card, not an embedded map widget:
```
┌────────────────────────────────┐
│ 📍 APPROXIMATE LOCATION          │
│ 🇩🇪  Frankfurt, Germany (approx.) │
│ Based on IP geolocation —        │
│ not attacker attribution.         │
└────────────────────────────────┘
```
Always includes the disclaimer line in Caption/`textMuted` styling, directly reflecting PRD §9's disclaimer requirement ("does not perform definitive attribution"). If geolocation lookup fails or the IP is private/reserved, the card shows an empty state (Section 32) instead of a blank/missing field.

---

# 25. Threat Visualization

Beyond NetworkGraph (Section 23) and severity badges (Section 26), "threat visualization" on MainDashboard is carried by:
- **ThreatBreakdown donut** (Section 22): Normal vs. Suspicious/threat volume + category split.
- **Threat Level KPI card** (Section 21): current maximum active severity, prominent.
- **LiveAlertFeed** (below): the primary real-time threat-visualization surface — a continuously updating list rather than a chart, matching how PRD §11 actually describes it ("live-updating list of recent alerts with severity color-coding").

**LiveAlertFeed anatomy** (list, not table — max ~8 visible rows, internally scrollable):
```
┌────────────────────────────────────────────────────────┐
│ [CRITICAL] DDoS-like Volumetric Behavior      22:13:45  │
│ 192.168.1.45 → 10.0.0.5 · TCP · Score 92          →     │
├────────────────────────────────────────────────────────┤
│ [HIGH] Port Scanning                          22:11:32  │
│ 192.168.1.23 → 8.8.8.8 · TCP · Score 71           →     │
└────────────────────────────────────────────────────────┘
```
Each row: left 3px severity-colored bar, severity pill, category name (bold), timestamp (right, Caption/mono), second line = src → dst (mono) · protocol · score, trailing chevron. New rows animate in at the top (Section 37). Clicking a row navigates to AlertDetail.

---

# 26. Threat Details

Covers **AlertDetail**'s risk-score and evidence presentation specifically (page layout is in Section 19).

**Risk Score panel:** radial gauge, 0–100, arc colored by severity band (a gradient is *not* used across the arc — the whole arc renders in the single severity color that band belongs to, keeping the "severity = one specific color" rule intact), large JetBrains Mono number centered (e.g., "92"), severity label beneath ("CRITICAL").

**Category badge:** pill, severity-colored background at 15% opacity + full-opacity text and 1px border, icon + label (e.g., "🛡 DDoS-like Volumetric Behavior"). When the supervised model's confidence is below threshold, renders as "Unknown Anomaly" per PRD §6.9/FR-011 — same visual treatment, using the `informational` color family to visually distinguish "named category" from "flagged but unclassified."

**Confidence indicator:** small inline row beneath the category badge — numeric percentage (JetBrains Mono) + a thin 4px-tall horizontal progress bar in the category's severity color, directly echoing Reference B's inline-confidence-bar pattern.

**Explanation panel:** a distinct card, `H3` heading "Why this was flagged," body text in Inter 14px (plain-language, 2–3 lines per PRD §6.5), followed by a monospace "Evidence" sub-block listing the specific contributing features (e.g., `unique_dst_port_count: 47 (baseline: 3–6)`), rendered in a `surfaceSunken` code-block style so it's visually distinct from the plain-language summary above it — this satisfies both the requirement for a human-readable explanation *and* access to the raw evidence, without conflating the two.

**Flow Metadata panel:** two-column key–value list, all values in JetBrains Mono: Source IP, Destination IP, Source Port, Destination Port, Protocol, Flow Duration, Total Packets, Total Bytes, Window Start/End.

**Recent Source History (P1):** compact mini-list of the last few alerts from the same source IP, each row = timestamp + category + severity dot, click navigates to that AlertDetail.

---

# 27. Tables

Two table contexts: **AlertHistory**'s primary table and (compact) **LiveAlertFeed** which is a list, not a table (Section 25).

**CyberTable pattern (AlertHistory):**
- Header row: `surfaceSunken` background, H4 styling (uppercase, `textMuted`), sortable columns show a small chevron on hover/active.
- Columns (per PRD §11): Time (mono) | Source IP (mono) | Category (label + severity dot) | Score (mono, colored by severity) | Status (pill: New / Acknowledged / False Positive — reflecting the three-state schema `appflow.md` documents as the actual MVP lifecycle) | Actions (inline Ack/FP icon buttons).
- Row: 1px bottom `border`, 48px min-height, hover = `surfaceSunken` background tint.
- Row actions: two small icon buttons (checkmark = Acknowledge, X = False Positive) that appear on row hover (desktop) or are always visible (mobile card view) — clicking either updates the row's Status pill in place with a brief 200ms fade, no full reload.
- Pagination: bottom-right, "Showing 1–25 of 342" + prev/next, page-size selector.
- Sorting: client-side on Time/Score for the currently loaded page (no claim of full-dataset server-side sort unless the endpoint documents it — it doesn't, per `appflow.md` §20, so this is scoped conservatively).

---

# 28. Search & Filters

**FilterBar (AlertHistory):**
```
[ Date range ▾ ]  [ Category ▾ ]  [ Severity ▾ ]  [ Source IP: ___ ]  [ Status ▾ ]   [Apply] [Clear]
```
- Each dropdown: `surface` background, `radius.sm`, opens a `surfaceElevated` popover.
- Severity filter uses the severity color as a small dot next to each option label (Low/Medium/High/Critical/Informational).
- Source IP: free-text input, monospace font (it's an IP), inline validation (basic IPv4/IPv6 shape check) — client-side only, since the exact query-param contract isn't specified server-side (`appflow.md` §20 flags this as unspecified; the filter degrades gracefully to "no results" rather than erroring if the backend rejects a malformed param).
- **Apply** button: `primary`-filled, triggers `GET /api/alerts/history` with the current filter state.
- **Clear** button: text-only/ghost style, resets all filters and re-queries with none.
- Active filter count badge appears on the FilterBar's mobile-collapsed trigger ("Filters (3)").

Global header search (Section 17) is a lighter-weight, client-side-only IP/ID filter over already-loaded feed/table data — visually a simple text input with a search icon, no dropdown.

---

# 29. Forms

Only two forms exist in the product, both intentionally minimal:

1. **SimulatorControls:** scenario `<select>` (Port Scan / Network Scan / DDoS-like Flood / Exfiltration / Beaconing / Unknown Anomaly, per PRD §9) + Start/Stop buttons for both "Normal Traffic" and the selected attack scenario, laid out as two labeled sub-groups within one card. Selecting a scenario is required before "Start Attack Scenario" enables (per `appflow.md`'s documented frontend validation).
2. **Notes (AlertDetail):** a single `<textarea>`, 3 rows default (auto-grows to 6), placeholder "Add investigation notes...", submit button disabled until non-empty, submits via `POST /api/alerts/{id}/notes`.

**Input styling (shared):** `surfaceSunken` background, `border` default / `borderFocus` on focus (2px), `radius.sm`, 40px height for single-line inputs, Inter 14px text, `textMuted` placeholder.

---

# 30. Alerts & Notifications

Two distinct concepts, not to be confused:
- **Threat Alerts** (the product's core domain object — Sections 25–26) are content, not UI chrome — they live in LiveAlertFeed/AlertHistory/AlertDetail.
- **System notifications** (UI chrome — toasts) confirm the *result of a user action*: "Alert acknowledged," "Note saved," "PCAP analysis started," "Simulator stopped." These are the only toasts in the product (per `appflow.md`'s many `[ASSUMPTION — not specified]` markers on action feedback, this spec makes the minimal, professional choice: a small toast, not a modal, not a full banner).

**Toast style:** bottom-right stack, `surfaceElevated` background, `radius.sm`, `shadow.md`, left 3px accent bar (`success` for confirmations, `danger` for failures), auto-dismiss after 4s, manually dismissible via a close icon. Max 3 stacked; older ones collapse/dismiss.

**Header notification bell (Section 17):** badge count = current unacknowledged High+Critical alerts; clicking opens a small popover listing the 5 most recent such alerts (same row styling as LiveAlertFeed, compact), with a "View All" link to AlertHistory pre-filtered to High+Critical/Unacknowledged.

---

# 31. Loading States

`[DESIGN DECISION — fills a documented gap, appflow.md §20 "No loading/empty/error state designs"]` — a UX pass was explicitly flagged as needed; this section is that pass, applied conservatively (no new functionality, only presentation of existing states).

- **Initial page load (any page):** skeleton screens matching each page's actual layout grid — KPI cards render as pulsing gray blocks at their real dimensions, chart areas render as a pulsing rounded rectangle, table rows render as 5 skeleton rows. No spinners-only states on data-heavy pages (skeletons preserve layout and feel faster).
- **Live data refresh (WebSocket-driven):** no loading indicator at all for incremental updates — counters/charts update in place (Section 37 covers the transition animation). A loading indicator here would be noisy given the sub-2-second update cadence the product targets.
- **Action-in-flight (Acknowledge, False Positive, Notes submit, simulator start, PCAP upload):** button enters a disabled state with a small inline spinner replacing its icon; label stays the same text (e.g., "Acknowledge" button shows spinner but keeps its label) to avoid layout shift.
- **Skeleton color:** `surfaceSunken` base with a subtle shimmer sweep in `border`-token opacity, 1.5s loop.

---

# 32. Empty States

- **LiveAlertFeed, no alerts yet:** centered icon (`ShieldCheck`, `accent` color) + "No active threats — traffic is nominal" (Body, `textSecondary`) + small caption "New alerts will appear here in real time."
- **AlertHistory, no results for current filters:** centered `Search`-style icon + "No alerts match these filters" + a **Clear filters** text button.
- **AlertHistory, no alerts ever recorded (fresh install):** centered `ShieldCheck` icon + "No alerts recorded yet — start the simulator or connect a live traffic source from the Dashboard" with a button linking back to MainDashboard.
- **NetworkGraph (P2, current default state until its endpoint exists):** centered `Network` icon (`textMuted`) + "Network Graph is coming soon" + one-line note that this view visualizes source→destination risk relationships once enabled — a calm placeholder rather than an error, since this is a documented `[ARCHITECTURE GAP]`, not a product bug.
- **AlertDetail, geolocation unavailable:** within the Approximate Location card, "Location unavailable for private or reserved IP ranges" (Caption, `textMuted`), icon dimmed.
- **AlertDetail, no recent source history:** "No other alerts recorded for this source" (Caption, `textMuted`).

All empty states share: centered content, icon size 32px, `textMuted`/`textSecondary` text, generous vertical padding (min 64px), never an error color (empty ≠ broken).

---

# 33. Error States

- **WebSocket disconnected:** StatusBar pill switches from `[● LIVE MONITORING]` (cyan, pulsing dot) to `[◌ RECONNECTING...]` (amber, `warning` color) while the client retries; if retries are exhausted, `[✕ DISCONNECTED]` (danger/`critical` color) with a manual "Retry" button. Per `architecture.md`'s WS-disconnect→polling fallback, once polling engages the pill instead reads `[◐ POLLING]` in `warning` color with a caption "Live updates paused — refreshing every 10s."
- **ML pipeline degraded (FR-021):** StatusBar/sidebar system-status footer shows `[◐ DEGRADED]` in `warning` color, caption "Detection running in degraded mode — some alerts may be delayed," never blocking the rest of the UI (ingestion/dashboard must keep functioning per the requirement).
- **API request failure (e.g., filter apply, action submit):** inline error banner within the relevant card/panel — `danger`-tinted background at 8% opacity, `AlertTriangle` icon, one-line message ("Couldn't save note — try again"), never a full-page error unless the entire app fails to load its initial shell.
- **App-shell-level failure (status/stats endpoints unreachable on first load):** full-page state — centered `WifiOff` icon, "Can't reach OneWay Sentinel's backend," "Retry" button — the only true full-page error state in the product.
- **PCAP upload failure (invalid file, processing error):** inline within the upload modal, `danger`-tinted message beneath the dropzone, dropzone remains active for a retry.

---

# 34. Real-Time UI

- **Connection states:** Live (cyan pulsing dot, `glow.cyan`) → Reconnecting (amber, no glow, spin icon) → Polling fallback (amber, static dot + "10s" cadence caption) → Disconnected (red, static dot). Defined once in the StatusBar/sidebar-footer component and reused identically wherever connection state is shown.
- **Counters:** KPI numbers use a brief count-up/roll transition (150–250ms) when their value changes via WS push, rather than an instant jump — communicates "this just moved" without being distracting.
- **Charts:** TrafficChart's line extends smoothly as new data points arrive (no full re-draw flash); ThreatBreakdown donut segments animate their arc-length change over ~300ms when category proportions shift.
- **New alert arrival:** covered in Section 37 (Animation).
- **Latency expectation surfaced to the user:** none needed as an explicit UI element — the sub-2-second target (PRD FR-020) is an implementation SLA, not something the UI needs to display as a number; it's felt through the responsiveness of the states above.

---

# 35. Responsive Design

| Element | Desktop (≥1280px) | Laptop (1024–1279px) | Tablet (768–1023px) | Mobile (<768px) |
|---|---|---|---|---|
| Sidebar | 260px fixed, expanded | 72px icon-only (hover-expand) | Hidden, hamburger-triggered overlay drawer | Same as tablet |
| Header | Full (title, search, bell, clock) | Same, search may shrink | Search collapses to icon-triggered overlay | Title + hamburger + bell only; clock/search hidden |
| KPI Cards | 4-across | 2×2 | 2×2, reduced padding | 1-per-row, stacked |
| Charts | Side-by-side (8/4 span) | Side-by-side, narrower | Stacked, full-width each | Stacked, full-width, reduced height (180px) |
| Tables (AlertHistory) | Standard table | Standard table | Standard table, horizontal scroll if needed | Converts to stacked "card" rows: each alert becomes a mini-card with the same fields as columns, labeled |
| FilterBar | Inline row | Inline row, wraps to 2 lines if needed | Collapses into "Filters" button → drawer | Same as tablet |
| NetworkGraph | Full canvas + drawer | Full canvas + drawer | Full canvas, drawer becomes bottom sheet | Placeholder message directing to larger screen (Section 19) |
| Threat details (AlertDetail) | Two-column | Two-column, narrower | Single column, gauge panel first | Single column |

---

# 36. Accessibility

- **Contrast:** all text/background pairs meet WCAG AA (4.5:1 body text, 3:1 large text/UI components) — verified token-by-token in Section 7's notes; severity badges always pair a colored background with sufficiently contrasting text (never color-on-color at low contrast).
- **Keyboard navigation:** full tab order through sidebar → header controls → page content → cards/rows/buttons in visual order; all interactive elements (nav items, KPI cards' info affordance if any, table rows, buttons, filter controls) are reachable and operable via Enter/Space.
- **Focus states:** every focusable element gets a visible 2px `borderFocus` (cyan) outline with 2px offset — never `outline: none` without a replacement.
- **Semantic HTML:** nav landmark for sidebar, `<table>` for AlertHistory (not div-grids), `<button>` for actions (not clickable divs), form labels properly associated with inputs.
- **Screen reader support:** live-region (`aria-live="polite"`) on LiveAlertFeed so new alerts are announced without stealing focus; status pill changes (Live/Degraded/Disconnected) also live-region announced; icons that carry meaning (severity, status) always have an accompanying visually-hidden text label for screen readers even when a visible text label is also present.
- **Accessible charts:** every chart has an adjacent (visually hidden or expandable) data-table equivalent, or at minimum a text summary ("Traffic trending up 12.5% over the last hour, peak at 10:22") — satisfies non-visual access to the same information the chart conveys.
- **Accessible tables:** proper `<th scope="col">` headers, sortable-column state exposed via `aria-sort`.
- **Non-color severity indicators:** every severity instance (badge, KPI, node, alert row) pairs color with an icon (Section 14) and a text label — never color alone, satisfying both the accessibility requirement and the brief's explicit "do not rely only on color" rule for threat states.

---

# 37. Animation & Motion

All motion is subtle, purposeful, and short (150–400ms), using an ease-out curve for entrances and ease-in-out for state changes. No looping decorative animation anywhere except the two explicitly-stateful pulses below.

- **New alert arrival (LiveAlertFeed):** new row slides down from the top with a 300ms ease-out + fades in; if Critical, the row's left-edge glow (`glow.critical`) pulses (opacity 100%→60%→100%) exactly twice over 1.2s, then settles to steady — draws the eye once without becoming a persistent distraction.
- **Live status dot:** steady 2s-cycle soft pulse on the "LIVE" dot only, using `glow.cyan` opacity oscillation — the single "idle/ambient" animation permitted in the product, since it communicates "still connected," which is exactly the ongoing thing it needs to communicate.
- **Hover:** border color shift + shadow elevation change, 150ms, on all interactive cards/buttons/rows — no scale/transform.
- **Focus:** instant outline appearance (no transition delay — accessibility takes priority over polish here).
- **Card transitions (route change):** content area cross-fades (200ms) rather than sliding, since the sidebar/header stay fixed and only content swaps.
- **Threat alerts (Critical toast/banner, if the notification bell popover is open when one arrives):** brief 150ms flash of the bell icon's badge color, not a screen-wide flash.
- **Chart updates:** covered in Section 34 — smooth extend/redraw, no flash-to-white or hard cuts.
- **Network activity (NetworkGraph):** new node/edge fade-and-settle over 400ms (Section 23); no continuous "flowing packets" animation along edges (decorative, not evidentiary — avoided per the brief's caution against decorative network visualizations).
- **Page transitions:** 200ms cross-fade only, as above; no page-slide effects (keeps the tool feeling like an instrument, not a marketing site).

---

# 38. Component Library

Scoped to components with a real basis in `architecture.md`'s named files/PRD features — no invented components.

```
Layout
  AppShell, Sidebar, Header, PageContainer

Page components (architecture.md frontend/src/pages/)
  MainDashboard, AlertDetail, AlertHistory, NetworkGraph

Named components (architecture.md frontend/src/components/)
  StatusBar, ZeroOutboundBadge, TrafficChart, ThreatBreakdown,
  LiveAlertFeed, SimulatorControls, FilterBar

Derived/supporting components (implied by the above, not separately named
in architecture.md, but required to build them — kept minimal)
  CyberCard        — base glass card wrapper used by every panel
  CyberPanel       — larger section wrapper (adds H2 header slot)
  CyberButton      — primary/secondary/ghost/destructive variants
  CyberInput       — text input, used in FilterBar/Notes/Search
  CyberBadge       — generic pill badge (status, category)
  SeverityBadge    — CyberBadge specialization bound to the severity palette
  ThreatBadge      — category-labeled badge (icon + name), used in feed/table/detail
  RiskGauge        — radial 0–100 score indicator (AlertDetail)
  StatusPill       — Live/Degraded/Disconnected/Polling indicator
  KPICard          — CyberCard specialization for MainDashboard's stat row
  CyberTable       — AlertHistory's data table
  Toast / ToastStack — system notification chrome (Section 30)
  Skeleton         — loading placeholder (Section 31)
  EmptyState       — reusable empty-state layout (Section 32)
  Modal            — PCAP upload dialog
  NetworkGraphCanvas — NetworkGraph's node/edge renderer
```

---

# 39. Design Tokens

```yaml
colors:
  background: "#0A0E17"
  backgroundGradientTop: "#131B2E"
  surface: "#101828"
  surfaceElevated: "#16202F"
  surfaceSunken: "#0C121C"
  sidebarBg: "#0B111C"
  headerBg: "#0D1420"
  navActiveBg: "#14304A"
  border: "rgba(255,255,255,0.08)"
  borderStrong: "rgba(255,255,255,0.15)"
  borderFocus: "#00D9E0"
  primary: "#00D9E0"
  primaryMuted: "rgba(0,217,224,0.20)"
  secondary: "#6C7BFF"
  accent: "#00FFC2"
  textPrimary: "#E9EEF5"
  textSecondary: "#9AACC2"
  textMuted: "#647089"
  textDisabled: "#3E4A5E"
  informational: "#6C7BFF"
  low: "#00C2A8"
  medium: "#F5A524"
  high: "#FF7A45"
  critical: "#FF3B5C"
  success: "#2ED47A"
  warning: "#F5A524"
  danger: "#FF3B5C"
  info: "#00D9E0"

spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"

radius:
  xs: "4px"
  sm: "6px"
  md: "10px"
  lg: "16px"
  full: "999px"

shadows:
  sm: "0 1px 2px rgba(0,0,0,0.4)"
  md: "0 4px 16px rgba(0,0,0,0.35)"
  lg: "0 12px 32px rgba(0,0,0,0.45)"

glow:
  cyan: "0 0 0 1px rgba(0,217,224,0.25), 0 0 20px rgba(0,217,224,0.12)"
  mint: "0 0 20px rgba(0,255,194,0.10)"
  warning: "0 0 20px rgba(245,165,36,0.14)"
  critical: "0 0 24px rgba(255,59,92,0.18)"

fonts:
  sans: "'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif"
  mono: "'JetBrains Mono', 'IBM Plex Mono', 'SFMono-Regular', Menlo, monospace"

breakpoints:
  mobile: "480px"
  tablet: "768px"
  laptop: "1024px"
  desktop: "1280px"
```

---

# 40. Tailwind CSS Implementation Guidance

Extend `tailwind.config.js` with the Section 39 tokens under `theme.extend`, then define reusable component classes via `@layer components` so no page repeats long utility strings:

```css
@layer components {
  .cyber-card {
    @apply relative rounded-[10px] border border-white/[0.08] bg-surface/70
           backdrop-blur-xl p-4 shadow-sm;
  }
  .cyber-panel {
    @apply cyber-card p-6;
  }
  .cyber-button-primary {
    @apply rounded-md bg-primary text-[#04141A] font-semibold text-sm px-4 py-2
           hover:brightness-110 transition disabled:opacity-40 disabled:pointer-events-none;
  }
  .cyber-button-ghost {
    @apply rounded-md border border-white/[0.08] text-textSecondary text-sm px-4 py-2
           hover:border-white/[0.15] hover:text-textPrimary transition;
  }
  .cyber-input {
    @apply rounded-md bg-surfaceSunken border border-white/[0.08] text-sm text-textPrimary
           px-3 h-10 placeholder:text-textMuted focus:outline-none focus:border-primary
           focus:ring-2 focus:ring-primary/30;
  }
  .cyber-badge {
    @apply inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold border;
  }
  .cyber-table {
    @apply w-full text-sm border-collapse;
  }
  .cyber-table th {
    @apply text-left text-xs uppercase tracking-wider text-textMuted bg-surfaceSunken
           px-3 py-2 font-bold;
  }
  .cyber-table td {
    @apply px-3 py-3 border-b border-white/[0.06] font-mono text-textPrimary;
  }
  .cyber-glow-cyan   { box-shadow: 0 0 0 1px rgba(0,217,224,0.25), 0 0 20px rgba(0,217,224,0.12); }
  .cyber-glow-critical { box-shadow: 0 0 24px rgba(255,59,92,0.18); }

  .threat-informational { @apply cyber-badge text-informational border-informational/30 bg-informational/10; }
  .threat-low      { @apply cyber-badge text-low border-low/30 bg-low/10; }
  .threat-medium   { @apply cyber-badge text-medium border-medium/30 bg-medium/10; }
  .threat-high     { @apply cyber-badge text-high border-high/30 bg-high/10; }
  .threat-critical { @apply cyber-badge text-critical border-critical/30 bg-critical/10 cyber-glow-critical; }
}
```

Every page/component composes these classes rather than repeating raw utilities — e.g., a KPI card is `<div className="cyber-card">...</div>`, never a fresh 15-class string per instance.

---

# 41. React Component Architecture

```
frontend/src/
├── components/
│   ├── layout/          AppShell.jsx, Sidebar.jsx, Header.jsx, PageContainer.jsx
│   ├── status/           StatusBar.jsx, ZeroOutboundBadge.jsx, StatusPill.jsx
│   ├── charts/           TrafficChart.jsx, ThreatBreakdown.jsx
│   ├── alerts/           LiveAlertFeed.jsx, SeverityBadge.jsx, ThreatBadge.jsx,
│   │                      RiskGauge.jsx
│   ├── simulator/        SimulatorControls.jsx, PcapUploadModal.jsx
│   ├── history/          FilterBar.jsx, CyberTable.jsx
│   ├── graph/             NetworkGraphCanvas.jsx
│   ├── ui/                CyberCard.jsx, CyberPanel.jsx, CyberButton.jsx, CyberInput.jsx,
│   │                        CyberBadge.jsx, Modal.jsx, Toast.jsx, Skeleton.jsx, EmptyState.jsx
├── pages/
│   ├── MainDashboard.jsx
│   ├── AlertDetail.jsx
│   ├── AlertHistory.jsx
│   └── NetworkGraph.jsx
├── api/                  client.js, ws.js   (per architecture.md §3, unchanged)
├── hooks/                 useLiveAlerts.js (wraps ws.js), useAlertHistory.js,
│                           useStatus.js, useStats.js
└── styles/                tailwind.css, tokens (Section 39 values)
```

State: a WS-driven context (`architecture.md` §12) feeds `useLiveAlerts`/`useStatus`/`useStats`; AlertHistory and AlertDetail use plain fetch-on-mount + refetch-on-filter-change (no need for the WS context on those pages beyond an optional "new alerts available" banner if desired — not required by PRD, so omitted to avoid inventing functionality).

---

# 42. Reference-to-Design Mapping

| Reference element | Source | Adopted as | Section |
|---|---|---|---|
| KPI-row → chart-row → live-table → alert-table skeleton | Reference A | MainDashboard grid layout | 20 |
| Inline sparkline in stat cards | Reference A | KPI Card sparkline | 21 |
| Donut with centered total + legend | Both | ThreatBreakdown | 22 |
| Top Talkers horizontal-bar list | Reference A | Optional Top Talkers panel | 20, 22 |
| Sidebar bottom-pinned status panels | Reference A | Sidebar system-status footer + ZeroOutboundBadge | 16 |
| "Block IP" row action | Reference A | **Adapted, not copied** — becomes Acknowledge/False Positive (detect-only product, no blocking capability exists) | 27 |
| Dark near-black canvas with top gradient | Reference B | Section 15 app shell background | 15 |
| Glass stat cards with soft glow shadow | Reference B | CyberCard / KPI Card | 13, 21 |
| 5-step "Detection Pipeline" strip | Reference B | Adopted directly — maps onto the real pipeline (PRD §10) | 20 |
| Donut with centered total (SENTINEL-X variant) | Reference B | ThreatBreakdown | 22 |
| Live activity feed with icon chips | Reference B | LiveAlertFeed row pattern | 25 |
| Severity pill badges | Reference B | SeverityBadge / ThreatBadge | 26, 38 |
| Inline confidence % + progress bar | Reference B | AlertDetail confidence indicator | 26 |
| World-map / flowing-globe hero | Reference B | **Not adopted** — no PRD/architecture basis for a geographic hero visual | 5 |

---

# 43. Design DOs and DON'Ts

**DO**
- Pair every severity indicator with color + icon + text.
- Keep the zero-outbound badge permanently visible.
- Use monospace for every IP/port/protocol/ID/timestamp value.
- Treat glow as a severity/liveness signal, applied once per element, never stacked.
- Design every state a screen can actually be in (loading/empty/error), not just the happy path.
- Keep action buttons limited to analyst triage — never imply the system can block or act on the network.

**DON'T**
- Don't add a full RBAC/login UI — MVP has none (PRD §24: auth is P2).
- Don't invent a global geographic map — only AlertDetail's disclaimed "Approximate Location" exists.
- Don't add a "Block IP" or any active-response control — this is a detect-only product (PRD Non-Goals).
- Don't animate anything continuously except the Live status pulse.
- Don't apply glass/blur to the sidebar or header — reserve it for content cards.
- Don't invent new API endpoints in the frontend to make a screen "feel complete" (e.g., NetworkGraph's data source is genuinely unresolved — build it against the documented gap, not a fabricated route).
- Don't let severity color leak into non-severity UI (e.g., a "Critical" red must never appear as a generic error color for something unrelated to threat severity — use `danger`, a separate token, for that).

---

# 44. Frontend Implementation Checklist

- [ ] Tailwind config extended with Section 39 tokens; `@layer components` classes from Section 40 added.
- [ ] `Inter` and `JetBrains Mono` fonts loaded (self-hosted or via a privacy-respecting method — no third-party font CDN assumption made here, left to the implementer per hackathon offline-demo constraint, PRD §19).
- [ ] AppShell + Sidebar + Header built per Sections 15–17, with React Router routes from Section 18.
- [ ] MainDashboard assembled from StatusBar, 4× KPICard, TrafficChart, ThreatBreakdown, Detection Pipeline strip, LiveAlertFeed, SimulatorControls (+ PCAP modal), per Section 20.
- [ ] WS context (`useLiveAlerts`) wired to `/ws/alerts`, with reconnect/polling-fallback states per Section 33.
- [ ] AlertDetail built with RiskGauge, ThreatBadge, explanation panel (plain-language + evidence sub-block), flow metadata table, geolocation card, recent-history list, triage actions — Section 19/26.
- [ ] AlertHistory built with FilterBar + CyberTable + pagination + row actions — Section 19/27/28.
- [ ] NetworkGraph built as a feature-flagged nav item, defaulting to the "coming soon" empty state (Section 32) until its backing endpoint is defined — Section 19/23.
- [ ] All severity instances use SeverityBadge (color + icon + text) — never color-only.
- [ ] Loading skeletons implemented for every page's initial load (Section 31); no spinner-only states on data-heavy screens.
- [ ] Empty states implemented for every documented case in Section 32.
- [ ] Toast system implemented for action confirmations only (Section 30) — not used for threat alerts themselves.
- [ ] Accessibility pass: focus rings, aria-live on LiveAlertFeed, chart text-summaries, table semantics (Section 36).
- [ ] Responsive behavior verified at all four breakpoints (Section 35), including AlertHistory's table→card conversion on mobile.
- [ ] Animation durations audited against Section 37 — nothing loops except the Live status pulse.
- [ ] Verified no UI element implies active response/blocking capability anywhere in the app (final pass against Section 43's DON'Ts).
