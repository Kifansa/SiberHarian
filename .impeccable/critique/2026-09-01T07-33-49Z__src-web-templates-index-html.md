---
target: src/web/templates/index.html
total_score: 29
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 1
timestamp: 2026-09-01T07-33-49Z
slug: src-web-templates-index-html
---
Method: dual-agent (A: 5ea50aae-5e7c-4bb9-b656-7acfc5ea484a · B: 6ac69240-25b9-43dc-85d4-2d715c5284c8)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|:-----:|-----------|
| 1 | Visibility of System Status | 3 / 4 | SSE log streaming and refresh toasts are excellent; but the "Live Feed" pulse badge flashes continuously even on static historical database data. |
| 2 | Match Between System and Real World | 3 / 4 | Accurate Indonesian CTI terminology (*Vektor Serangan, Insiden Spesifik, Mitigasi*); but "Cloud Shell" branding clashes with on-premise local Ollama architecture. |
| 3 | User Control and Freedom | 3 / 4 | Pipeline can be aborted and modal dismisses on Esc; but navigation tabs disappear entirely on mobile screens (`hidden md:flex`), trapping mobile users. |
| 4 | Consistency and Standards | 3 / 4 | Strong adherence to Sentinel Spectrum color codes; but the header search input is non-functional (false affordance). |
| 5 | Error Prevention | 3 / 4 | Pipeline run button disables during execution to prevent race conditions; but non-functional search and placeholder footer links induce user confusion. |
| 6 | Recognition Rather Than Recall | 4 / 4 | Outstanding visual chunking with explicit severity badges, CVSS score pills, date counters in Arsip, and baseline comparison tables (+X% growth). |
| 7 | Flexibility and Efficiency of Use | 2 / 4 | Lacks power-user keyboard shortcuts (e.g. `1`-`3` tab switching, `/` search focus), no clipboard "Copy Mitigation" action for SOC tickets, and no client-side filtering by vendor/keyword. |
| 8 | Aesthetic and Minimalist Design | 3 / 4 | Clean typography, subtle elevation (`card-hover-lift`), and high signal-to-noise ratio; but the marketing Hero header on Beranda pushes operational data below the fold. |
| 9 | Error Recovery | 3 / 4 | Terminal logs format `ERROR` and `WARNING` levels in distinct red/amber; toast notifies failed manual refresh; but no inline retry button exists if initial `/api/beranda` fetch fails. |
| 10 | Help and Documentation | 2 / 4 | Informative empty states guide the user to run the pipeline; but footer links (`Dokumentasi`, `Status API`) are dead `#` anchors, and no tooltips explain CTI baseline metrics (e.g. 3H vs 4H logic). |
| **Total** | | **29/40** | **Good / Competent (Ready for Enterprise Polish)** |

## Design Specificity Verdict

**Verdict: HIGHLY GROUNDED (Domain-Specific CTI Terminal with minor SaaS Artifacts)**

SiberHarian possesses a distinct, purpose-built identity as an on-premise Cyber Threat Intelligence (CTI) terminal for Diskominfo Jawa Timur. The visual composition, semantic color rules (Crimson `#dc2626` strictly for active incidents & CVSS 9.0–10.0, Amber `#d97706` for High severity warnings, Cobalt Blue `#2563eb` for intel/governance), and dual-font pairing (Inter for narrative analysis + JetBrains Mono for CVSS scores, CVE IDs, and growth percentages) firmly establish the product in its domain.

**Deterministic Scan Telemetry:**
- **Automated Detector:** 33 total findings (4 warnings, 29 advisories).
- **False Positives (3):** `overused-font` on Inter (mandated by `DESIGN.md`), `design-system-font` on Material Symbols (icon font), and `dark-glow` on `.terminal-glow` (documented token).
- **True Findings (30):**
  1. Undocumented color `#e8f0fe` in `index.html:55` (token drift from `#eff6ff`).
  2. 28 arbitrary font sizes (`text-[11px]`, `text-[16px]`, `text-[20px]`, `text-[28px]`) causing typography scale drift and low contrast ratios (2.5:1 on `text-slate-400`).
  3. Missing ARIA roles on navigation tabs, modal container, and search input.

## Overall Impression

SiberHarian demonstrates thoughtful, production-grade frontend architecture. The separation into three distinct workspaces (**Beranda** for immediate daily triage, **Arsip** for historical 7-day recall, and **Tren Siber** for strategic intelligence) perfectly aligns with the operational workflows of Diskominfo Jawa Timur. The interface delivers high signal density without feeling overwhelming. The key opportunities for improvement lie in eliminating dead UI elements (the non-functional search input and placeholder footer links), restoring responsive mobile navigation, streamlining top-heavy vertical space on Beranda, and upgrading accessibility compliance.

