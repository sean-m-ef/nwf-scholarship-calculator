# NWF Scholarship Calculator — Task List

## MVP Build — Complete

- [x] pyproject.toml + config.py + engine/__init__.py
- [x] sample_data/ — synthetic CSVs
- [x] engine/loader.py + tests/test_loader.py
- [x] engine/eligibility.py + tests/test_eligibility.py
- [x] engine/solver.py + tests/test_solver.py (28 passing)
- [x] engine/postprocess.py
- [x] engine/exporter.py
- [x] app.py — Marimo UI
- [x] End-to-end scale test (200×160, <1s solve)
- [x] Mac/Windows double-click launchers (launch.command, launch.bat)

## Bug Fixes Applied

- [x] full_name lowercased in output — fixed in loader.py
- [x] NaN in numeric columns silently coerced to False — raises ValueError
- [x] Missing recipient attribute silently excluded everyone — raises ValueError
- [x] No validation on award_amount / scholarship amount positivity — added
- [x] Duplicate recipient_id / scholarship_id silent corruption — added check
- [x] LP rounding before sum caused $0.01 display errors — fixed in solver.py
- [x] LP objective weights inverted (used general scholarships before tight ones) — fixed

## Test Run Against Client Data (2026-03-30)

- [x] Extracted 86 funded recipients + 99 scholarships from NWF Scholarships to SM.xlsx
- [x] Mapped eligibility criteria from text descriptions to crit__ schema
- [x] Solver: Optimal, 0.19s, all 86 funded, $265,423.89, no over-allocation
- [x] 23 scholarships match client's manual allocation exactly
- [x] Remaining diffs explained: LP has multiple valid solutions + 4 missing data points

## Pending — Awaiting Client

- [ ] AHEC membership list (affects 4 scholarships, ~$20k)
- [ ] Domestic violence flag (affects 2 scholarships, ~$11k)
- [ ] Amanda Fisher (incarceration history, ~$483)
- [ ] Soroptimist membership list (~$30k)
- [ ] Clarify: are all 219 applicants funded this cycle or just the 86? What are award amounts for the rest?
- [ ] Full recipient dataset with names (current output shows "Recipient N")

## Known MVP Shortcuts (Documented)

1. Minimum split not enforced in LP — post-process flagging only; MIP required for enforcement
2. No OR criteria — boolean AND gates only; "nursing or medicine" type criteria simplified or dropped
3. Minimize scholarships-per-recipient not formally enforced — tight-weight heuristic approximates it
4. No persistent storage / audit log — Excel output is the only record
5. Single-user, no concurrency
6. Balance assumed, not enforced — imbalanced input surfaces as infeasibility
