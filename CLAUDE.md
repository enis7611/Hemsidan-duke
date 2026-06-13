# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The marketing website for **Duke Systems AB** (duke.se) — a Nordic ExtendSim distributor. It is a single static **one-page site** with no build system, no tests, no frameworks, and no backend. The entire site (HTML + CSS + JS) lives inline in one file: `src/index.html` (~2400 lines).

The site content is in **Swedish** (with a runtime English toggle). Project docs are also Swedish. `docs/HANDOFF_CONTEXT.md` is the authoritative project brief — read it before making content or design changes.

## Running / previewing

No build step. Open `src/index.html` directly in a browser, or serve the folder:

```powershell
python -m http.server 8000   # then open http://localhost:8000/src/index.html
```

There is no lint or test command. "Testing" is the manual sanity checklist in `docs/HANDOFF_CONTEXT.md` §10 (toggle SV/EN, scroll-reveal, submit form, mobile hamburger, nav anchors).

## Architecture & conventions that span the file

**Single-file, inline everything.** Keep CSS in the `<style>` block and JS in the `<script>` block at the bottom. Do not split into external files or add tooling while the site stays a one-pager (this is a deliberate decision so it can be pasted into WordPress — see HANDOFF §8).

**Design tokens are locked in `:root` CSS variables** (the "Mint & Stål" theme). Never hardcode a hex color if a variable exists; change the variable to recolor globally. The palette and its history are documented in HANDOFF §3.

**Bilingual system (the main gotcha).** All visible text is driven by a single `translations` object with `sv` and `en` keys (defined ~line 2078). `applyLang(lang)` calls `setText('elementId', L.key)` for every element. Default is `currentLang = 'sv'`. When you add or change any visible text you MUST:
1. Give the element a unique `id`.
2. Add the key to **both** the `sv` and `en` objects in `translations`.
3. Add a `setText('id', L.key)` line in `applyLang()`.
A missing `setText` silently blanks the element on toggle — always test the SV/EN switch after text edits.

**Contact form is `mailto:`, not a backend.** `handleSubmit()` validates name/email/GDPR checkbox, builds a `mailto:info@duke.se` link, and opens the user's mail client. No server.

**Sections** are anchor-linked `<section id="...">` blocks (`#hero`, `#tjanster`, `#varfor`, `#extendsim`, `#mcp`, `#konsult`, `#branscher`, `#cta-banner`, `#om-oss`, `#kontakt`, `#sekretesspolicy`). Nav links and the mobile menu point at these ids. Animations are scroll-reveal via `IntersectionObserver` on `.reveal` elements.

**Responsive breakpoints:** `768px` (mobile / hamburger), `1024px` (grid), `480px` (small screens).

## Content guardrails (from HANDOFF §1 — do not violate)

The company sells exactly **three things**: ExtendSim (simulation software), ExtendSim MCP (AI control via Model Context Protocol), and consulting (simulation + IT infrastructure: Commvault, Windows Server, Azure).

**These deprecated products must never appear on the site:** NetApp, Bridgeworks, Spectra Logic, ForecastPRO, Komprise, Office 365 consulting, Visma, RPA, generic IT support, TeamViewer remote support.

The tagline is locked: **"Vi löser problemet. Sedan 1988."** CTAs use "Berätta om ditt problem" rather than generic "Kontakta oss".

## docs/

- `docs/HANDOFF_CONTEXT.md` — authoritative brief: design system, section map, feature mechanics, open TODOs, WordPress migration plan.
- `docs/Nytt_matreal/` — new source material not yet on the site (e.g. the second MCP server "SimulationsMCP_build" for the `#mcp` section, and the ExtendMQTT PRD). Treat as input to draft from, not published copy.