## What's Working

1. **Precision CTI Visual Language & Typography Pairing:**
   Strict adherence to `The Technical Clarity Rule` (JetBrains Mono for technical metrics and Inter for analytical prose) creates immediate domain credibility and rapid scanning efficiency.
2. **Execution Transparency & Real-Time Feedback:**
   The real-time Server-Sent Events (SSE) terminal monitor, animated count-up metrics, flash card highlights, and toast notifications provide exceptional confidence during AI pipeline executions.
3. **Structured Semantic Parsing in Tren Tab:**
   `renderLaporanCards` in `tren.js` elegantly transforms raw LLM responses into tactical cards with tailored iconography (`local_fire_department`, `shield`, `bolt`) and embedded data tables.

## Priority Issues

### [P0] Mobile Navigation Completely Absent on Narrow Screens
- **Why it matters:** On screens `< md`, navigation tabs are hidden (`hidden md:flex`), preventing analysts on mobile devices (e.g. triaging alerts from Telegram) from switching to Arsip or Tren.
- **Fix:** Implement a responsive bottom navigation bar or horizontal scrollable tab strip for mobile viewports.
- **Suggested command:** `/impeccable adapt src/web/templates/index.html`

### [P1] Modal Accessibility & Keyboard Focus Trapping Missing
- **Why it matters:** The incident detail modal lacks `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and keyboard focus trapping, leaking focus to background elements and failing WCAG AA compliance.
- **Fix:** Add semantic dialog ARIA attributes to `#modal-box` and trap Tab focus within the active modal in `modal.js`.
- **Suggested command:** `/impeccable harden src/web/static/js/modal.js`

### [P2] Non-Functional Header Search Input (False Affordance)
- **Why it matters:** The search input in the header creates an expectation of searchability but contains no JavaScript event listeners or form submission, violating user trust and error prevention.
- **Fix:** Implement client-side instant filtering across loaded incident titles/summaries with highlight matching, or connect to the archive search API.
- **Suggested command:** `/impeccable clarify src/web/templates/index.html`

### [P3] Terminology & Brand Inconsistency ("Cloud Shell")
- **Why it matters:** Labeling the terminal as `"Cloud Shell"` contradicts Product Principle #2 (*Local-First On-Premise Sovereign Intelligence*) and creates confusion about external cloud transmission.
- **Fix:** Rename label to `"Local Engine - Pipeline Monitor"` or `"Terminal Pemrosesan Intelijen"`.
- **Suggested command:** `/impeccable polish src/web/templates/index.html`

## Persona Red Flags

- **Alex (Senior SOC Analyst / Power User):** No keyboard shortcuts for tab navigation (`1`-`3`) or modal dismissal; no "Copy Mitigation" button in modal to quickly paste into ticketing systems; forced to scroll past the large Hero banner every morning to see incident cards.
- **Jordan (First-Time Security Operator):** Confused by the `"Cloud Shell"` title on an internal on-premise server; no tooltip explanation for why CVE trends compare 3-day recent vs 4-day baseline.
- **Sam (Accessibility-Dependent User):** Screen reader reads raw icon names ("inventory_2", "insights") due to missing `aria-hidden="true"`; modal focus escapes to underlying page; `text-slate-400` labels have 2.5:1 contrast on white (fails WCAG AA 4.5:1).
- **Diskominfo Jatim Incident Responder:** Cannot access Tren or Arsip on smartphone during weekend incident triage due to `hidden md:flex` on navigation.

## Minor Observations

1. **Dead Footer Links:** Links for `Dokumentasi`, `Status API`, `Privasi`, and `Ketentuan` point to empty `#` anchors.
2. **Token Drift:** Color `#e8f0fe` in body gradient should be unified with `#eff6ff` (`primary-light`).
3. **Arbitrary Font Sizes:** 28 instances of `text-[11px]` and arbitrary icon sizes should be mapped to standard Tailwind tokens (`text-xs`, `text-xl`, `text-3xl`).

## Questions to Consider

1. Should the Beranda tab collapse the Hero title and Terminal into a compact status pill once data is loaded, prioritizing today's incident cards at the top of the viewport?
2. Would an "Ekspor Laporan (PDF/Markdown)" button in the Tren tab accelerate Diskominfo daily executive briefings?
3. Should the header search bar filter dynamically across both today's active feed and the 7-day archive cache with instant keyword highlighting?
