# calendar_generator_cli.py

import pandas as pd
import pytz
import argparse
from tqdm import tqdm
import os


def generate_calendar_table(
    start_datetime, end_datetime, freq="min", chunk_size=500_000, regions=None
) -> pd.DataFrame:
    if regions is None:
        regions = ["UTC"]

    start_dt = pd.to_datetime(start_datetime)
    end_dt = pd.to_datetime(end_datetime)

    try:
        full_range = pd.date_range(start=start_dt, end=end_dt, freq=freq, tz="UTC")
    except ValueError as e:
        raise ValueError(f"Invalid frequency '{freq}': {e}")

    if len(full_range) > 10_000_000:
        print(
            f"⚠️ Warning: Generating {len(full_range):,} rows. Consider using a coarser frequency or a smaller date range."
        )

    chunks = []

    for i in tqdm(
        range(0, len(full_range), chunk_size), desc="Generating calendar", unit="chunk"
    ):
        chunk = full_range[i : i + chunk_size]
        df = pd.DataFrame({"datetime_utc": chunk})
        df["date_utc"] = df["datetime_utc"].dt.date

        # Time components
        df["hour"] = df["datetime_utc"].dt.hour
        df["minute"] = df["datetime_utc"].dt.minute
        df["second"] = df["datetime_utc"].dt.second

        # Standard calendar attributes (UTC-based)
        df["year"] = df["datetime_utc"].dt.year
        df["month"] = df["datetime_utc"].dt.month
        df["quarter"] = df["datetime_utc"].dt.quarter
        df["month_name"] = df["datetime_utc"].dt.month_name()
        df["week_ISO"] = df["datetime_utc"].dt.isocalendar().week
        df["iso_weekday"] = df["datetime_utc"].dt.isocalendar().day
        df["Week_US"] = df["datetime_utc"].dt.strftime("%W").astype(int) + 1
        df["day_name"] = df["datetime_utc"].dt.day_name()
        df["day_of_week"] = df["datetime_utc"].dt.dayofweek
        df["day_of_year"] = df["datetime_utc"].dt.dayofyear
        df["is_weekend"] = df["day_of_week"] >= 5
        df["is_month_start"] = df["datetime_utc"].dt.is_month_start
        df["is_month_end"] = df["datetime_utc"].dt.is_month_end
        df["is_quarter_start"] = df["datetime_utc"].dt.is_quarter_start
        df["is_quarter_end"] = df["datetime_utc"].dt.is_quarter_end
        df["is_year_start"] = df["datetime_utc"].dt.is_year_start
        df["is_year_end"] = df["datetime_utc"].dt.is_year_end
        df["is_leap_year"] = df["datetime_utc"].dt.is_leap_year
        df["days_in_month"] = df["datetime_utc"].dt.days_in_month
        df["days_in_year"] = df["datetime_utc"].dt.is_leap_year.apply(
            lambda x: 366 if x else 365
        )
        df["week_of_month"] = (df["datetime_utc"].dt.day - 1) // 7 + 1

        # Regional timezones
        for region in regions:
            tz = pytz.timezone(region)
            region_col = region.replace("/", "_").replace("-", "_")
            dt_col = f"datetime_{region_col}"
            df[dt_col] = df["datetime_utc"].dt.tz_convert(tz)

            # Localized flags
            df[f"is_month_end_{region_col}"] = df[dt_col].dt.is_month_end
            df[f"is_business_day_{region_col}"] = df[dt_col].dt.dayofweek < 5
            df[f"date_{region_col}"] = df[dt_col].dt.date
            mask = df[f"is_business_day_{region_col}"]
            business_days = df[mask].copy()
            business_days["month"] = business_days[dt_col].dt.month
            business_days["year"] = business_days[dt_col].dt.year
            last_biz_idx = business_days.groupby(["year", "month"])[dt_col].idxmax()
            df[f"is_business_month_end_{region_col}"] = False
            df.loc[last_biz_idx, f"is_business_month_end_{region_col}"] = True
            df[f"is_dst_{region_col}"] = (
                df[dt_col].dt.dst().apply(lambda x: bool(x and x.total_seconds() != 0))
            )

        chunks.append(df)

    return pd.concat(chunks, ignore_index=True)


def save_calendar(df, filename, format="csv"):
    if format == "csv":
        df.to_csv(f"{filename}.csv", index=False)
    elif format == "parquet":
        df.to_parquet(f"{filename}.parquet", index=False)
    else:
        raise ValueError("Unsupported format. Use 'csv' or 'parquet'.")


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
        "--freq", default="min", help="Frequency (e.g., '5min', 'D', 'H')"
    )
    parser.add_argument(
        "--regions",
        nargs="*",
        default=["UTC"],
        help="List of timezones (e.g., 'US/Eastern Europe/Rome')",
    )
    parser.add_argument(
        "--output", required=True, help="Output filename without extension"
    )
    parser.add_argument(
        "--format", choices=["csv", "parquet"], default="csv", help="Output file format"
    )

    args = parser.parse_args()

    print(f"[Info] CLI Calendar generation started.")
    print(f"  Start: {args.start}")
    print(f"  End:   {args.end}")
    print(f"  Freq:  {args.freq}")
    print(f"  Regions: {args.regions}")
    print(f"  Output: {args.output}.{args.format}")

    calendar_df = generate_calendar_table(
        args.start, args.end, freq=args.freq, regions=args.regions
    )
    print(f"[Info] Saving calendar to disk...")
    save_calendar(calendar_df, filename=args.output, format=args.format)
    print(f"[Success] Calendar saved to {args.output}.{args.format}")


if __name__ == "__main__":
    main()
