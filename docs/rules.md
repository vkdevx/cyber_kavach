# rules.md — OneWay Sentinel Engineering Constitution

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)
**Governs:** All human and AI-agent contributions to this codebase (Claude, Claude Code, Cursor, Copilot, Antigravity, or any other agent/developer).
**Source documents this file converts into enforceable rules:**
| Doc | Role |
|---|---|
| `prd.md` (`master-prd.md`) | Product & business requirements |
| `architecture.md` (`oneway_sentinel_architecture.md`) | Technical implementation decisions |
| `appflow.md` | User behavior and application flow |
| `design.md` | Visual and interaction system |
| `rules.md` (this file) | How the above gets implemented and maintained |

This file does not restate those documents. Where it summarizes them, the summary exists only to make a rule enforceable — the source document remains authoritative for the underlying requirement. If this file and a source document ever appear to disagree, **Section 2 (Documentation Hierarchy)** and **Section 47 (Rule Priority)** govern, not this file's convenience.

---

## 1. Project Constitution

These principles are non-negotiable. Every other section in this file is an application of one or more of them.

1. **Requirements before implementation.** No code is written to satisfy a need that isn't traceable to `prd.md`, `architecture.md`, `appflow.md`, or `design.md`. If a requirement seems obviously necessary but isn't written down anywhere, that is a documentation gap to flag (Section 46), not a license to invent silently.
2. **Consistency before novelty.** OneWay Sentinel already has a defined architecture (modular monolith, one-directional queue), a defined visual language (Sections 7–14 of `design.md`), and a defined flow (`appflow.md`). A new, "better" pattern is never introduced mid-project without going through Section 34/36 (documentation sync / change management).
3. **Reuse before duplication.** Before writing a new component, service, utility, hook, or model, search the existing codebase for something that already does it or is close enough to extend. Create a new abstraction only when the existing one cannot satisfy the requirement without introducing inappropriate coupling (e.g., forcing `backend/risk/` to import from `network/`).
4. **Security before convenience.** This product's entire reason for existing is a security guarantee (zero return traffic through a data-diode-protected link, PRD §3/§18, architecture.md §18). Any shortcut that risks that guarantee — a debug endpoint, a "temporary" send capability, a convenience socket — is prohibited outright, not "flagged for later."
5. **Explicit behavior before assumptions.** If `appflow.md` marks something `[ASSUMPTION]` or `[ARCHITECTURE GAP]` (see Section 20 of `appflow.md`), an implementer does not silently pick a behavior. Follow Section 46 of this file.
6. **Minimal changes before large refactors.** A bug fix or feature addition touches the smallest set of files that correctly solves the problem. Large refactors are governed by Section 36 and require an explicit reason.
7. **Documentation and implementation must remain synchronized.** If code changes something described in a source document, that document is updated in the same change set (Section 34).
8. **Existing working functionality must not be broken.** Especially the zero-outbound guarantee (FR-001, FR-019) and the sub-2-second alert latency (FR-020) — these are the product's two most demo-critical, judge-visible properties and must be protected by every change (Section 31 Regression Prevention).

---

## 2. Documentation Hierarchy

| Area | Source of Truth |
|---|---|
| Product requirements, business rules, success metrics, MVP scope | `prd.md` |
| Technical stack, module boundaries, data flow, DB schema, deployment | `architecture.md` |
| Screen-to-screen navigation, user actions, state transitions | `appflow.md` |
| Visual system, layout, tokens, responsive/interaction behavior | `design.md` |
| How all of the above get implemented, tested, and maintained | `rules.md` (this file) |

**Conflict resolution mechanism:**
1. **Identify the conflict explicitly.** Name the two (or more) documents and quote the conflicting statements.
2. **Do not silently choose a resolution if it changes product behavior.** A behavior-changing decision is not an implementation detail.
3. **Prefer the highest-priority source** per Section 47 (Security & data integrity > PRD > Architecture > App Flow > Design > code conventions > best practices > agent preference).
4. **Record the conflict and any assumption made** in the relevant module's docstring/README and in a running `docs/gaps_and_assumptions.md` (create if absent) — do not let it live only in a chat transcript or PR description.
5. **Update the affected documentation once the decision is finalized** (Section 34).

**Known conflicts and gaps already identified (`appflow.md` §22) — treat these as pre-flagged, do not re-litigate silently, do not "fix" them without following the process above:**
- **[CONFLICT] Alert lifecycle vs. schema:** PRD §12 describes `New → Acknowledged → (Investigating) → Resolved / False Positive`; `architecture.md` §10's `alerts.status` CHECK constraint only allows `'new' | 'acknowledged' | 'false_positive'`. **Rule:** implement against the schema (three states) for MVP, exactly as `appflow.md` already conservatively resolved it. Do not add `investigating`/`resolved` UI or logic without first extending the schema through a documented migration.
- **[ARCHITECTURE GAP] Geolocation has no PRD-side requirement.** It is architecturally specified (architecture.md §17) but not named in `prd.md` at all. Treat it as an approved architecture-team addition (P1, per architecture.md §20) — implement it as `Approximate Location` only, never as attacker attribution, but do not expand its scope beyond what §17 specifies.
- **[ARCHITECTURE GAP] No frontend component named for PCAP upload placement.** `design.md` §44/§28 resolves this: it lives inside `SimulatorControls.jsx` as a modal (`PcapUploadModal.jsx`). Follow `design.md`, not a new invention.
- **[ARCHITECTURE GAP] `NetworkGraph.jsx` has no backing API endpoint.** Do not fabricate one. Follow `design.md` §32/§44: ship the "coming soon" empty state until a real endpoint is defined and documented.
- **[ARCHITECTURE GAP] No frontend consumer for `GET /api/models/status`.** Not resolved by any source document. Leave unimplemented in the UI until product/architecture decides; do not silently wire it into `StatusBar` without that decision being recorded.
- **[ARCHITECTURE GAP] No retrain-trigger endpoint despite the P2 feature.** Do not build UI for a control that has no backing route. Mark as `UNKNOWN — REQUIRES CLARIFICATION` if asked to implement.
- **[PRD/ARCHITECTURE GAP] No request/response schemas for most endpoints (only `/api/geolocation/{ip}` is specified).** Rule: `backend/api/schemas.py` (Pydantic models) is the single source of truth for every request/response shape once written. An agent must **define** these schemas explicitly and document them there — never invent an implicit shape scattered across handler code and never let frontend and backend infer different shapes independently.
- **[PRD/ARCHITECTURE GAP] No loading/empty/error state designs in the original two docs.** This is resolved: `design.md` §31–33 is the authoritative UX pass. Follow it exactly; do not re-invent loading/empty/error copy or components.
- **[ASSUMPTION] Alert-generation threshold value/location.** Assume it lives in `config/default.yaml` per `appflow.md`'s reasoning; confirm the exact default with the team before hardcoding a number anywhere else.
- **[ASSUMPTION] No RBAC/role differentiation in MVP.** Do not build role-gating logic based on PRD §4's role table — those roles are functional descriptions only, not an access-control spec, until P2 authentication lands.
- **[ASSUMPTION] Top-level navigation mechanism.** `design.md` resolves this with a persistent sidebar (Section 15–18 of `design.md`). Follow it.

**Undocumented requirements:** if a need arises that no source document covers and this section's known-gap list doesn't already address it, follow Section 46 (Emergency/Unclear Requirement Protocol) — do not invent silently.

**Architectural changes:** any change to module boundaries, the folder tree (architecture.md §3), the DB schema (architecture.md §10), or the API surface (architecture.md §11) must be reflected back into `architecture.md` in the same change set, per Section 34.

---

## 3. AI Agent Operating Rules

This section applies to every AI coding agent (Claude, Claude Code, Cursor, Copilot, Antigravity, or others) working on this repository.

**Before writing any code, the agent MUST:**
1. Read the relevant sections of `prd.md`, `architecture.md`, `appflow.md`, and `design.md` for the feature/bug at hand.
2. Inspect the existing implementation of the affected module(s) — do not assume based on the folder tree alone; open the actual files.
3. Identify every file the change will touch, directly or indirectly (imports, consumers of a changed interface, tests).
4. Identify dependencies: what does this module import, what imports this module.
5. Understand existing abstractions (e.g., the repository pattern in `storage/repositories/`, the pure-function pipeline stages in `backend/pipeline/orchestrator.py`) before adding a new one.
6. Reuse existing code where it satisfies the requirement (Section 1, Principle 3).
7. Make the smallest safe change that correctly satisfies the requirement.
8. Test the change (Section 30).
9. Check for regressions in dependent features (Section 31).
10. Update documentation where the change affects it (Section 34).

