"""The single entry point for reading curated data.

Everything in the project reads curated parquet through this function, which
enforces the data contract at read time: the sidecar must exist and the
sha256 must match. A reader that silently returned unverified bytes would
make the contract decorative, so it does not.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import polars as pl

CURATED_DIR = Path(__file__).resolve().parents[2] / "data" / "curated"


class CuratedDataError(FileNotFoundError):
    """Raised when a curated dataset or its sidecar is missing or corrupt."""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_curated(name: str) -> pl.DataFrame:
    """Load ``data/curated/<name>.parquet``, enforcing the data contract.

    Raises CuratedDataError naming the missing file if the parquet or its
    ``.meta.json`` sidecar is absent, or ValueError if the sidecar's sha256
    does not match the file on disk.
    """
    parquet = CURATED_DIR / f"{name}.parquet"
    sidecar = CURATED_DIR / f"{name}.meta.json"
    if not parquet.exists():
        raise CuratedDataError(f"curated dataset not found: {parquet}")
    if not sidecar.exists():
        raise CuratedDataError(f"sidecar not found: {sidecar}")
    meta = json.loads(sidecar.read_text())
    if meta.get("licence", "") == "":
        raise ValueError(f"empty licence in {sidecar}: UNVERIFIED data must not be read")
    digest = _sha256(parquet)
    if meta.get("sha256") != digest:
        raise ValueError(
            f"sha256 mismatch for {parquet}: sidecar declares "
            f"{meta.get('sha256')}, file is {digest}"
        )
    return pl.read_parquet(parquet)
