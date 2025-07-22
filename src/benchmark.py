# benchmark.py

import time
import pandas as pd
from calendar_generator import generate_calendar_table
from calendar_utils import get_available_workers

def run_benchmark(start_date, end_date, freq, regions, column_groups, n_workers, description):
    """
    Runs a single benchmark for calendar generation and prints the duration.
    """
    print(f"\n--- Running Benchmark: {description} ---")
    start_time = time.time()
    try:
        df = generate_calendar_table(
            start_date,
            end_date,
            freq=freq,
            regions=regions,
            column_groups=column_groups,
            n_workers=n_workers,
        )
        end_time = time.time()
        duration = end_time - start_time
        print(f"Benchmark completed in {duration:.2f} seconds. Generated {len(df):,} rows.")
    except Exception as e:
        print(f"Benchmark failed: {e}")

if __name__ == "__main__":
    print("Starting Calendar Table Generator Benchmarks...")

    # Define common parameters
    default_regions = ["Europe/Rome", "US/Eastern"]
    all_column_groups = [
        "time",
        "standard",
        "fiscal",
        "additional",
        "country_business",
        "regional",
        "extra",
    ]
    available_workers = get_available_workers()

    # Benchmark 1: Small range, daily, all columns, single worker
    run_benchmark(
        start_date="2023-01-01",
        end_date="2023-01-31",
        freq="D",
        regions=default_regions,
        column_groups=all_column_groups,
        n_workers=1,
        description="Small range (1 month), Daily, All columns, 1 Worker",
    )

    # Benchmark 2: Small range, daily, all columns, max workers
    run_benchmark(
        start_date="2023-01-01",
        end_date="2023-01-31",
        freq="D",
        regions=default_regions,
        column_groups=all_column_groups,
        n_workers=available_workers,
        description=f"Small range (1 month), Daily, All columns, {available_workers} Workers",
    )

    # Benchmark 3: Medium range, daily, all columns, max workers
    run_benchmark(
        start_date="2023-01-01",
        end_date="2023-12-31",
        freq="D",
        regions=default_regions,
        column_groups=all_column_groups,
        n_workers=available_workers,
        description=f"Medium range (1 year), Daily, All columns, {available_workers} Workers",
    )

    # Benchmark 4: Medium range, hourly, all columns, max workers (more rows)
    run_benchmark(
        start_date="2023-01-01",
        end_date="2023-01-07", # One week hourly
        freq="H",
        regions=default_regions,
        column_groups=all_column_groups,
        n_workers=available_workers,
        description=f"Medium range (1 week), Hourly, All columns, {available_workers} Workers",
    )

    # Benchmark 5: Medium range, daily, fewer column groups, max workers
    run_benchmark(
        start_date="2023-01-01",
        end_date="2023-12-31",
        freq="D",
        regions=default_regions,
        column_groups=["standard", "regional"],
        n_workers=available_workers,
        description=f"Medium range (1 year), Daily, Standard + Regional columns, {available_workers} Workers",
    )

    print("\nAll benchmarks completed.")
