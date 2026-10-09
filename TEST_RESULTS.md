# Validation of ticker lookup and recommendation changes

Validated on 2026-10-09 in the development environment.

- `python -m unittest discover -s tests`: **42 tests passed**, approximately 3 seconds.
- `python -m compileall -q app.py cli.py analytics data reporting tests`: passed.
- `git diff --check`: passed.

Coverage includes arbitrary ticker inputs and `.VN` normalization; listing all provider symbols; DNSE priority; Vietcap statement/year normalization; same-ticker cache isolation; rejecting fabricated prices and legacy financial caches; missing financial data; distinct recommendation evidence; overbought/bearish/stale-price safeguards; negative cash flow excluded from DCF; Streamlit full/partial/error flows; and PDF generation with the shared recommendation results.

Tests use explicit synthetic fixtures and mocked network providers. They do not establish live availability or accuracy of Vietcap, DNSE, VNDirect, or Yahoo Finance. A direct Vietcap metadata request returned HTTP 400 in this environment, so successful live retrieval is not claimed. DNSE was validated without accessing credentials or executing authenticated requests.

Macro facts, industry benchmarks, DCF growth assumptions, and scenario probabilities still require source verification or model calibration before being treated as current market research.
