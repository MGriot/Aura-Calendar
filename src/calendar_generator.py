# calendar_generator.py
import os
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from calendar_utils import (
    get_column_group_functions,
    save_calendar,
)


def process_chunk(args):
    chunk, regions, column_groups, countries_for_holidays = args
    df = pd.DataFrame({"datetime_utc": chunk})
    df["date_utc"] = df["datetime_utc"].dt.date
    group_funcs = get_column_group_functions()
    for group in column_groups:
        func = group_funcs[group]
        if group == "regional":
            df = func(df, regions)
        elif group == "country_business":
            df = func(df, countries=countries_for_holidays)
        else:
            df = func(df)
    return df


def generate_calendar_table(
    start_datetime,
    end_datetime,
    freq="min",
    date_format=None,
    chunk_size=500_000,
    regions=None,
    column_groups=None,
    n_workers=None,
    countries=None, # Added
) -> pd.DataFrame:
    """
    Generate a comprehensive calendar table with user-selectable column groups, using parallel processing.

    Parameters
    ----------
    start_datetime : str | datetime.date | datetime.datetime
        The start of the calendar range.
    end_datetime : str | datetime.date | datetime.datetime
        The end of the calendar range.
    freq : str, default='min'
        Frequency string for the datetime range. See pandas offset aliases.
    date_format : str, optional
        Optional format string to parse the input dates.
    chunk_size : int, default=500_000
        Number of rows to process per chunk for memory efficiency.
    regions : list of str, optional
        List of timezone region names for regional columns.
    column_groups : list of str, optional
        List of column group names to include. Defaults to all.
    n_workers : int, optional
        Number of parallel processes to use. Defaults to number of CPU cores.
    countries : list of str, optional
        List of ISO 3166-1 alpha-2 country codes for which to compute business day flags.

    Returns
    -------
    pd.DataFrame
        A DataFrame with the selected calendar columns.
    """

    if regions is None:
        regions = ["US/Eastern", "Europe/Rome", "Asia/Tokyo"]
    if countries is None: # Added
        countries = ["IT", "CZ", "CN", "MX"] # Added default countries for holidays

    if column_groups is None:
        column_groups = [
            "time",
            "standard",
            "fiscal",
            "additional",
            "country_business",
            "regional",
            "extra",
            "keys",
            "seasonality",
        ]

    try:
        start_dt = (
            pd.to_datetime(start_datetime, format=date_format)
            if date_format
            else pd.to_datetime(start_datetime)
        )
        end_dt = (
            pd.to_datetime(end_datetime, format=date_format)
            if date_format
            else pd.to_datetime(end_datetime)
        )
    except ValueError as e:
        raise ValueError(f"Invalid date format or value for start/end datetime: {e}")

    try:
        full_range = pd.date_range(start=start_dt, end=end_dt, freq=freq, tz="UTC")
    except ValueError as e:
        raise ValueError(f"Invalid frequency '{freq}': {e}")

    if len(full_range) > 10_000_000:
        print(
            f"⚠️ Warning: Generating {len(full_range):,} rows. Consider using a coarser frequency or a smaller date range."
        )

    total_workers = n_workers if n_workers else os.cpu_count()
    print(f"[Info] Calendar generation started.")
    print(f"  Start: {start_datetime}")
    print(f"  End:   {end_datetime}")
    print(f"  Freq:  {freq}")
    print(f"  Regions: {regions}")
    print(f"  Column groups: {column_groups}")
    print(f"  Chunk size: {chunk_size}")
    print(
        f"  Workers: {n_workers if n_workers else 'auto'} (Total available: {os.cpu_count()})"
    )
    print(f"  Total periods: {len(full_range):,}")

    chunk_args = []
    for i in range(0, len(full_range), chunk_size):
        chunk = full_range[i : i + chunk_size]
        chunk_args.append((chunk, regions, column_groups, countries)) # Added countries

    results = []
    try:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            for idx, df in enumerate(
                tqdm(
                    executor.map(process_chunk, chunk_args),
                    total=len(chunk_args),
                    desc="Generating calendar",
                    unit="chunk",
                )
            ):
                print(f"[Chunk {idx+1}/{len(chunk_args)}] Processed {len(df):,} rows.")
                results.append(df)
    except Exception as e:
        raise RuntimeError(f"Error during parallel processing: {e}")

    final_df = pd.concat(results, ignore_index=True)
    print(f"[Info] Calendar generation completed. Total rows: {len(final_df):,}")
    return final_df


if __name__ == "__main__":
    start = "2025-01-01"
    end = "2035-12-31"
    freq = "D"
    regions = ["Europe/Rome", "Europe/Prague", "Asia/Shanghai", "America/Mexico_City"]
    countries = ["US", "IT"] # Example countries for main execution

    calendar_df = generate_calendar_table(
        start, end, freq=freq, regions=regions, countries=countries, n_workers=8
    )
    print("[Info] Saving calendar to disk...")
    save_calendar(
        calendar_df,
        filename=rf"C:\Users\Admin\Documents\Coding\Calendar\calendar_table_{start}-{end}_freq_{freq}",
        format="csv",
    )
    print("[Info] Calendar saved.")
    print(calendar_df.head(10))