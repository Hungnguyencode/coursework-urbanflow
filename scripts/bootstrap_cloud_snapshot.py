"""Prepare the August 2026 UrbanFlow snapshot on Streamlit Community Cloud.

Designed to be invoked at the beginning of dashboard/1_Overview.py on the
separate deployment branch, not from the Windows refresh pipeline.

REQUIRES: a public GitHub Release named snapshot-2026-08 with both parquet
assets; the existing scripts/build_database.py with --period 202608.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = (
    "https://github.com/Hungnguyencode/coursework-urbanflow/"
    "releases/download/snapshot-2026-08"
)
TRIPS = ROOT / "data/processed/trips/trips_2026_08.parquet"
WEATHER = ROOT / "data/processed/weather/weather_2026_08.parquet"
DATABASE = ROOT / "data/analytics/urbanflow.duckdb"
METADATA = ROOT / "data/analytics/refresh_metadata.json"


def _download_if_missing(filename: str, destination: Path, min_bytes: int) -> None:
    if destination.is_file() and destination.stat().st_size >= min_bytes:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    url = f"{RELEASE}/{filename}"
    print(f"[UrbanFlow Cloud] Downloading {filename} from GitHub Release...", flush=True)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "UrbanFlow-Cloud-Snapshot/1.0"})
        with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as target:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
        if temporary.stat().st_size < min_bytes:
            raise RuntimeError(f"File downloaded but is unexpectedly small: {filename}")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def ensure_snapshot() -> None:
    """Fetch input Parquet and rebuild a Linux-compatible DuckDB as needed."""
    _download_if_missing(TRIPS.name, TRIPS, 100_000_000)
    _download_if_missing(WEATHER.name, WEATHER, 1_000)

    if not DATABASE.is_file() or DATABASE.stat().st_size < 1_000_000:
        print("[UrbanFlow Cloud] Building the August 2026 DuckDB...", flush=True)
        builder = ROOT / "scripts/build_database.py"
        if not builder.is_file():
            raise FileNotFoundError(f"Expected database builder not found: {builder}")
        # The repository uses the src/ layout. A subprocess started from
        # scripts/ needs the package path even if an editable install is absent.
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            str(p) for p in (ROOT / "src", ROOT)
        ) + os.pathsep + env.get("PYTHONPATH", "")
        subprocess.run(
            [sys.executable, str(builder), "--period", "202608"],
            cwd=ROOT,
            check=True,
            env=env,
        )
        if not DATABASE.is_file() or DATABASE.stat().st_size < 1_000_000:
            raise RuntimeError(f"Database builder did not produce {DATABASE}")

    # Do not reuse metadata containing C:\\Users\\... paths from Windows.
    metadata = {
        "requested_period": "2026-08",
        "active_period": "2026-08",
        "last_refresh": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trips_parquet": str(TRIPS.resolve()),
        "weather_parquet": str(WEATHER.resolve()),
        "database": str(DATABASE.resolve()),
    }
    METADATA.parent.mkdir(parents=True, exist_ok=True)
    if not METADATA.exists():
        METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        try:
            existing = json.loads(METADATA.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            existing = {}
        if any(existing.get(key) != metadata[key] for key in
               ("requested_period", "active_period", "trips_parquet", "weather_parquet", "database")):
            METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ensure_snapshot()