**The AI agent MUST NOT:**
- Guess undocumented requirements — see Section 46.
- Invent API endpoints, request/response schemas, database fields/tables, environment variables, or dependencies not already present or explicitly approved.
- Replace or restructure the architecture (module boundaries, pipeline shape, the one-directional queue design in architecture.md §18) without explicit approval and a documentation update.
- Rewrite large portions of the codebase to satisfy a small, unrelated request.
- Delete working functionality without verifying it is genuinely unused and unreferenced.
- Create a component/service/utility that duplicates an existing one's responsibility.
- Ignore design tokens defined in `design.md` §7–14/§39 and hardcode a visual value instead.
- Ignore the documented application flow in `appflow.md` and invent a different navigation/interaction path.
- Claim a change "works," "passes tests," or "is complete" without having actually run/verified it in this session. If verification isn't possible in the current environment, say so explicitly instead of asserting success.
- Add any send/write/response capability anywhere on the path from the monitored interface into the pipeline (architecture.md §18). This is the single hardest constraint in the project — see Section 20.

---

## 4. Requirement Traceability

Every non-trivial change should be traceable through this chain:

```
PRD requirement (FR-xxx / Core Feature §6.x)
      ↓
Application flow (appflow.md screen/action)
      ↓
Architecture (folder/module/API/DB element, architecture.md §3–§11)
      ↓
UI/UX design (design.md component/token/state)
      ↓
Implementation (actual files changed)
      ↓
Testing (architecture.md §19 test category)
```

**How an AI agent verifies this before submitting work:**
- State which `FR-xxx` (or Core Feature `§6.x`, or Use Case `UCx`) the change satisfies. If none, the change is either a pure technical/infra task (state that explicitly) or is out of scope — flag per Section 46.
- Confirm the screen/action exists in `appflow.md` Section 3/4 (Navigation Map / Screen-by-Screen Flow); if it doesn't, that's a new flow and needs `appflow.md` updated, not silently built.
- Confirm the architectural element (module, endpoint, table/column) already exists in `architecture.md` §3/§10/§11, or is being added with a corresponding doc update in the same change set.
- Confirm the UI matches a named component/token/state in `design.md`; if a new visual pattern is genuinely required, it must be justified against a real gap (`design.md` §8 "Honest about gaps" precedent), not personal taste.
- Confirm a test exists per the relevant category in Section 30/architecture.md §19.

**PRD requirements reference (FR-001 through FR-022) live in `prd.md` §13** — do not re-list them here; look them up when tracing.

---

## 5. Technology Stack Rules

Derived exclusively from `architecture.md` §21 ("Recommended Technology Stack"). Do not introduce a technology not listed here without going through Section 27 (Dependency Rules) and updating `architecture.md`.

