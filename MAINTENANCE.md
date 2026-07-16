# Maintenance

## Annual refresh

The next scheduled annual refresh is **2027-01**. Reassess labor agreements,
energy prices, robot pricing, reliability assumptions, source licenses, and
external-validity disclosures. Regenerate the reports and review whether the
decision statement remains supported before publishing a new release.

## Between refreshes

Correct material data, model, or source errors promptly through the governed
finding workflow. Record assumption changes in `config/` and regenerate the
assumption register rather than editing generated outputs by hand.

Recruiter PDFs (`Executive_Summary_*.pdf`, `exhibit_deck.pdf`) are regenerated
with `make exec-summary` (Quarto typst). `scripts/render_decision_pdfs.py` is an
emergency fallback only — never commit its ReportLab output.

## Coverage ratchet

The July 2026 full-suite measurement after F-240 is **91%**, so the enforced
threshold is **`--cov-fail-under=90`** in `pyproject.toml`. Raise it in small
verified increments toward higher bars as remaining gaps shrink; do not claim a
higher enforced threshold until the suite measures it. Omit list remains
`*/tests/*` and `*/__main__.py` only.
