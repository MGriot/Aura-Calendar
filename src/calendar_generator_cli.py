# calendar_generator_cli.py

import argparse
import os
from calendar_generator import generate_calendar_table
from calendar_utils import save_calendar, get_available_workers


def main():
    parser = argparse.ArgumentParser(
        description="Generate a comprehensive calendar table with timezone support."
    )
    parser.add_argument(
        "--start", required=True, help="Start datetime (e.g., '2020-01-01')"
    )
    parser.add_argument(
        "--end", required=True, help="End datetime (e.g., '2025-12-31')"
    )
    parser.add_argument(
        "--freq", default="D", help="Frequency (e.g., '5min', 'D', 'H')"
    )
    parser.add_argument(
        "--regions",
        nargs="*",
        default=["Europe/Rome", "US/Eastern"],
        help="List of timezones (e.g., 'US/Eastern Europe/Rome')",
    )
    parser.add_argument(
        "--column_groups",
        nargs="*",
        default=[
            "time",
            "standard",
            "fiscal",
            "additional",
            "country_business",
            "regional",
            "extra",
        ],
        help="List of column groups to include (e.g., 'standard fiscal')",
    )
    parser.add_argument(
        "--n_workers",
        type=int,
        default=get_available_workers(),
        help="Number of parallel processes to use. Defaults to number of CPU cores.",
    )
    parser.add_argument(
        "--output", required=True, help="Output filename without extension"
    )
    parser.add_argument(
        "--format", choices=["csv", "parquet", "excel", "json"], default="csv", help="Output file format"
    )

    args = parser.parse_args()

    print(f"[Info] CLI Calendar generation started.")
    print(f"  Start: {args.start}")
    print(f"  End:   {args.end}")
    print(f"  Freq:  {args.freq}")
    print(f"  Regions: {args.regions}")
    print(f"  Column groups: {args.column_groups}")
    print(f"  Workers: {args.n_workers}")
    print(f"  Output: {args.output}.{args.format}")

    calendar_df = generate_calendar_table(
        start_datetime=args.start,
        end_datetime=args.end,
        freq=args.freq,
        regions=args.regions,
        column_groups=args.column_groups,
        n_workers=args.n_workers,
    )
    print(f"[Info] Saving calendar to disk...")
    save_calendar(calendar_df, filename=args.output, format=args.format)
    print(f"[Success] Calendar saved to {args.output}.{args.format}")


if __name__ == "__main__":
    main()
