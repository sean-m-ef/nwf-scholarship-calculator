# NWF Scholarship Calculator — Task List

## MVP Build

- [x] pyproject.toml + config.py + engine/__init__.py
- [ ] sample_data/ — synthetic CSVs (5 recipients, 4 scholarships)
- [ ] engine/loader.py + tests/test_loader.py
- [ ] engine/eligibility.py + tests/test_eligibility.py
- [ ] engine/solver.py + tests/test_solver.py (known-answer verification)
- [ ] engine/postprocess.py
- [ ] engine/exporter.py (verify by opening output)
- [ ] app.py — Marimo UI
- [ ] End-to-end scale test (200×160 synthetic data, solve <5s)

## Known MVP Shortcuts

1. Minimum split not enforced in LP — post-process flagging only; MIP required for enforcement
2. No fuzzy/soft criteria — boolean gates only
3. Minimize scholarships-per-recipient not formally enforced — heuristic approximation via tight-weight objective
4. No persistent storage / audit log — Excel output is the only record
5. Single-user, no concurrency
6. Balance assumed, not enforced — imbalanced input surfaces as infeasibility