| Technology | Why used | Where it belongs | Where it must NOT be used | Conventions / common mistakes |
|---|---|---|---|---|
| **Python 3.11** | Single consistent language across ML + backend for a small hackathon team (PRD §19) | `backend/`, `network/`, `ml/`, `storage/`, `simulator/`, `geolocation/`, `config/`, `scripts/` | Frontend (that's React/JS) | Type-hint public functions; keep pipeline stages as pure functions/classes per architecture.md §9. |
| **FastAPI + Uvicorn** | REST + native WebSocket support, async-friendly for the sniff loop | `backend/api/` only | Business logic must never live inside a route handler — handlers call into `backend/pipeline`, `backend/risk`, `storage/repositories`, `simulator`, `geolocation` (architecture.md §11) | All request/response bodies are Pydantic models in `backend/api/schemas.py`, never raw dicts. |
| **scapy** (`AsyncSniffer`, `rdpcap`) | Simplest capture library for a student team; async-friendly | `network/passive_capture.py` (live), `network/pcap_reader.py` (PCAP replay, read-only) | Never call any `send`/`sendp`/`sr`/`sr1` anywhere in `network/` — see Section 20 | Swappable later for `pypcap`/`dpkt` if performance demands it (architecture.md §21) — do not swap without a documented reason. |
| **scikit-learn** (`RandomForestClassifier`, `IsolationForest`) | Fast to train, native feature-importance output for explainability, appropriate for tabular flow metadata at this scale | `ml/supervised/`, `ml/unsupervised/` | No deep learning frameworks (architecture.md §7 explicitly rules this out as unjustified) unless a documented architecture change approves it | Persist trained models with `joblib` to `models/trained/*.pkl`; load via `ml/model_registry.py`, never load a model file directly from elsewhere. |
| **pandas / numpy** | Feature engineering | `ml/feature_extraction.py`, `ml/feature_normalizer.py`, `datasets/pipeline/*` | Not the ingestion/validation layer (`network/`) — those stay stdlib/scapy-typed until features are extracted | Feature extraction functions are pure (no I/O) per architecture.md §5. |
| **SQLite via SQLAlchemy** | Zero-ops, laptop-friendly, trivially swappable for Postgres later | `storage/db.py`, `storage/models_orm.py`, `storage/repositories/*.py` | No other file writes raw SQL — repositories are the only SQL-writing files (architecture.md §5) | WAL mode enabled; single-writer pattern (architecture.md §24). |
| **Native WebSocket (FastAPI)** | Chosen over SSE/polling for real-time push (architecture.md §22) | `backend/api/ws_manager.py` | — | Frontend must implement the documented WS→polling fallback (`design.md` §33, architecture.md §24) — never silently drop reconnection handling. |
| **React (Vite)** | Frontend SPA | `frontend/src/` | — | Functional components + hooks; no class components unless there's a specific documented reason. |
| **recharts or chart.js** | Lightweight charting | `TrafficChart.jsx`, `ThreatBreakdown.jsx`, and any chart component | — | Pick one and use it consistently across the whole app — do not mix both charting libraries in the same project. |
| **Tailwind CSS** (per `design.md` §40) | Utility-first styling matching the design system | `frontend/src/` via `@layer components` classes (`design.md` §40) | Never repeat long raw utility strings per instance — always compose the shared classes (`.cyber-card`, `.cyber-button-primary`, etc.) | Extend `tailwind.config.js` with `design.md` §39 tokens; do not hardcode hex values in JSX. |
| **MaxMind GeoLite2 (`geoip2`)** | Offline geolocation, no live internet dependency for the demo | `geolocation/geolocation_service.py`, `geolocation/geo_cache.py` | Never presented as anything but "Approximate Location" (architecture.md §17, `design.md` icon rules) | Always includes `is_approximate: true` in every result — mandatory field per architecture.md §17.5. |
| **pytest, pytest-asyncio, httpx** | Backend/API testing | `tests/unit/`, `tests/integration/`, `tests/ml/`, `tests/network/`, `tests/simulator/` | — | Mirror the source tree structure (architecture.md §3/§19). |
| **React Testing Library** | Frontend/component testing | `frontend/` test files | — | Test the data-contract between WS payload and `schemas.py` (architecture.md §19). |
| **pydantic-settings, python-dotenv** | Typed config, `.env` loading | `config/settings.py` | Every other module reads config only through `config/settings.py` — never hardcode a path/threshold elsewhere (architecture.md §5) | `.env.example` documents every variable; never commit a real `.env`. |

**Anything not in this table (a new library, framework, or service) is `TO BE DEFINED` until explicitly approved and added to `architecture.md` §21.**

---

## 6. Architecture Rules

Derived from `architecture.md` §1–§9 and §18. The system is a **modular monolith** — one Python process (or small set of cooperating local processes) — not microservices. Respect this; do not propose splitting into services without an explicit, documented architecture change.

**Layering (strict, per architecture.md §4 folder table):**
- `network/` — capture, validation, dedup, flow aggregation only. **Must NOT contain:** any `send`/`sendp`/`sr`/`sr1` call, ML code.
- `ml/` — feature extraction, RF, Isolation Forest, fusion, inference. **Must NOT contain:** network capture code, DB writes.
- `backend/risk/` — risk scoring, severity, confidence, explanation. **Must NOT contain:** model training code, DB code.
- `backend/pipeline/` — orchestrates the flow → feature → ML → risk → storage sequence. **Must NOT contain:** business rules for scoring (that belongs in `backend/risk/`).
- `backend/core/` — logging, error types, degraded-mode state machine (cross-cutting). **Must NOT contain:** feature/ML/risk logic.
- `backend/api/` — HTTP + WebSocket surface. **Must NOT contain:** ML/risk logic inline in handlers.
- `storage/` — SQLite schema, ORM models, repositories. **Must NOT contain:** payload bytes, business logic.
- `simulator/` — normal/attack traffic generators, demo controller. **Must NOT contain:** real capture code.
- `geolocation/` — IP → approximate location, cached. **Must NOT contain:** any claim of exact/attacker location.
- `config/` — centralized settings. **Must NOT contain:** secrets committed in plaintext.
- `frontend/` — React SPA. **Must NOT contain:** business logic, ML logic.

**Dependency direction:** `simulator/` and `network/` are alternate/parallel ingestion sources that both feed `backend/pipeline/orchestrator.py` through **one shared queue interface** — downstream code must never know or care which source produced a flow (architecture.md §13/§8). `backend/pipeline/` depends on `network/`/`simulator/`, `ml/`, `backend/risk/`, and `storage/`; none of those may depend back on `backend/pipeline/` (no circular imports).

**Prohibited patterns:**
- Circular dependencies between any of the layers above.
- Business logic inside UI components (`frontend/`) — components render state and dispatch actions; they do not compute risk scores, severity, or explanations.
- Database logic inside `backend/pipeline/`, `backend/risk/`, `ml/`, or `frontend/` — only `storage/repositories/*.py` writes SQL.
- God components/services: a single file that does ingestion + scoring + persistence + presentation. Every pipeline stage in architecture.md §6 is a separate typed dataclass/Pydantic object; keep stages separate and independently testable (architecture.md §9).
- Ad hoc dicts crossing module boundaries — every object in the pipeline (`FlowRecord`, `FeatureVector`, `RiskResult`, `Explanation`, `AlertRecord`) is a typed dataclass/Pydantic model defined once and reused (architecture.md §6).

---

## 7. Project Structure Rules

The folder tree in `architecture.md` §3 is authoritative. Do not add a new top-level folder, rename an existing one, or move a file to a different layer without a documented architecture change (Section 2/34).

- New backend modules go under the existing layer they belong to (see Section 6) — never create a new top-level package for something that fits an existing one.
- New frontend components go under `frontend/src/components/<category>/` following the existing categorization in `design.md` §41 (`layout/`, `status/`, `charts/`, `alerts/`, `simulator/`, `history/`, `graph/`, `ui/`); new pages go under `frontend/src/pages/` and must correspond to a screen already named in `appflow.md` §3, or a documented flow update.
- Shared/reusable frontend primitives (buttons, cards, badges, inputs, modals) live in `frontend/src/components/ui/` — do not redefine a button or card style locally in a page component when `CyberCard`/`CyberButton`/etc. already exist.
- Hooks live in `frontend/src/hooks/`; API clients in `frontend/src/api/`; styles/tokens in `frontend/src/styles/` (`design.md` §41).
- Tests mirror the source tree (`architecture.md` §3/§19): `tests/unit/`, `tests/integration/`, `tests/ml/`, `tests/network/`, `tests/simulator/`.
- Dataset processing (`datasets/`) is training-time only and never imported by runtime code (`appflow.md` §19 confirms it has no runtime UI representation — do not wire it into the live pipeline).
- Trained model artifacts live only in `models/trained/`; never commit a model binary anywhere else, and never load one from a path not resolved through `ml/model_registry.py`.
- Config values live only in `config/` (`settings.py`, `default.yaml`, `risk_weights.yaml`, `.env.example`) — no magic numbers/paths/thresholds hardcoded elsewhere (architecture.md §5, `risk_engine.py` entry).

---

## 8. Naming Conventions

Where the source documents establish a concrete pattern (via actual named files/routes/tables), that pattern is the rule. Where they don't, use the stated convention and stay consistent across the codebase.

| Category | Convention | Example (from source docs) |
|---|---|---|
| Python files/modules | `snake_case.py` | `flow_aggregator.py`, `risk_engine.py`, `severity_mapper.py` |
| Python classes | `PascalCase` | `FlowRecord` (architecture.md §6) |
| Python functions/variables | `snake_case` | `predict_proba`, `anomaly_score` |
| React component files | `PascalCase.jsx` | `MainDashboard.jsx`, `ZeroOutboundBadge.jsx`, `LiveAlertFeed.jsx` |
| React hooks | `useCamelCase.js` | `useLiveAlerts.js`, `useAlertHistory.js`, `useStatus.js`, `useStats.js` (`design.md` §41) |
| Shared Tailwind component classes | `.cyber-<name>` prefix, kebab-case | `.cyber-card`, `.cyber-button-primary`, `.cyber-badge` (`design.md` §40) |
| API endpoints | `snake_case`/kebab path segments under `/api/` | `/api/status`, `/api/stats/live`, `/api/alerts/{id}/false-positive` (architecture.md §11) |
| WebSocket routes | `/ws/<resource>` | `/ws/alerts` |
| Database tables | plural, `snake_case` | `flows`, `features`, `model_results`, `alerts` (architecture.md §10) |
| Database columns | `snake_case` | `flow_id`, `src_ip`, `risk_score`, `created_ts` |
| Environment variables | `UPPER_SNAKE_CASE`, documented in `.env.example` | not individually named in source docs — new ones must be added to `.env.example` with a comment |
| Test files | `test_<unit_under_test>.py` | `test_feature_extraction.py`, `test_zero_outbound.py` (architecture.md §3) |
| Design tokens (CSS vars / Tailwind theme keys) | `camelCase`, matching `design.md` §39 exactly | `textPrimary`, `borderFocus`, `glow.critical` |

Anything not covered above: follow the closest existing precedent in the same folder before inventing a new pattern.

---

## 9. Component Rules (Frontend)

- Each component has one responsibility, matching `design.md`'s rule: **"every card answers one question"** (`design.md` §6.3). A component that mixes unrelated data (e.g., a KPI card that also renders a filter control) is split.
- Page components (`MainDashboard.jsx`, `AlertDetail.jsx`, `AlertHistory.jsx`, `NetworkGraph.jsx`) compose smaller components; they do not contain large inline JSX blocks that duplicate an existing component's job.
- Presentational components (`ui/` category) accept props and render; they do not fetch data directly — data comes from hooks (`hooks/`) or is passed down from a page.
- Business/derived state (risk score, severity, explanation) is never computed client-side — it always arrives from the backend already computed (Section 6: no business logic in `frontend/`).
- Reusable primitives (`CyberCard`, `CyberButton`, `CyberBadge`, `Modal`, `Toast`, `Skeleton`, `EmptyState`) are used, not re-implemented, wherever their pattern applies.
- New feature-specific components are created only when no existing `ui/` primitive plus composition can satisfy the need.
- Props: keep prop surfaces minimal and typed (PropTypes or TypeScript if the project adopts it — not currently specified, so match whatever the existing components use).
- Side effects (WS subscriptions, polling, fetches) live in hooks, not scattered inline in component bodies.

---

## 10. UI/UX Implementation Rules

All UI must follow `design.md` exactly. This section names the enforcement points; `design.md` remains the content source.

- **Colors:** only tokens from `design.md` §7/§39 — never a raw hex value in a component. Severity colors (`informational`/`low`/`medium`/`high`/`critical`) are used **only** for severity; `warning`/`danger`/`success`/`info` are used only for their semantic (non-severity) purpose. Never let severity red leak into a generic error color or vice versa (`design.md` §43 DON'Ts).
- **Typography:** follow the table in `design.md` §8 exactly — monospace (`JetBrains Mono`) for every IP/port/protocol/ID/raw timestamp; sans (`Inter`) for everything a human reads as prose. This distinction is a design rule with no exceptions.
- **Spacing:** only the 8px-based scale in `design.md` §9 (`xs`–`2xl`). No arbitrary pixel values for padding/margin/gap.
- **Layout:** follow the grid system in `design.md` §10 and the Application Shell in `design.md` §15 (fixed sidebar + fixed header, independently scrolling content).
- **Components:** buttons, forms, cards, tables, modals, navigation, dashboards, notifications all follow their dedicated `design.md` sections (§20–§30) — do not invent a new visual pattern for something already specified.
- **Icons:** `lucide-react` only, per the usage map in `design.md` §14. Icons never carry meaning alone — always paired with color + text label (`design.md` §14/§36).
- Arbitrary visual decisions are prohibited whenever an existing design token or pattern already covers the case. A genuinely new visual need is handled per `design.md` §8's own precedent: make one concrete, minimal, documented decision and label it, rather than freelancing silently.

---

## 11. Design Token Rules

- Every color, spacing, radius, shadow, glow, and font value used in the frontend comes from `design.md` §39's token object (also reproduced in `design.md` §7–§13). Do not hardcode a repeated visual value — if a value is used more than once, it is a token.
- Do not create a visually similar but separate token (e.g., a second "cyan" or a second "16px" spacing value) when an existing token already serves the purpose.
- Tailwind config is extended once with these tokens (`design.md` §40); components consume them via Tailwind theme classes or the shared `.cyber-*` component classes, never via inline style hex/px literals.
- Glow tokens follow the "at most one glow per card, never stacked" rule (`design.md` §12).
- Severity always pairs color + icon + text label — this is both a design rule (`design.md` §6.6) and an accessibility rule (Section 13 below); it is never satisfied by color alone.

---

## 12. Responsive Design Rules

Follow the breakpoint table in `design.md` §35 exactly (Desktop ≥1280px, Laptop 1024–1279px, Tablet 768–1023px, Mobile <768px). Requirements at every breakpoint:

- No horizontal overflow at any width.
- No broken layouts — sidebar collapses to icon-only (laptop) then to a hamburger-triggered overlay drawer (tablet/mobile), per `design.md` §16/§35.
- Touch-friendly controls on tablet/mobile (adequate tap target size — see Section 13 accessibility touch-target rule).
- KPI cards: 4-across (desktop) → 2×2 (laptop/tablet) → 1-per-row stacked (mobile).
- Charts: side-by-side (desktop/laptop) → stacked full-width (tablet/mobile), reduced height on mobile.
- Tables (AlertHistory): standard table down to tablet (horizontal scroll if needed), converts to stacked "card" rows on mobile — this conversion is mandatory, not optional (`design.md` §35).
- FilterBar collapses into a "Filters" button/drawer on tablet/mobile.
- NetworkGraph shows a "use a larger screen" placeholder on mobile rather than attempting the canvas.
- Text wraps appropriately at every breakpoint; no fixed-width text containers that clip content.

---

## 13. Accessibility Rules

Target: WCAG-AA-conscious implementation, per `design.md` §36.

- **Contrast:** all text/background pairs meet WCAG AA (4.5:1 body text, 3:1 large text/UI components) — use the token pairs already verified in `design.md` §7's contrast notes; do not introduce a new color pairing without checking contrast.
- **Semantic HTML:** `<nav>` for the sidebar, `<table>` for AlertHistory (never div-grids for tabular data), `<button>` for actions (never a clickable `<div>`), form labels properly associated with their inputs.
- **Keyboard navigation:** full tab order through sidebar → header → page content → cards/rows/buttons in visual order. Every interactive element is reachable and operable via Enter/Space.
- **Focus states:** every focusable element gets a visible 2px `borderFocus` outline with 2px offset — never `outline: none` without a replacement.
- **Screen readers:** `aria-live="polite"` on `LiveAlertFeed` so new alerts are announced without stealing focus; status pill changes (Live/Degraded/Disconnected) are also live-region announced; icons carrying meaning have an accompanying visually-hidden text label.
- **Charts:** every chart has an adjacent (visually hidden or expandable) data-table equivalent or text summary — non-visual access to the same information the chart conveys.
- **Tables:** proper `<th scope="col">` headers; sortable-column state exposed via `aria-sort`.
- **Non-color severity:** every severity instance pairs color + icon + text label — never color alone (see Section 11).
- **Reduced motion:** motion is subtle and short (150–400ms per `design.md` §37); respect `prefers-reduced-motion` where the platform provides it — not explicitly specified beyond this, so default to disabling non-essential transitions when that media query is active.
- **Touch targets:** interactive elements on tablet/mobile must be large enough to tap reliably — not given an exact pixel value in `design.md`; use a minimum of 44×44px as a reasonable, widely-adopted default until a specific value is documented.

---

## 14. Application Flow Rules

Follow `appflow.md` exactly for navigation, routing, and user journeys. Do not invent a new flow that contradicts it.

- **Navigation:** persistent sidebar with MainDashboard (default route), AlertHistory, NetworkGraph (P2, feature-flagged) as top-level items; AlertDetail is reached only via click-through from `LiveAlertFeed` or an `AlertHistory` row — it is never a sidebar nav item (`design.md` §1, resolving `appflow.md`'s flagged navigation gap).
- **Routing:** React Router (or equivalent) implements the four page routes named in `architecture.md` §3's frontend tree. No fifth page is added without updating `architecture.md` and `appflow.md` together.
- **Authentication/Authorization:** none exists in MVP (`appflow.md` §10, PRD §24 lists auth as P2). Do not build a login screen, protected route, or session concept for MVP. If P2 auth work begins, it must be added as toggleable middleware that does not destabilize existing P0 flows (architecture.md §20).
- **Protected pages:** none in MVP — every screen is reachable by every user (`appflow.md` §2's gap note). Do not implement role-based UI gating based on PRD §4's role table.
- **Forms:** only the two forms specified in `design.md` §29 (SimulatorControls scenario selection, AlertDetail notes textarea) — plus any PCAP upload control per the resolved gap. Follow their exact validation/submission behavior.
- **Success/failure/loading/empty states:** follow `design.md` §31–33 exactly (this is the resolved version of `appflow.md`'s flagged gap — do not re-derive these from scratch).
- **Redirects:** not specified beyond in-app navigation via click-through; do not add a redirect behavior (e.g., auto-navigating after an action) that isn't documented.
- No new flow should contradict `appflow.md` §4 (Screen-by-Screen Flow) or §5 (End-to-End User Journeys) without both documents being updated together.

---

## 15. State Management Rules

Derived from `architecture.md` §12 and `design.md` §41.

- **Local state:** component-local UI state (form inputs, toggle states, modal open/closed) uses React's own `useState`/`useReducer`. No global store for this.
- **Global/live state:** a WebSocket-driven React context (`architecture.md` §12) feeds `useLiveAlerts`/`useStatus`/`useStats` — this is the single source for real-time data (status, counters, charts, live alert feed).
- **Server/query state:** `AlertHistory` and `AlertDetail` use plain fetch-on-mount + refetch-on-filter-change; they do not need the WS context beyond an optional "new alerts available" banner, which is explicitly **not required** by the PRD and should not be added speculatively (`design.md` §41).
- **No Redux or equivalent heavyweight state library** — explicitly ruled unnecessary at this scale (`architecture.md` §12: "no need for Redux"). Do not introduce one without a documented reason and a Section 27 dependency justification.
- **Persistent/cache state:** the backend is the source of truth; the frontend does not persist state to `localStorage`/`sessionStorage` beyond what's explicitly required (none currently specified).
- **Derived state** (e.g., filtered/sorted table rows) is computed from server data at render/query time, not duplicated into a separate store.

---

## 16. API Rules

The API surface is defined in `architecture.md` §11. Do not add, remove, or change an endpoint's meaning without updating that section.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/status` | system/passive-mode/degraded status |
| GET | `/api/stats/live` | packets scanned, flows analyzed, threats detected, safe traffic |
| GET | `/api/alerts` | live + historical, filterable |
| GET | `/api/alerts/{id}` | full alert detail |
| POST | `/api/alerts/{id}/ack` | acknowledge |
| POST | `/api/alerts/{id}/false-positive` | mark false positive |
| POST | `/api/alerts/{id}/notes` | add notes |
| GET | `/api/alerts/history` | filtered history (date, category, severity, src IP, status) |
| POST | `/api/simulator/normal/start` \| `/stop` | control normal traffic sim |
| POST | `/api/simulator/attack/{scenario}/start` \| `/stop` | control a specific attack scenario |
| POST | `/api/pcap/upload` | upload + replay a PCAP |
| GET | `/api/models/status` | model versions, load state, degraded flag |
| GET | `/api/geolocation/{ip}` | approximate geolocation lookup |
| WS | `/ws/alerts` | real-time alert + stat push |

**Rules:**
- **Request/response schemas:** must be explicit Pydantic models in `backend/api/schemas.py`. Only `/api/geolocation/{ip}`'s response is currently documented (`{country, state, city, lat, lon, is_approximate: true}` or `{status: "unavailable"|"private/local"}`). Every other endpoint's schema must be defined there before implementation — never leave it as an implicit dict shape.
- **Validation:** happens server-side in the route handler (via Pydantic) before any business logic runs; frontend-side validation (e.g., scenario-must-be-selected in `design.md` §29) is a UX convenience, never the security/correctness boundary (Section 22).
- **Error format:** not explicitly specified by the source docs beyond "structured, timestamped" logging (FR-022). Use a single consistent JSON error shape across all endpoints (e.g., `{error: {code, message}}`) once decided, and document it in `schemas.py` — do not let each route invent its own shape.
- **Authentication:** none in MVP (Section 14). Do not add auth middleware to routes without the documented P2 process.
- **Status codes:** use conventional HTTP semantics (200 success, 400 validation error, 404 not found, 500 server error) — not explicitly enumerated per-route in the source docs, so this is the reasonable default until specified otherwise.
- **Pagination/filtering/sorting:** `/api/alerts/history` supports filtering by date range, category, severity, source IP, status (`prd.md` §12, `architecture.md` §12). Exact query-param contract is unspecified (`appflow.md` §20) — the frontend degrades gracefully to "no results" on a malformed param rather than erroring (`design.md` §28), and any implementer choosing param names must document them in `schemas.py`/`api_reference.md`.
- **Rate limiting / versioning:** not specified anywhere in the source documents. `TO BE DEFINED` — do not add either speculatively.
- Business logic never lives inline in a route handler — handlers call into `backend/pipeline`, `backend/risk`, `storage/repositories`, `simulator`, `geolocation` only (architecture.md §11).

---

## 17. Database Rules

Schema is defined in `architecture.md` §10 (SQLite). Reproduced here for enforcement, not as a duplicate source of truth — `architecture.md` governs any change.

- Tables: `flows`, `features`, `model_results`, `alerts` — linked by `flow_id`/`correlation_id` for full packet→flow→feature→alert traceability (PRD §15, FR requirement).
- `alerts.status` is constrained to `'new' | 'acknowledged' | 'false_positive'` — see the documented lifecycle conflict in Section 2; do not add a value without a migration and a documentation update.
- **No table ever stores packet payload bytes** — this is a hard constraint from both PRD §18/Non-Goals and architecture.md §10. Any schema change that would let payload content persist is prohibited outright, not reviewable.
- **Migrations:** `storage/migrations/` holds versioned SQL migrations (e.g., `0001_init.sql`). Every schema change is a new migration file, never a hand-edited existing one and never a manual `ALTER` run outside the migration path.
- **Naming:** plural snake_case tables, snake_case columns (Section 8).
- **Data access:** only `storage/repositories/*.py` writes SQL (`flow_repository.py`, `alert_repository.py`, `model_result_repository.py`) — this is the sole persistence boundary (architecture.md §5/§6).
- **Transactions/integrity:** single-writer pattern via one pipeline process; WAL mode enabled to avoid write contention (architecture.md §24).
- **Constraints:** `CHECK` constraints (e.g., `alerts.status`, `flows.source`) are enforced at the schema level, not only in application code.
- **Query optimization:** not detailed in source docs beyond the SQLite/WAL choice; add indexes only when a real performance need is identified, and document the reason.
- **Seed data:** distinguish clearly from mock/demo/test data — see Section 38.

---

## 18. Authentication Rules

- No authentication exists in MVP by design (PRD §18/§24, `architecture.md` §20/§21, `appflow.md` §10). Do not implement login, registration, session, or token flows unless explicitly asked to build the P2 feature.
- **If/when authentication is implemented (P2):** passwords must be hashed (never stored in plaintext), sessions/tokens handled securely, and the implementation kept minimal — not a full RBAC system (PRD §18's explicit conditional). It must be built as toggleable middleware that can be disabled without touching P0 code paths (architecture.md §20).
- Never expose credentials in code, logs, URLs, or error messages (Section 20/21).
- Never store secrets in source code — see Section 28.
- Logout/session expiration: not applicable until P2 auth exists.

---

## 19. Authorization Rules

```
Authentication = Who are you?
Authorization  = What are you allowed to do?
```

- In MVP, there is no authentication, so there is no meaningful authorization layer either — every user who can reach the dashboard has identical capabilities (`appflow.md` §2's explicit finding). Do not build role/permission checks against PRD §4's role table for MVP; those roles are organizational, not technical.
- When P2 auth/RBAC eventually lands, authorization enforcement must happen server-side (route/service layer), never solely in the frontend — frontend role checks are a UX convenience only, never a security boundary (Section 22 reinforces this generally).

---

## 20. Security Rules

Security is a core engineering requirement for this project, not an optional enhancement — the product's entire value proposition is a security guarantee.

**The single most important rule in this document:**
> **Zero outbound / zero return traffic.** Nothing in `network/` (capture or PCAP read) may ever call a send/write/response primitive. No `send`, `sendp`, `sr`, `sr1`, raw-socket-write, or ICMP/TCP-reset primitive is permitted anywhere in that package (architecture.md §18). This is enforced at three layers simultaneously and all three must be respected by every change:
> 1. **Structurally** — the boundary between `network/` (read-only) and everything downstream is a one-directional queue (`asyncio.Queue`/`multiprocessing.Queue`); there is no API for the consumer side to write back into the producer side or onto the interface.
> 2. **Procedurally** — `network/interface_guard.py` refuses process startup if a send-capable socket is ever requested against the configured capture interface.
> 3. **Empirically** — `scripts/verify_zero_outbound.py` (static grep) and `tests/network/test_zero_outbound.py` (runtime assertion of zero bytes written) must both pass, and must be re-run whenever `network/` changes.
>
> An AI agent must treat any request that would add a write/response capability to the monitoring path as out of scope for this product, regardless of how it's framed (a "debug" feature, a "just for testing" probe, an "optional" ACK). Flag it and decline per Section 3/42.

**Other security requirements:**
- **Input validation:** malformed/incomplete packet headers are dropped and logged, never processed (FR-006, `network/packet_validator.py`). All API request bodies are validated via Pydantic schemas before reaching business logic (Section 16).
- **Output encoding / XSS:** the frontend renders all user/attacker-influenced data (IPs, ports, explanation text) as text content, never as raw HTML — no `dangerouslySetInnerHTML` on flow/alert-derived data.
- **SQL injection:** only repositories write SQL, and only through the ORM/parameterized queries (SQLAlchemy) — never string-interpolated SQL.
- **CSRF:** not addressed in source docs because there's no session/auth in MVP; revisit when P2 auth lands.
- **Authentication attacks / authorization bypass:** not applicable until P2 auth exists (Sections 18–19); when it does, follow standard hashing/session practices as PRD §18 requires.
- **API security:** no endpoint returns packet payload content (none is ever stored — see Section 17). No endpoint allows triggering a send on the monitored interface (see above).
- **File uploads:** PCAP upload (`POST /api/pcap/upload`) is parsed read-only via `scapy.rdpcap`, never re-injected onto a live interface (architecture.md §8 Mode B). File-type/size validation is currently unspecified (`appflow.md` §4 flags this) — until specified, validate file extension/magic bytes and enforce a reasonable size limit rather than accepting anything.
- **Rate limiting:** not specified — `TO BE DEFINED`. Do not add speculatively without documenting it in `architecture.md`.
- **Dependency vulnerabilities:** see Section 27 — new dependencies require a maintenance/security check before adoption.
- **Error disclosure:** error responses must not leak internal implementation details (stack traces, file paths, DB structure) to the client; log the detail server-side (Section 39), return a generic message to the client.
- **Logging:** never log passwords, tokens, API keys, secrets, or payload bytes (Section 39).
- **Sensitive information:** any stored IP/metadata is treated as sensitive operational data and access-limited in a real deployment context (PRD §18) — even though MVP has no auth, do not casually expose this data through unrelated endpoints or logs.

---

## 21. Data Protection Rules

- **PII/sensitive data in this product:** source/destination IPs, ports, protocol, size, timing — this is genuinely sensitive operational metadata about the monitored network (PRD §18). No payload content is ever captured, stored, or logged (PRD §18, architecture.md §10) — this is the structural privacy guarantee that makes the whole approach viable.
- **Credentials/tokens:** never committed to source, never logged (Section 20/28).
- **Logs:** structured, timestamped (FR-022); never contain secrets or payload bytes.
- **Database access:** only through `storage/repositories/*.py` (Section 17).
- **Data transmission:** the dashboard API/WebSocket runs on a separate network context from the monitored interface — never mix the two (architecture.md §18).
- **Data retention:** flow/alert/feature records are retained for the dashboard's history view; raw packet payloads are never retained at any stage (PRD §15).
- Never expose sensitive information through: frontend bundles, logs, URLs, or error messages, unless explicitly required and architecturally approved (none currently is).
- Client-side storage (`localStorage`/`sessionStorage`) is not used for sensitive data — see Section 15; MVP doesn't specify any persistent client-side storage need.

---

## 22. Validation Rules

- **Client-side validation** (e.g., "a scenario must be selected" before enabling Start, `design.md` §29; basic IPv4/IPv6 shape check on the FilterBar source-IP field, `design.md` §28) exists purely for UX — it prevents obviously-wrong submissions and gives immediate feedback. **It is never treated as a security boundary.**
- **Server-side validation** (Pydantic schemas in `backend/api/schemas.py`, Section 16) is the actual boundary — every request is validated there regardless of what the frontend already checked.
- **Database constraints** (`CHECK` constraints on `alerts.status`, `flows.source`) are the final integrity layer — even if application code has a bug, the DB itself rejects invalid values.
- **Sanitization:** applies to any user-supplied text that gets rendered (e.g., alert notes) — render as text, not HTML (Section 20).
- **Type validation:** enforced by Pydantic at the API boundary and by the ORM at the persistence boundary.
- **Business-rule validation** (e.g., alert lifecycle transitions, dedup window logic) lives in `backend/pipeline`/`backend/risk`, not scattered across route handlers or the frontend.

**Layer responsibility summary:** frontend = UX guidance only; API layer (Pydantic) = contract enforcement; business logic layer = domain rules; database = final integrity guarantee. Each layer validates independently; none trusts that a previous layer already did its job.

---

## 23. Error Handling Rules

- **Validation errors:** returned from the API with a clear, non-implementation-leaking message; surfaced in the frontend via the inline error patterns in `design.md` §33 (banner within the relevant card/panel, `danger`-tinted, `AlertTriangle` icon, one-line message).
- **Authentication/authorization errors:** not applicable in MVP (Sections 18–19).
- **Network errors (frontend → API):** WebSocket disconnect → automatic reconnect attempts → polling fallback → manual retry, exactly as specified in `design.md` §33 and `architecture.md` §24. Do not invent a different reconnection strategy.
- **API errors (backend → external):** not applicable (no outbound calls except optional geolocation provider and dataset downloads at dev time, both non-blocking per architecture.md §24).
- **Database errors:** SQLite write contention is mitigated architecturally (single-writer + WAL); not surfaced to the user (architecture.md §24).
- **ML/inference errors:** caught by `backend/core/degraded_mode.py`, which marks the pipeline `DEGRADED` and continues passing flows through with `risk_score=null`, `severity="Unknown - ML Unavailable"` rather than crashing ingestion or the dashboard (FR-021). This is a hard requirement — any change to `ml/` or `backend/pipeline/` must preserve this fallback path.
- **Unexpected/unhandled errors:** logged in structured, timestamped format (FR-022, `backend/core/logging_setup.py`/`errors.py`); the app-shell-level full-page error state (`design.md` §33 — `WifiOff` icon, "Can't reach OneWay Sentinel's backend," Retry button) is the only true full-page error state in the product — don't add others casually.

**General principle:** errors help the user understand what happened, avoid exposing internal implementation details, are consistently formatted, and are always logged appropriately (Section 39).

---

## 24. Loading / Empty / Error / Success States

Every asynchronous, user-facing feature must define all applicable states from:
```
Loading → Success → Empty → Error
```
Follow `design.md` §31–33 exactly — this is the resolved version of `appflow.md`'s flagged gap; do not re-derive these from scratch or invent alternate copy/behavior.

- **Loading:** skeleton screens matching each page's real layout for initial page load; no loading indicator for incremental WS-driven updates; buttons show an inline spinner (keeping their label, no layout shift) for action-in-flight states.
- **Empty:** every documented empty case in `design.md` §32 (no active alerts, no filtered results, no alerts ever recorded, NetworkGraph "coming soon," geolocation unavailable, no source history) uses the specified icon/copy pattern — centered content, `textMuted`/`textSecondary`, never an error color.
- **Error:** WS disconnected/reconnecting/polling/disconnected states on the StatusBar pill; ML-degraded banner; inline API-failure banners; the one app-shell-level full-page failure state; PCAP-upload inline failure — all per `design.md` §33.
- **Success:** confirmed via toast notifications only for action confirmations (Acknowledge, note saved, simulator started/stopped, PCAP analysis started) — never for the threat alerts themselves, which are content, not chrome (`design.md` §30).

Never leave the user with a blank screen, a frozen button, an unexplained loader, or a silent failure.

---

## 25. Form Rules

Only two forms exist in the product (`design.md` §29) — do not add a third without a documented product need:

1. **SimulatorControls:** scenario `<select>` (Port Scan / Network Scan / DDoS-like Flood / Exfiltration / Beaconing / Unknown Anomaly) + Start/Stop for Normal Traffic and the selected attack scenario. "Start Attack Scenario" stays disabled until a scenario is selected.
2. **Notes (AlertDetail):** single `<textarea>`, 3 rows default (auto-grows to 6), placeholder "Add investigation notes...", submit disabled until non-empty, submits via `POST /api/alerts/{id}/notes`.

**Standards for both:**
- Labels are present and properly associated with inputs (Section 13).
- Required fields are enforced client-side (UX) and server-side (Section 22).
- Error messages are inline, per `design.md` §33.
- Submission shows the disabled + inline-spinner loading state (`design.md` §31).
- Success is confirmed via toast (`design.md` §30).
- Input styling uses the shared token set (`surfaceSunken` background, `border`/`borderFocus`, `radius.sm`, 40px height, Inter 14px) — `design.md` §29.
- Server-side validation is the real boundary (Section 22); never trust client-side checks alone.
- Sanitize any free-text field (notes) before rendering it back (Section 20).

If PCAP upload is implemented as a modal/dropzone (Section 2's resolved gap), it follows the same standards: inline error state within the modal, dropzone stays active for retry on failure (`design.md` §33).

---

## 26. Code Quality Rules

- **Readability:** code should be understandable by a teammate without ML/networking specialization reading it cold — this mirrors the product's own "Usability" NFR of plain-language explanations (PRD §14) applied to the codebase itself.
- **Maintainability:** feature extraction, model inference, scoring, and presentation are kept as separable modules so any one can be modified or swapped independently (PRD §14 NFR, architecture.md §6/§9) — this must remain true after every change, not just at initial build time.
- **Modularity/SOLID (applied pragmatically, not dogmatically):** single-responsibility per module (Section 6); depend on the typed pipeline objects (interfaces), not on another module's internals; don't force an unrelated abstraction just to satisfy a principle on paper.
- **Type safety:** Python functions in the pipeline are type-hinted; pipeline objects are dataclasses/Pydantic models, not raw dicts (architecture.md §6).
- **DRY:** reuse existing utilities/components before writing a new implementation (Section 1, Principle 3) — but don't force a shared abstraction across two things that only coincidentally look similar today and are likely to diverge.
- **No magic numbers:** thresholds, weights, and window sizes come from `config/` (`risk_weights.yaml`, `default.yaml`), never hardcoded inline (architecture.md §5).
- **No dead code:** don't leave commented-out blocks or unused functions "just in case" — if it's not used, remove it (after verifying it's genuinely unreferenced, Section 41).
- **No unnecessary abstractions:** this is a hackathon-scale, laptop-run prototype (PRD §19) — do not introduce enterprise patterns (message queues, service meshes, generic plugin systems) that the project doesn't need. Simplicity is itself a requirement here, not a shortcut.

---

## 27. Dependency Rules

Before adding any new dependency (Python package or JS package):
1. **Check existing project capabilities** — does something already in Section 5's stack solve this?
2. **Check compatibility** — Python 3.11 / the existing `requirements.txt`/`pyproject.toml`, or the existing `package.json`'s React/Vite setup.
3. **Check maintenance status** — is it actively maintained, not abandoned?
4. **Check security** — any known vulnerabilities?
5. **Check bundle/runtime impact** — this must run on a single student laptop (PRD §19); avoid heavy dependencies for small conveniences.
6. **Check licensing** where relevant for a hackathon submission.

Prefer existing dependencies (Section 5's table) over adding new ones. A new dependency requires a stated reason and, if it changes the technology stack meaningfully, an update to `architecture.md` §21.

---

## 28. Environment Configuration Rules

- All configuration goes through `config/settings.py`, which loads `default.yaml` + `.env` + `risk_weights.yaml` into one typed settings object (architecture.md §5). No other module reads `.env` directly or hardcodes a config value.
- `.env.example` documents every environment variable with a comment; a real `.env` is never committed.
- **Never commit secrets.** Never hardcode credentials, API keys, or database connection strings in source.
- Development vs. production configuration: not detailed in source docs beyond the single-laptop deployment target (PRD §19) — this is a hackathon prototype, not a multi-environment production system; `TO BE DEFINED` if the project later needs environment-specific configs.
- Geolocation provider credentials (if a remote provider is ever configured instead of the offline MaxMind file) go through the same `config/settings.py` mechanism, never inline in `geolocation_service.py`.

---

## 29. Performance Rules

- **Target:** alert reaches the dashboard within 2 seconds of the triggering flow being ingested, at demo-representative volumes — hundreds of flows/second on commodity hardware (PRD §14/§17, FR-020). Treat this as a hard, testable performance budget for the full pipeline, not an aspiration.
- **Rendering:** WS-driven counters/charts update in place without full re-renders/re-draw flashes (`design.md` §34); avoid re-rendering the entire alert feed on every incoming event — update only the changed portion.
- **API requests:** `AlertHistory`/`AlertDetail` fetch on demand (not continuously polled) — no unnecessary repeated requests (Section 15).
- **Database queries:** indexed appropriately for the filter/history queries once a real performance need is identified (Section 17) — don't add indexes speculatively without evidence.
- **Caching:** geolocation results are cached (`geo_cache.py`) since IP→geo rarely changes (architecture.md §17) — no TTL needed per that design.
- **Lazy loading / code splitting:** not explicitly required by source docs given the small scope (4 pages); apply only if bundle size becomes a real problem.
- **Large datasets:** `AlertHistory` supports filtering/pagination-style querying rather than loading the entire alert table at once (implied by PRD §6.7/§11's "searchable/filterable" requirement).
- **Network efficiency:** WebSocket push is used specifically to avoid polling overhead under normal operation (architecture.md §22); polling is only the degraded fallback.
- **No premature optimization** — this is explicitly out of scope for a hackathon prototype; fix obvious performance problems, don't speculatively optimize what isn't measured as slow.

---

## 30. Testing Rules

Testing categories, per `architecture.md` §19 — this is authoritative; do not invent a different testing strategy.

| Category | Scope |
|---|---|
| **Unit** | feature extraction math, risk engine weighting, severity band mapping, confidence calculation, explanation generation (fixed feature inputs → stable explanation text pattern) |
| **ML inference** | RF and IF loaded from fixture models, deterministic outputs on fixed feature vectors |
| **Risk-score** | boundary tests at each severity band edge (19/20, 39/40, 59/60, 79/80) |
| **Simulator** | each scenario emits the expected statistical shape (e.g., port scan → `unique_dst_port_count` above threshold) |
| **API** | every route in architecture.md §11, including error paths (invalid alert id, malformed PCAP upload) |
| **Dashboard integration** | WS event → store update → component render (React Testing Library); data-contract test that the WS payload matches `backend/api/schemas.py` |
| **Passive-ingestion** | validator rejects malformed packets, deduplicator drops repeats, aggregator windows correctly |
| **Zero-outbound verification** | the flagship test — floods the interface with adversarial "response-provoking" scenarios, asserts send counters remain exactly zero for the entire run. **This must never be skipped, weakened, or removed.** |

Prioritize testing around critical product requirements: zero-outbound guarantee (highest priority — see Section 20), sub-2-second latency, hybrid detection correctness, explanation coverage, degraded-mode graceful failure.

**Security tests** cover: zero-outbound (above), malformed-input handling, degraded-mode fallback correctness. Authentication/authorization tests are not applicable until P2 auth exists.

---

## 31. Regression Prevention

Whenever code changes, verify:
- The changed feature itself works as intended.
- Dependent features that consume the changed interface/data still work (trace via Section 4).
- Shared components/utilities used elsewhere in the codebase are unaffected.
- The documented application flow (`appflow.md`) still holds end to end.
- API contracts (`backend/api/schemas.py`) haven't silently changed shape for existing consumers.
- Authentication/authorization — not applicable in MVP, but re-check this note if P2 auth lands.
- Responsive UI is re-verified at all four breakpoints if any visual/layout code changed (`design.md` §35).
- **The zero-outbound guarantee** (`scripts/verify_zero_outbound.py` + `tests/network/test_zero_outbound.py`) is re-run whenever `network/` or the ingestion queue changes — this is the single highest-priority regression check in the project.
- The sub-2-second latency budget is re-checked whenever the pipeline (`backend/pipeline/orchestrator.py`) or any stage it calls changes.

---

## 32. Git Rules

Not specified in project documentation beyond the general engineering-hygiene expectation implied by "small, well-understood models" and a short hackathon build window (PRD §19). Apply conventional, low-friction practices:
- **Branch naming:** `TO BE DEFINED` by the team — a reasonable default is `<type>/<short-description>` (e.g., `feat/pcap-upload-modal`, `fix/severity-mapper-boundary`).
- **Commit messages:** small, focused commits with a clear summary of what changed and why; avoid bundling unrelated changes into one commit.
- **Commit scope:** one logical change per commit where practical.
- **Pull requests:** described against the traceability chain in Section 4 (which requirement, which flow, which architecture element).
- **Reviews:** use the checklist in Section 33.
- **Merge practices / conflict resolution:** `TO BE DEFINED` — no specific policy given in source docs; prefer rebasing small feature branches over long-lived divergent branches, given the team size and timeline (PRD §19).

Encourage small, focused changes over large batched ones (Section 1, Principle 6).

---

## 33. Code Review Rules

Checklist for reviewing any change (self-review for an AI agent before presenting work, or human review):

- [ ] Traceable to a PRD requirement / Core Feature / Use Case (Section 4).
- [ ] Respects the architecture's module boundaries (Section 6).
- [ ] Matches `design.md`'s visual system and states, if UI (Sections 10–13, 24).
- [ ] No security regression, especially zero-outbound (Section 20).
- [ ] No obvious performance regression against the 2-second latency budget (Section 29).
- [ ] Has appropriate tests per Section 30, and existing tests still pass.
- [ ] Accessibility checked if UI changed (Section 13).
- [ ] Error handling follows Section 23 (no silent failures, no leaked internals).
- [ ] Maintainability preserved — modules stay separable (Section 26).
- [ ] Documentation updated if the change affects `prd.md`/`architecture.md`/`appflow.md`/`design.md` (Section 34).

---

## 34. Documentation Synchronization

When product requirements change, propagate downward and update **only the documents actually affected**:

```
prd.md
  ↓
appflow.md
  ↓
architecture.md
  ↓
design.md
  ↓
rules.md
```

- A PRD change to a feature's scope may ripple into `appflow.md` (new/changed flow), `architecture.md` (new module/endpoint/table), `design.md` (new screen/state), and finally this file if it changes an enforceable rule.
- Not every change touches every document — e.g., a pure bug fix with no requirement/flow/architecture change touches none of them; a new P1 feature (like PCAP upload) touches PRD (already exists), architecture (already exists), and may need `appflow.md`/`design.md` updates if the flow/UI wasn't fully specified.
- Do not modify documentation unnecessarily — only update what the change actually affects.
- The same rule applies in reverse: if implementation reveals that a document was wrong or incomplete (e.g., a genuinely missing schema), update the document, don't just patch around it silently in code.

---

## 35. Change Management

For any major change (new feature, schema change, API surface change, architecture change), identify and record:
- **Requirements affected** (which `FR-xxx`/`§6.x`/PRD section).
- **Architecture affected** (which folder/module/data-flow diagram in `architecture.md`).
- **Database affected** (which table/column, and whether a migration is needed).
- **API affected** (which endpoint(s), and whether `schemas.py` changes).
- **UI affected** (which screen/component in `design.md`/`appflow.md`).
- **User flow affected** (which journey in `appflow.md` §4/§5).
- **Security impact** (does it touch `network/`, auth, or data exposure — Section 20/21).
- **Testing impact** (which test categories from Section 30 need new/updated tests).
- **Documentation impact** (which of the four source docs plus this file, per Section 34).

---

## 36. Refactoring Rules

Refactoring is allowed when it:
- Preserves existing behavior (verified by existing tests, Section 30/31).
- Improves maintainability with a clear, stated reason (not "felt like cleaning up").
- Avoids unrelated changes bundled into the same commit/PR.
- Includes regression testing before and after.

Do not perform large refactors during unrelated feature work — if a refactor is genuinely needed while fixing a bug or adding a feature, it is a separate, clearly-labeled change, reviewed on its own.

---

## 37. Technical Debt Rules

- **Identify:** when a shortcut is taken (e.g., a hardcoded threshold pending Section 2's flagged config-location assumption, or a `TO BE DEFINED` item from this file), note it explicitly in code comments and/or `docs/gaps_and_assumptions.md`.
- **Document:** state what was skipped and why, and what the "right" fix would be.
- **Prioritize:** weigh against the P0/P1/P2 priority already established in `prd.md` §24 and `architecture.md` §20 — debt in a P0 path is higher priority than debt in a P2 path.
- **Track:** keep a running list (issue tracker or `docs/gaps_and_assumptions.md`) rather than letting it live only in a commit message.
- **Resolve:** address tracked debt opportunistically when touching the related area, not by scheduling a separate "big cleanup" that risks Section 36's refactor discipline.

Do not hide technical debt — a known gap that's silently left unmentioned is worse than one that's flagged and deferred.

---

## 38. Mock Data Rules

Distinguish these clearly — they are not interchangeable:

- **Mock data:** fake data used only in unit/component tests, never reaching a running instance of the app.
- **Demo data / Simulator data:** the synthetic traffic from `simulator/normal_traffic_simulator.py` and `simulator/attack_simulator.py` — explicitly designed to be realistic and demo-ready (PRD §6.1, architecture.md §15/§16). This is a legitimate, first-class ingestion source, not a stand-in to be removed later — it is the documented reliable fallback if live capture fails (architecture.md §24). Flow records from it are tagged `source = 'simulator_normal' | 'simulator_attack'` in the DB (architecture.md §10), so they're always distinguishable from live/PCAP-sourced data.
- **Seed data:** any data used to pre-populate the DB for development convenience — not currently specified as a project need; if added, it must be clearly separated from the simulator's runtime-generated data and never presented as live/real detections.
- **Test data:** fixtures used in `tests/` (fixed feature vectors, fixture models per Section 30) — never used outside the test suite.
- **Production/real data:** live captured traffic or uploaded PCAPs — the only data that should ever be presented to a user as an actual live/historical detection.

**Hard rule:** an AI agent must never let mock, seed, or test data leak into a path that presents it to a user as if it were live or historical real detection data. Simulator data is the one exception, and it is explicitly labeled as such via the `source` column and the UI's SimulatorControls context — it is never disguised as live capture.

---

## 39. Logging & Monitoring Rules

- **Application logging:** structured, timestamped format (FR-022, `backend/core/logging_setup.py`).
- **Errors:** detection-relevant errors (malformed input, inference failure) are logged in that structured format (FR-022).
- **Security events:** not separately specified — treat zero-outbound test failures and interface_guard refusals as security-relevant and log them prominently.
- **Authentication events:** not applicable until P2 auth exists.
- **API failures:** logged server-side with enough detail to debug, without leaking that detail to the client response (Section 20/23).
- **Monitoring/alerts (ops-level, distinct from the product's own threat alerts):** not specified in source docs beyond `GET /api/models/status` and `GET /api/status` as health-check-style endpoints; no external monitoring/alerting system is in scope for MVP.

**Never log:**
- passwords
- tokens
- API keys
- secrets
- packet payload bytes
- any other unnecessary sensitive information

---

## 40. AI Hallucination Prevention

An AI agent must never invent, without explicit basis in the source documents or an explicit instruction from the team:
- APIs / endpoints not listed in Section 16 / `architecture.md` §11.
- Database fields/tables not listed in Section 17 / `architecture.md` §10.
- Environment variables not already in `.env.example`.
- Libraries/dependencies not in Section 5, without going through Section 27.
- Components not named in `architecture.md` §3 or `design.md` §41, without going through Section 2's gap-resolution process.
- Product features not in `prd.md` §6/§13.
- User permissions/roles beyond what `appflow.md` §2 documents (i.e., none, technically, in MVP).
- Business logic (thresholds, scoring weights, lifecycle states) not documented in `prd.md`/`architecture.md`/`config/`.

**If something is unknown:** state `UNKNOWN — REQUIRES CLARIFICATION` rather than guessing.

**If it can be safely inferred from an established pattern already in the codebase** (e.g., naming a new repository method the same way existing ones are named, per Section 8), the agent may follow that established pattern — this is pattern-following, not invention, and should be stated as such ("following the existing `X` pattern used in `Y`").

---

## 41. Existing Code Preservation

When modifying existing code, an AI agent must:
- **Inspect before editing** — read the actual current implementation, not an assumption from the folder tree.
- **Preserve working behavior** — especially the zero-outbound guarantee and the degraded-mode fallback (Sections 20, 23).
- **Avoid unnecessary rewrites** — change only what the task requires.
- **Avoid changing unrelated files** — a fix to `severity_mapper.py` doesn't also reformat `risk_engine.py`.
- **Avoid deleting apparently unused code without verifying references** — grep/search the codebase for usages before removing anything.
- **Avoid changing public interfaces without checking consumers** — e.g., changing `FlowRecord`'s fields (architecture.md §6) requires checking every stage that consumes it (`ml/feature_extraction.py`, `backend/risk/*`, `storage/repositories/*`, `backend/api/schemas.py`, frontend types).

---

## 42. "DO NOT" Rules

A consolidated checklist of prohibited behavior (each item traces to a section above):
- Do not invent requirements. (Sections 1, 40)
- Do not invent APIs. (Sections 16, 40)
- Do not invent database schema. (Sections 17, 40)
- Do not expose secrets. (Sections 20, 21, 28, 39)
- Do not bypass authentication (when it exists) or implement fake auth for MVP. (Sections 14, 18)
- Do not rely only on frontend authorization/validation. (Sections 19, 22)
- Do not randomly change the design. (Sections 10, 11)
- Do not duplicate existing components. (Sections 1, 9)
- Do not introduce unnecessary packages. (Section 27)
- Do not break documented flows. (Section 14)
- Do not silently change architecture. (Sections 2, 6, 35)
- Do not use production mock data — i.e., never present mock/seed/test data as real. (Section 38)
- Do not ignore errors. (Section 23)
- Do not hide failures. (Sections 23, 24, 37)
- Do not delete working features without justification. (Section 41)
- Do not make unrelated changes. (Sections 1, 36, 41)
- Do not claim completion without verification. (Section 3)
- **Do not add any send/write/response capability to the monitoring path, under any framing.** (Section 20)

---

## 43. Feature Development Workflow

**Phase A — Understand**
```
Read PRD (relevant §)
 ↓
Read architecture (relevant §)
 ↓
Read app flow (relevant screen/action)
 ↓
Read design (relevant component/section)
 ↓
Inspect existing code
```

**Phase B — Plan.** Identify: requirements, files, components, APIs, database changes, state changes, tests, documentation (Section 4/35).

**Phase C — Implement.** Implement the smallest complete solution that satisfies the requirement (Section 1, Principle 6).

**Phase D — Verify.** Check: functionality, UI (if applicable), responsive behavior, accessibility, security (especially zero-outbound if `network/`/pipeline touched), performance (2s latency budget), error handling, tests, regressions (Section 31).

**Phase E — Document.** Update `prd.md`/`architecture.md`/`appflow.md`/`design.md`/this file where the change affects them (Section 34).

---

## 44. Definition of Done

A feature is not complete until every applicable item is satisfied:

```
[ ] PRD requirement implemented
[ ] Architecture respected
[ ] App flow respected
[ ] Design system respected
[ ] Responsive behavior verified
[ ] Accessibility checked
[ ] Validation implemented (client UX + server boundary)
[ ] Error handling implemented
[ ] Loading state implemented
[ ] Empty state implemented
[ ] Success state implemented
[ ] Authentication/authorization checked (n/a for MVP, but explicitly considered)
[ ] Security reviewed — especially zero-outbound if network/pipeline touched
[ ] Tests added/updated
[ ] No unnecessary dependencies
[ ] No console/runtime errors
[ ] Existing functionality still works (regression check, Section 31)
[ ] Documentation updated if necessary (Section 34)
```

---

## 45. Pre-Commit Checklist

- [ ] Change traces to a real requirement (Section 4) or is explicitly a non-functional/infra task.
- [ ] No new send/write capability introduced on the monitoring path.
- [ ] No hardcoded secret, threshold, or magic number that belongs in `config/`.
- [ ] No hardcoded visual value that belongs in a `design.md` token.
- [ ] Tests updated/added and passing, including `tests/network/test_zero_outbound.py` if `network/` changed.
- [ ] No unrelated files touched.
- [ ] Documentation updated if this change affects a source document.
- [ ] Commit message clearly states what changed and why.

---

## 46. Emergency / Unclear Requirement Protocol

When an AI agent (or developer) encounters ambiguity:

- **If the ambiguity is low-risk** (e.g., internal variable naming, minor implementation detail with no behavioral consequence): follow existing project patterns (Section 8) and proceed.
- **If the ambiguity affects UI:** follow `design.md`; if `design.md` itself doesn't cover it, flag it explicitly rather than inventing a new visual pattern.
- **If the ambiguity affects user flow:** check `appflow.md`; if it's one of the already-documented gaps (Section 2's list), follow the resolution already given there (mostly by `design.md`); if it's a new, undocumented gap, flag it.
- **If the ambiguity affects architecture:** do not make a major architectural decision silently — flag it and propose an option, but do not merge/ship it as settled.
- **If the ambiguity affects security:** choose the safer approach (when in doubt, the option that keeps `network/` strictly read-only, that avoids storing new sensitive data, or that fails closed rather than open) and flag the issue explicitly.
- **If the ambiguity affects product behavior:** ask for clarification, or document the assumption explicitly (Section 2's conflict-recording process) rather than silently picking one.

In all cases: state the ambiguity, state the option chosen (if proceeding), and state why — never proceed silently on something that could plausibly be wrong.

---

## 47. Rule Priority

When instructions conflict, resolve in this order:

```
1. Security and data integrity (esp. zero-outbound guarantee, no payload storage)
2. Explicit PRD requirements (prd.md)
3. Established architecture (architecture.md)
4. Established application flow (appflow.md)
5. Established design system (design.md)
6. Existing code conventions
7. General engineering best practices
8. AI/agent preference
```

**The agent's personal preference (stylistic taste, a "better" pattern it knows, a different framework it prefers) never overrides an explicit project requirement.** If a best-practice instinct conflicts with something explicitly documented in `prd.md`/`architecture.md`/`appflow.md`/`design.md`, the documented decision wins — flag the tension (Section 46) rather than silently substituting the agent's preference.

---

## 48. Final AI Agent Contract

Before implementing any change, the AI coding agent must:

1. **Understand** the relevant sections of `prd.md`, `architecture.md`, `appflow.md`, and `design.md` for the task at hand.
2. **Inspect** the existing implementation — actual files, not assumptions from the folder tree.
3. **Follow** the established architecture (module boundaries, one-directional queue, pipeline shape) and design system (tokens, components, states) exactly, deviating only through the documented gap-resolution process (Section 2/46).
4. **Preserve** existing, working behavior — above all, the zero-outbound guarantee (Section 20) and the sub-2-second latency target (Section 29) — and preserve every other feature not in scope for the current change.
5. **Implement** appropriate validation, security, and error handling at the correct layer (Sections 22–24), never relying on the frontend as a security boundary.
6. **Verify** the result: functionality, tests, regressions, accessibility, responsiveness, and — whenever `network/` or the pipeline is touched — the zero-outbound test suite.
7. **Update documentation** whenever the change affects `prd.md`, `architecture.md`, `appflow.md`, `design.md`, or this file (Section 34).
8. **Never claim** something works, passes, or is complete without having actually verified it.
9. **Never invent** undocumented requirements, APIs, schema, endpoints, dependencies, or business logic (Section 40) — say `UNKNOWN — REQUIRES CLARIFICATION` instead.
10. **Never weaken** the product's core guarantee — that OneWay Sentinel observes, scores, and explains, and never, under any circumstance, sends anything back through the monitored link.

This contract governs every change, by every agent, for the lifetime of this project.
