"""Download and extract the required M5 competition files via Kaggle."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
COMPETITION = "m5-forecasting-accuracy"
REQUIRED_FILES = (
    "calendar.csv",
    "sales_train_evaluation.csv",
    "sell_prices.csv",
)


def download(*, force: bool = False, keep_archive: bool = False) -> None:
    """Download the Kaggle archive and extract only project input files."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    existing = [RAW_DIR / name for name in REQUIRED_FILES]
    if all(path.is_file() and path.stat().st_size > 0 for path in existing) and not force:
        print("All required M5 files already exist. Use --force to replace them.")
        return

    archive = RAW_DIR / f"{COMPETITION}.zip"
    command = [
        sys.executable,
        "-m",
        "kaggle",
        "competitions",
        "download",
        "-c",
        COMPETITION,
        "-p",
        str(RAW_DIR),
        "--force",
    ]
    print("Downloading M5 through the Kaggle API...")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as error:
        raise SystemExit(
            "Kaggle download failed. Accept the competition rules and configure "
            "kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY, then retry."
        ) from error

    if not archive.is_file():
        raise FileNotFoundError(f"Kaggle did not create the expected archive: {archive}")

    with ZipFile(archive) as source:
        members_by_name = {Path(name).name: name for name in source.namelist()}
        missing = sorted(set(REQUIRED_FILES).difference(members_by_name))
        if missing:
            raise ValueError("Competition archive is missing: " + ", ".join(missing))
        for filename in REQUIRED_FILES:
            destination = RAW_DIR / filename
            with source.open(members_by_name[filename]) as input_file:
                with destination.open("wb") as output_file:
                    shutil.copyfileobj(input_file, output_file)
            if destination.stat().st_size == 0:
                raise ValueError(f"Extracted file is empty: {destination}")
            print(f"Extracted {filename} ({destination.stat().st_size / 1024**2:.1f} MB)")

    if not keep_archive:
        archive.unlink()
    print(f"M5 data is ready under {RAW_DIR}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Replace existing files.")
    parser.add_argument(
        "--keep-archive", action="store_true", help="Keep the downloaded ZIP file."
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    download(force=arguments.force, keep_archive=arguments.keep_archive)
