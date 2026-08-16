"""Guard test: no bare numbers in essays (the anti-hallucination rule).

Every numeral in essays/*.md must be inside a {{metric:...}} or {{fig:...}}
directive, be a 4-digit year in 1800-2100, or sit on a line ending with the
explicit ``<!-- lit -->`` allowlist comment (use logged in progress.md).
Never weaken this test: it is the difference between a data project and a
plausible-sounding blog.
"""

from __future__ import annotations

import re
from pathlib import Path

ESSAYS = Path(__file__).resolve().parents[1] / "essays"

DIRECTIVE = re.compile(r"\{\{[^}]*\}\}")
NUMERAL = re.compile(r"\d+")


def essay_files() -> list[Path]:
    return sorted(p for p in ESSAYS.glob("*.md")) if ESSAYS.is_dir() else []


def test_essays_directory_exists():
    assert ESSAYS.is_dir(), f"missing essays directory: {ESSAYS}"


def test_no_bare_numbers():
    offenders: list[str] = []
    for path in essay_files():
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            where = f"{path.name}:{lineno}"
            if line.rstrip().endswith("<!-- lit -->"):
                continue
            stripped = DIRECTIVE.sub("", line)
            for hit in NUMERAL.findall(stripped):
                if len(hit) == 4 and 1800 <= int(hit) <= 2100:
                    continue  # a year in prose is allowed
                offenders.append(f"{where}: bare number '{hit}' in: {line.strip()}")
    assert not offenders, "bare numbers found:\n" + "\n".join(offenders)
