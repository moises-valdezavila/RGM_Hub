# ADR 0001: Use Typed Report Parameters

- Status: Accepted
- Date: 2026-08-23

## Context

The report entry point in `main.py` now constructs a typed input object instead of passing a raw dictionary. The `ReportParams` dataclass localizes the input contract in one place and makes required values explicit at construction time.

The underlying report flow still depends on a local `services.to_sql` module for SQL access, and the project remains intentionally lightweight and script-driven. This makes the parameter boundary the right place to enforce validation without introducing extra infrastructure.

## Decision

Use a strict `ReportParams` dataclass as the input contract for the report.

The dataclass currently:

- represents the five report parameters;
- defaults `exportar_trimestre` to `False`;
- normalizes date-like inputs to pandas timestamps;
- validates required values, positive numeric inputs, parseable dates, and date ordering; and
- rejects non-typed callers at the boundary by requiring `execute()` to receive a `ReportParams` instance.

`main.py` constructs `ReportParams`, and `execute()` passes the typed object into `logic()`. The current report calculations, database calls, field names, and unrelated business constants remain unchanged.

## Alternatives Considered

### Keep the dictionary and `.get()` calls

This requires the fewest edits but preserves silent omissions, late failures, and an implicit input contract. It does not address the source of the error-prone behavior.

### Keep a dictionary but add manual validation

This would improve failures but leave the contract distributed across string keys and repeated extraction code. It adds validation without removing the maintenance problem.

### Use a broader configuration framework

A settings framework or separate configuration service would be disproportionate for this lightweight, script-driven repository and would increase dependencies and migration cost.

## Consequences

Positive consequences:

- Callers see the complete report contract at construction time.
- Invalid inputs fail early with focused errors.
- Attribute access removes repeated string-key lookups.
- Defaults and normalization have one owner.
- The execution boundary is explicit and easier to extend safely.

Tradeoffs:

- Callers must construct `ReportParams` instead of passing raw dictionaries.
- The notebook workflow remains out of sync and is tracked as a follow-up item.
- The active report logic still relies on the local database-access module, so end-to-end execution requires that environment.
- `exportar_trimestre` remains in the contract even though the current Python path does not actively use it.

## Scope Boundaries

This decision does not move target filters, store filters, inventory factors, sentinel values, or other business rules into the dataclass. Those are separate concerns and should be refactored independently if needed.

The notebook migration is explicitly a follow-up item: update `tools/VG_Reporte_detalle.ipynb` to construct or consume `ReportParams` once the Python implementation is complete.

## Verification

The repository currently verifies the boundary with focused tests for:

- valid construction;
- date normalization;
- reversed date rejection;
- rejection of raw dict input; and
- execution returning a DataFrame for a valid typed input.

The implemented checks are run with:

```bash
python -m unittest tests.test_report_params -v
python -m compileall .
```

The full `python main.py` execution path still depends on the local ignored `services.to_sql` dependency and its database access, so that step is environment-dependent rather than repository-dependent.
