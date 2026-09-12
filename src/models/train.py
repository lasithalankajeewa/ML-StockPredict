"""Command-line entry point for executing the model experiment notebook."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from src.config import PROJECT_ROOT


DEFAULT_NOTEBOOK = PROJECT_ROOT / "notebooks" / "03_model_experiments.ipynb"
DEFAULT_OUTPUT = PROJECT_ROOT / "notebooks" / "runs" / "03_model_experiments.ipynb"


def execute_training_notebook(
    notebook: Path = DEFAULT_NOTEBOOK,
    output: Path = DEFAULT_OUTPUT,
    *,
    timeout: int = -1,
) -> Path:
    """Execute all training, tuning, export, and evaluation cells in order."""
    notebook = notebook.resolve()
    output = output.resolve()
    if not notebook.is_file():
        raise FileNotFoundError(f"Training notebook does not exist: {notebook}")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        f"--ExecutePreprocessor.timeout={timeout}",
        "--output",
        output.name,
        "--output-dir",
        str(output.parent),
        str(notebook),
    ]
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--timeout",
        type=int,
        default=-1,
        help="Per-cell timeout in seconds; -1 disables the timeout.",
    )
    return parser.parse_args()


def main() -> None:
    """Execute the configured notebook and report its saved path."""
    args = parse_args()
    output = execute_training_notebook(args.notebook, args.output, timeout=args.timeout)
    print(f"Executed training notebook saved to {output}")


if __name__ == "__main__":
    main()
