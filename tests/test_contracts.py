"""Guard test: the data contract holds for every curated dataset.

Fails if any parquet in data/curated lacks a sidecar, if the sha256
mismatches, or if the licence is empty. Never weaken this test.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"

REQUIRED_FIELDS = ("name", "source_url", "publisher", "licence",
                   "retrieved_at", "sha256", "rows", "columns")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_curated_dir_exists():
    assert CURATED.is_dir(), f"missing curated data directory: {CURATED}"


def _parquets() -> list[Path]:
    return sorted(CURATED.glob("*.parquet"))


@pytest.mark.parametrize("parquet", _parquets(), ids=lambda p: p.stem)
def test_every_parquet_has_a_valid_sidecar(parquet: Path):
    sidecar = parquet.with_suffix("").with_suffix(".meta.json")
    assert sidecar.exists(), f"no sidecar for {parquet.name}"
    meta = json.loads(sidecar.read_text())
    for field in REQUIRED_FIELDS:
        assert field in meta, f"{sidecar.name}: missing field '{field}'"
    assert meta["licence"], f"{sidecar.name}: licence must not be empty"
    assert meta["sha256"] == _sha256(parquet), (
        f"{sidecar.name}: sha256 mismatch — rebuild the dataset"
    )
    assert meta["name"] == parquet.with_suffix("").name, (
        f"{sidecar.name}: 'name' must match the parquet stem"
    )
