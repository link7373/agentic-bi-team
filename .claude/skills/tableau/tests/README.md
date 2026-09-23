# Tableau builder & validator tests

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> Regression suite for `../scripts/twb_builder.py` and `../scripts/validate_twb.py`.
> Fixtures are built in a temp directory and cleaned up - nothing touches the repo.

```bash
python .claude/skills/tableau/tests/run_tests.py      # -v to show each finding
```

Exit 0 = all pass. **Run it after any change to the builder or the validator.**

## What it asserts

1. Every chart recipe builds and passes schema validation.
2. A clean generated workbook validates with zero errors and exit 0.
3. Each injected defect raises **its specific code** at the **right severity**.
4. The builder refuses a bad spec with `SpecError` rather than emitting bad XML.
5. Building the same spec twice is byte-identical (so git diffs stay meaningful).

## Why the defect cases exist

Three of them encode failures that reached Tableau and were only caught by a
human opening the file:

| Case | Code | What it caught |
|---|---|---|
| `unqualified_ref` | `REF006` | `[Multiple Values]` without its datasource qualifier - Tableau drops the field, sheet renders nothing |
| `missing_viewpoint` | `REF007` | a dashboard whose window declares no `<viewpoint>` for a sheet it shows - Tableau refuses the whole dashboard |
| `column_drift` | `REF001` | a shelf pointing at a column no longer declared on the datasource |

None of them is visible to XSD validation. That is the point: the schema layer
proves the file is well-formed, and these prove it means something.

Requires `lxml` for the schema layer. Without it those assertions are reported
as **skipped**, not silently passed.
