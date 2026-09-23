#!/usr/bin/env python3
"""Write a Tableau .hyper extract, and package a workbook as .twbx.

WHY THIS EXISTS
---------------
Tableau Public cannot open a workbook with a live connection at all - not just
that it cannot publish one:

    Workbooks saved to Tableau Public must use extracts. The data source,
    <name>, is not an extract. Error Code: 3C242D89

So for anyone whose only Tableau is the free Public app - which is the common
case for this team - a CSV or SQL connection is not enough. The workbook needs a
.hyper extract, and the extract has to travel inside a .twbx package because the
<extract> connection stores a package-relative path:

    <connection class='hyper' dbname='Data/Extracts/exec_kpis.hyper' ... />

Tableau Desktop has no such restriction and opens a live connection fine.

DEPENDENCY
----------
Requires `tableauhyperapi` (official Tableau, pip-installable, free to use but
proprietary-licensed, ships ~70MB of native binaries). It is imported lazily and
ONLY on the extract path, so the rest of this module stays dependency-free:

    pip install tableauhyperapi

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

# The schema/table names Tableau uses inside every extract it writes. The .twb
# refers to them as [Extract].[Extract]; do not rename them.
EXTRACT_SCHEMA = "Extract"
EXTRACT_TABLE = "Extract"

# Where the extract lives inside a .twbx. Tableau writes this exact prefix.
PACKAGE_DATA_DIR = "Data/Extracts"


def _hyper_type(datatype: str):
    """Map a spec datatype to a Hyper SqlType."""
    from tableauhyperapi import SqlType
    mapping = {
        "string": SqlType.text,
        "integer": SqlType.big_int,
        "real": SqlType.double,
        "date": SqlType.date,
        "datetime": SqlType.timestamp,
        "boolean": SqlType.bool,
    }
    if datatype not in mapping:
        raise ValueError(f"unsupported datatype {datatype!r}; "
                         f"expected one of {sorted(mapping)}")
    return mapping[datatype]()


def _coerce(value, datatype: str):
    """Coerce a Python value to what Hyper expects for the column type."""
    if value is None or value == "":
        return None
    if datatype == "date":
        import datetime as _dt
        if isinstance(value, _dt.date):
            return value
        return _dt.date.fromisoformat(str(value)[:10])
    if datatype == "datetime":
        import datetime as _dt
        if isinstance(value, _dt.datetime):
            return value
        return _dt.datetime.fromisoformat(str(value))
    if datatype == "integer":
        return int(value)
    if datatype == "real":
        return float(value)
    if datatype == "boolean":
        return bool(value)
    return str(value)


def write_hyper(fields: list[dict], rows, out_path: str | Path) -> Path:
    """Write rows into a .hyper extract.

    `fields` is the same list the workbook spec uses: {name, datatype, role}.
    `rows` is an iterable of sequences, in the same column order as `fields`.
    """
    try:
        from tableauhyperapi import (
            Connection, CreateMode, HyperProcess, Inserter, TableDefinition,
            TableName, Telemetry,
        )
    except ImportError as e:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "tableauhyperapi is required to build a .hyper extract.\n"
            "  pip install tableauhyperapi\n"
            "It is only needed for the extract path - CSV and SQL connections "
            "work without it, but Tableau Public cannot open those."
        ) from e

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    table = TableName(EXTRACT_SCHEMA, EXTRACT_TABLE)
    columns = [
        __import__("tableauhyperapi").TableDefinition.Column(
            f["name"], _hyper_type(f["datatype"]))
        for f in fields
    ]
    definition = TableDefinition(table_name=table, columns=columns)
    types = [f["datatype"] for f in fields]

    # Telemetry is opt-out; this team does not send usage data to Tableau.
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(endpoint=hp.endpoint, database=str(out),
                        create_mode=CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema(EXTRACT_SCHEMA)
            conn.catalog.create_table(definition)
            with Inserter(conn, definition) as ins:
                for row in rows:
                    ins.add_row([_coerce(v, t) for v, t in zip(row, types)])
                ins.execute()
    return out


def package_twbx(twb_path: str | Path, hyper_path: str | Path | None,
                 out_path: str | Path) -> Path:
    """Zip a .twb (plus its extract) into a .twbx.

    A .twbx is an ordinary zip. The .twb sits at the root and the extract goes
    under Data/Extracts/, which is the package-relative path the <extract>
    connection's @dbname points at.
    """
    twb = Path(twb_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(twb, twb.name)
        if hyper_path:
            hp = Path(hyper_path)
            z.write(hp, f"{PACKAGE_DATA_DIR}/{hp.name}")
    return out


def package_relative_hyper(name: str) -> str:
    """The @dbname a .twb should use for an extract of this name."""
    return f"{PACKAGE_DATA_DIR}/{name}.hyper"
