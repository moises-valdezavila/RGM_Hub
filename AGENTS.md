# AGENTS.md

## Project overview

This repository is a Python retail-analysis project focused on sales, margin, inventory, and trend reporting. The codebase is data-pipeline oriented rather than application-oriented: it loads source data, normalizes category/store values, aggregates metrics in pandas DataFrames, and returns a reporting dataset.

The repository is intentionally lightweight and script-driven:

- `main.py` is the entry point.
- `tools/VG_reporte_detalle.py` contains the main report logic.
- `data/map.py` stores lookup dictionaries used to standardize store and department names.
- The project expects a local `services.to_sql` module to exist outside the repo for database access.

## Architecture

The main execution flow is:

1. `main.py` builds a `params` dictionary.
2. It calls `tools.VG_reporte_detalle.execute(params)`.
3. The report function normalizes input dates and builds a multi-step pandas workflow.
4. It merges sales, prior-year data, inventory, and warehouse metadata into a single result set.
5. It computes trend and margin metrics per month, store, category, family, and product code.

The business logic is strongly tied to the dataset conventions used by the project, especially:

- Spanish field names such as `sucursal`, `categoria`, `subcategoria`, `familia`, `minimov2`, and `inv_une`
- `codigo` built as `str(articulo) + str(subcuenta)`
- normalized mappings in `data/map.py`
- filtering by target group such as `Menudeo` and `Combinado`

## Commands

There is no formal build, lint, or test configuration in this repository.

- Run the project: `python main.py`
- Validate syntax: `python -m compileall .`
- If a test suite is later added, prefer running a single file rather than the entire suite, for example: `pytest path/to/test_file.py -q` or `python -m pytest path/to/test_file.py -q`

## Conventions to preserve

- Preserve the existing DataFrame-first style. Do not convert this repo into a class-heavy or framework-based application unless there is a clear reason and a broader repo-wide plan.
- Keep the Spanish business terminology and field names consistent with existing code.
- Update the normalization tables in `data/map.py` together with any logic that relies on those mappings.
- Consider `codigo` and the classification maps as part of the report contract; changing them requires coordinating downstream joins and aggregations.
- Keep changes surgical and targeted. This project is small but tightly coupled.

## Local environment and generated artifacts

- `to_sql.py` is intentionally ignored by Git and must stay local to the machine.
- Generated outputs such as `HUB_Output/` are also excluded from the repository.
- Do not commit local database credentials, generated reports, or environment-specific files.

## Expectations for future work

- Prefer changes that preserve the current reporting workflow and naming conventions.
- Validate any logic change by running the script in the normal project mode: `python main.py`.
- When adding features, keep the same pipeline shape rather than introducing multi-service abstractions or a new project structure.
