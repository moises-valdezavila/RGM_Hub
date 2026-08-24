# Typed Report Parameters Refactor Plan

## Purpose

Replace the untyped parameter dictionary used by the report entry point with an explicit `ReportParams` dataclass. This will make the report's input contract visible, reduce errors caused by repeated dictionary lookups, centralize defaults and validation, and preserve the existing date normalization behavior.

## Current Problem

`main.py` builds a dictionary and passes it to `execute`. The report module then extracts values with repeated `params_u.get(...)` calls in `assign_parameters`. Required values are not validated, unknown keys are silently ignored, and the operational values are duplicated between `main.py` and the notebook workflow.

`assign_parameters` currently supplies only the default `exportar_trimestre=False`; it does not centralize the numeric and date values. The report calculations themselves receive five separate arguments, which makes future parameter additions easier to miss.

## Target Design

Add a `ReportParams` dataclass at the report boundary with these fields:

- `dias_transcurridos`
- `dias_laborales`
- `fecha_inicio`
- `fecha_final`
- `exportar_trimestre`, defaulting to `False`

The dataclass will normalize date-like inputs to pandas timestamps and validate required values, positive numeric inputs, parseable dates, and a coherent date range. Unexpected fields should be rejected rather than silently ignored.

`execute` will accept `ReportParams`, and `logic` will consume the typed object. Existing calculations, database calls, Spanish field names, and business rules will remain unchanged.

## Implementation Steps

1. Define and test `ReportParams` in `tools/VG_reporte_detalle.py` or a small nearby module.
2. Move normalization and validation into the typed parameter boundary.
3. Update `main.py` to construct `ReportParams` directly.
4. Update `execute` and `logic` to use the typed object and remove `assign_parameters` dictionary extraction.
5. Preserve `exportar_trimestre` for contract continuity even though it is currently unused in the active Python path.
6. Keep unrelated constants, such as target filters, store filters, inventory factors, and `Minimo` sentinel values, outside the parameter object.

## Scope and Follow-up

The Python entry point and report module are in scope. `tools/VG_Reporte_detalle.ipynb` is intentionally excluded from this refactor because it contains a duplicated workflow. Create a follow-up ticket to migrate the notebook's parameter setup and keep it aligned with `ReportParams`.

The strict typed API is intentional. Existing known callers will be updated, and dictionary compatibility will not be retained unless an undiscovered external contract requires it.

## Verification

Add focused tests for valid construction, date normalization, the `exportar_trimestre` default, missing fields, invalid or non-positive numeric values, invalid dates, reversed date ranges, and unexpected fields. Add an execution-boundary test with mocked `services.to_sql` functions so the output contract can be checked without a live database.

Run the repository checks after implementation:

```bash
python -m compileall .
python main.py
```

The second command requires the local ignored `services.to_sql` dependency and its database access. If that environment is unavailable, record the limitation while retaining the unit and syntax checks.

## Files

- `main.py`: construct the typed parameter object.
- `tools/VG_reporte_detalle.py`: own the parameter contract and consume it in report execution.
- `tools/VG_Reporte_detalle.ipynb`: unchanged in this refactor; tracked by a follow-up ticket.
- `docs/adr/0001-use-typed-report-parameters.md`: record the architecture decision.
