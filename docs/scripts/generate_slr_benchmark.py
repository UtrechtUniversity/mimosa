"""Compatibility wrapper for the SLR AR6 diagnostic."""

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from diagnostics.slr_ar6 import (  # noqa: E402,F401
    COMPONENTS_OUTPUT,
    TOTALS_OUTPUT,
    calculate_benchmark_tables,
    write_benchmark_tables,
)


if __name__ == "__main__":
    for output_path in write_benchmark_tables():
        print(f"Wrote {output_path.relative_to(REPOSITORY_ROOT)}")
