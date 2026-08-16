"""Bounded dataset inspection: ``python -m kinetiek.peek <name>``.

Prints shape, dtypes, null counts, and 5 rows. Total output is hard-capped
at 40 lines so that inspecting data can never blow the token budget.
"""

from __future__ import annotations

import sys

import polars as pl

MAX_LINES = 40


def peek(name: str) -> str:
    """Return the bounded summary for curated dataset ``name``."""
    from kinetiek.io import load_curated

    frame: pl.DataFrame = load_curated(name)
    lines: list[str] = [f"{name}: {frame.height} rows x {frame.width} cols"]
    lines.append("dtypes: " + ", ".join(f"{c}:{frame.schema[c]}" for c in frame.columns))
    nulls = ", ".join(
        f"{c}={frame[c].null_count()}" for c in frame.columns
    )
    lines.append("nulls: " + nulls)
    lines.append("head:")
    head = frame.head(5)
    remaining = MAX_LINES - len(lines)
    for row in head.iter_rows(named=True):
        if remaining <= 0:
            lines.append("…truncated")
            break
        lines.append("  " + ", ".join(f"{k}={v}" for k, v in row.items()))
        remaining -= 1
    return "\n".join(lines[:MAX_LINES])


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m kinetiek.peek <name>", file=sys.stderr)
        return 2
    print(peek(args[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
