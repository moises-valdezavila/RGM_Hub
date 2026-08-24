# RGM_Hub

RGM_Hub is a Python data-processing and reporting repository for retail sales analysis. It consolidates sales history, inventory information, and normalized category/store mappings into a single reporting pipeline used to evaluate margins, trends, and stock coverage across stores.

## What this project does

The project reads operational data, normalizes store and category labels, and computes business KPIs such as:

- sales by month and store
- margin comparisons against the prior year
- inventory movement and coverage metrics
- trend estimates for ongoing period performance

The main workflow is implemented in `tools/VG_reporte_detalle.py` and is executed from `main.py`.

## Repository structure

- `main.py` — entry point that prepares parameters and runs the report.
- `tools/VG_reporte_detalle.py` — primary ETL and analytics logic.
- `data/map.py` — store and category normalization maps used throughout the calculations.
- `.gitignore` — excludes local runtime artifacts such as `to_sql.py` and `HUB_Output/`.

## Prerequisites

This project expects a local Python environment with the required data-science dependencies available, including pandas and numpy. It also expects a local `services.to_sql` module outside the repository for database access.

## Usage

Run the report with:

```bash
python main.py
```

Optional syntax validation:

```bash
python -m compileall .
```

## Notes

- This repository does not currently include a formal build, lint, or test setup.
- The project is script-driven and environment-dependent rather than packaged as a reusable library.
- Business logic and field naming are intentionally aligned with the Spanish retail terminology used in the source data.
