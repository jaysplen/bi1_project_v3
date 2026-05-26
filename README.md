# VacuTech — Business Intelligence & Data Mining (DLMDSEBA02)

VacuTech Phase 2 analytics for three CRM-aligned business questions (W1/W2/W3).
Each work package uses one transparent, auditable algorithm with fixed
hyperparameters — designed for operational clarity and stakeholder review.

## Repository layout

| Path | Purpose |
|------|---------|
| `bi_pipeline.py` | End-to-end pipeline (load → W1 → W2 → W3) |
| `data/` | `repairs.csv`, `parts_used.csv`, `parts.csv` |
| `notebooks/` | Three CRISP-DM notebooks (W1, W2, W3) |
| `exports/` | Generated CSV / PNG / JSON artefacts |
| `tests/test_smoke.py` | Smoke tests on pipeline outputs |
| `PROJECT_HANDBOOK.md` | Business-first analytical handbook |
| `ACADEMIC_METHOD_JUSTIFICATION.md` | Academic sources and method justification (presentation) |
| `PROJECT_HANDBOOK.pdf` | Printable handbook |
| `build_handbook.py` | Regenerates the handbook PDF |
| `PRESENTATION.pptx` / `PRESENTATION.pdf` | 10-slide composite presentation deck |
| `build_presentation.py` | Regenerates `PRESENTATION.pptx` and `PRESENTATION.pdf` |

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Regenerate exports
python3 bi_pipeline.py

# Re-execute notebooks (from repo root)
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/W1_Inventory.ipynb \
  notebooks/W2_Repair_Duration.ipynb \
  notebooks/W3_QA_Failure_Risk.ipynb

# Rebuild handbook PDF (requires LibreOffice: soffice)
python3 build_handbook.py

# Rebuild the 10-slide presentation (PPTX + PDF; requires LibreOffice: soffice)
python3 build_presentation.py

# Tests
python3 -m pytest tests/ -v
```

## Methodology

| W | Algorithm | Rationale |
|---|-----------|-----------|
| W1 | Apriori (`min_support=0.05`, `min_lift=1.2`) | Auditable market-basket rules for PM add-on stocking |
| W2 | Decision Tree Regressor (`max_depth=6`) | Interpretable intake-time ETAs without scaling |
| W3 | Decision Tree Classifier (`max_depth=6`, threshold `0.30`) | Single governable operating point for pre-QA triage |

See `PROJECT_HANDBOOK.md` for business context, hyperparameter justification,
and cross-work-package performance interpretation. For tutor-facing literature
and scientific argumentation per W pain point, see `ACADEMIC_METHOD_JUSTIFICATION.md`.
The 10-slide composite presentation (CRM context → W1/W2/W3 → conclusion →
bibliography) lives in `PRESENTATION.pdf` (editable source: `PRESENTATION.pptx`).
