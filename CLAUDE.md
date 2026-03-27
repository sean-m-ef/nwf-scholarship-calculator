# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Criteria-based scholarship calculator for the [Nevada Women's Fund](https://nevadawomensfund.org). Evaluates applicants against weighted or scored criteria to support scholarship award decisions.

## Stack

- **Language:** Python
- **Potential frameworks:** Abstra (AI-powered process automation, `.abstra/` is gitignored) and/or Marimo (reactive notebooks, `__marimo__/` is gitignored) — check for installed packages before assuming either is in use
- **Package management:** uv is preferred (`.gitignore` includes `uv.lock` comments); fall back to pip/venv if not present

## Commands

These will depend on how the project is set up once source code exists. Standard patterns to use:

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt   # or: uv sync if pyproject.toml present

# Run (entry point TBD)
python main.py

# Tests
pytest

# Lint
ruff check .
ruff format .
```

## Problem Domain

**Scholarship distribution engine for the Nevada Women's Fund.**

- ~160 scholarships of varying dollar amounts; each may have boolean eligibility criteria
- ~200 recipients per cycle; each has a pre-determined dollar award amount and an attribute profile
- Total scholarship pool = total recipient awards (balanced by design before this engine runs)
- Scholarships may be split among multiple recipients; recipients may draw from multiple scholarships
- Minimum split amounts TBD — treat as a configurable constraint
- Fuzzy/soft criteria are a planned future extension (currently boolean gates only)
- Data in: CSV/Excel export; data out: Excel-importable file

## Architecture

This is a **linear programming assignment problem**. ~200 recipients × ~160 scholarships ≈ 32,000 allocation variables — tractable with PuLP + CBC solver.

**LP formulation:**
- Decision variable: `x[i,j]` = dollars allocated from scholarship `j` to recipient `i`
- Hard constraint: each recipient's allocations sum to their pre-determined award amount
- Hard constraint: each scholarship's allocations don't exceed its total amount
- Hard constraint: `x[i,j] = 0` if recipient `i` doesn't meet scholarship `j`'s criteria
- Secondary objective: prefer tighter criteria matches over general ones; minimize scholarships-per-recipient where possible
- Infeasibility detection: flag recipients whose attribute profile doesn't qualify them for enough scholarship funds to cover their award amount

**Future extension:** soft/fuzzy criteria become weighted penalty terms in the objective, not hard zeros.

**Planned stack:**
- `pandas` — data I/O and transformation
- `PuLP` — LP formulation and solve (CBC solver, bundled)
- `openpyxl` — Excel output
- `marimo` — browser-based UI (file upload → run → download); no CLI required for end user

## Architecture Notes

- Non-profit client context: post-handoff operators are non-engineers; prioritize operability over elegance
- Criteria and scholarship definitions must be data-driven (config/CSV), never hardcoded
- The engine should be runnable as a single CLI command against input CSVs
