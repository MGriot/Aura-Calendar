# calendar_utils.py
import numpy as np
import pandas as pd
from pandas import Timestamp, Timedelta
import holidays
import pytz
import os
import warnings
import multiprocessing
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

# Additional imports for multicultural support
from convertdate import hebrew, islamic, gregorian
from lunarcalendar import Converter, Solar
from dateutil import easter

# Suppress UserWarning for timezone drop in PeriodArray/Index conversion
# ... (existing warning filter)

class HolidayProvider:
    """Unified provider for National, Religious, and Cultural holidays."""

    @staticmethod
    def get_holidays(start_date: date, end_date: date, countries: List[str], enabled_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        holiday_map = {}
        years = list(range(start_date.year, end_date.year + 1))

        # 1. National Holidays (holidays package)
        # Map frontend granular IDs to country codes
        country_obj = {}
        country_map = {
            "holidays_it": "IT",
            "holidays_us": "US",
            "holidays_mx": "MX",
            "holidays_cz": "CZ"
        }
        for hid, code in country_map.items():
            if hid in enabled_types:
                try:
                    country_obj[code] = holidays.CountryHoliday(code, years=years)
                except:
                    continue

        # 2. Chinese Lunar Festivals

        # Spring Festival (L:1/1), Lantern (L:1/15), Qingming (Solar Approx), Dragon Boat (L:5/5), Mid-Autumn (L:8/15)
        chinese_festivals = {
            (1, 1): "Spring Festival (Chinese New Year)",
            (1, 15): "Lantern Festival",
            (5, 5): "Dragon Boat Festival",
            (8, 15): "Mid-Autumn Festival"
        }

        # 3. Catholic Floating Holidays (relative to Easter)
        # Ash Wednesday (-46), Palm Sunday (-7), Good Friday (-2), Easter (0), Easter Monday (+1), Pentecost (+50)
        # Fixed: Epiphany (Jan 6), Assumption (Aug 15), All Saints (Nov 1), Immaculate (Dec 8), Christmas (Dec 25)
        catholic_offsets = {
            -46: "Ash Wednesday",
            -7: "Palm Sunday",
            -2: "Good Friday",
            0: "Easter Sunday",
            1: "Easter Monday",
            50: "Pentecost"
        }
        catholic_fixed = {
            (1, 6): "Epiphany",
            (8, 15): "Assumption of Mary",
            (11, 1): "All Saints' Day",
            (12, 8): "Immaculate Conception",
            (12, 25): "Christmas Day"
        }

        cur = start_date
        while cur <= end_date:
            d_str = cur.isoformat()
            items = []
            
            # National
            for c, h in country_obj.items():
                name = h.get(cur)
                if name:
                    # Explicitly show which nation has it as requested
                    items.append({
                        "type": "holiday", 
                        "name": f"{name} ({c})", 
                        "country": c, 
                        "category": "national",
                        "color": "#ef4444" # Red for national
                    })
            
            # Chinese (Lunar)
            if "chinese" in enabled_types: # Matching the setting id used in frontend
                try:
                    solar = Solar(cur.year, cur.month, cur.day)
                    lunar = Converter.Solar2Lunar(solar)
                    lunar_key = (lunar.month, lunar.day)
                    if lunar_key in chinese_festivals:
                        items.append({
                            "type": "cultural", 
                            "name": f"{chinese_festivals[lunar_key]} (CN)", 
                            "category": "chinese",
                            "color": "#f59e0b" # Orange/Gold for Chinese
                        })
                except:
                    pass

            # Catholic
            if "catholic" in enabled_types:
                # Fixed
                fixed_key = (cur.month, cur.day)
                if fixed_key in catholic_fixed:
                    items.append({
                        "type": "religious", 
                        "name": catholic_fixed[fixed_key], 
                        "category": "catholic",
                        "color": "#8b5cf6" # Purple for Catholic
                    })
                
                # Floating
                easter_date = easter.easter(cur.year)
                delta = (cur - easter_date).days
                if delta in catholic_offsets:
                    items.append({
                        "type": "religious", 
                        "name": catholic_offsets[delta], 
                        "category": "catholic",
                        "color": "#8b5cf6"
                    })

            # Hebrew
            if "hebrew" in enabled_types:
                try:
                    _, h_month, h_day = hebrew.from_gregorian(cur.year, cur.month, cur.day)
                    # You could add specific Hebrew holidays here too
                    items.append({"type": "cultural", "name": f"Hebrew: {h_month}/{h_day}", "category": "hebrew"})
                except:
                    pass

            # Islamic
            if "islamic" in enabled_types:
                try:
                    _, i_month, i_day = islamic.from_gregorian(cur.year, cur.month, cur.day)
                    items.append({"type": "cultural", "name": f"Islamic: {i_month}/{i_day}", "category": "islamic"})
                except:
                    pass

            if items:
                holiday_map[d_str] = items
            
            cur += timedelta(days=1)
            
        return holiday_map
warnings.filterwarnings(
    "ignore",
    message="Converting to PeriodArray/Index representation will drop timezone information.",
    category=UserWarning,
    module=".*",
)


def generate_boundaries_with_alignment(year: int, pattern: list) -> list:
    """
    Generate fiscal period boundaries for a given year based on a repeating week pattern.

    Parameters
    ----------
    year : int
        The calendar year for which to generate fiscal boundaries.
    pattern : list
        A list of integers representing the number of weeks in each fiscal month (e.g., [4, 4, 5]).

    Returns
    -------
    list of tuple
        A list of (start_date, end_date) tuples for each fiscal period in the year.
    """
    boundaries = []
    start = Timestamp(year, 1, 1)
    # Month 1: from Jan 1 to the fourth Saturday
    days_until_sat = (5 - start.weekday()) % 7
    length_days = days_until_sat + (pattern[0] - 1) * 7
    end = start + Timedelta(days=length_days)
    dec31 = Timestamp(year, 12, 31)
    if end > dec31:
        end = dec31
    boundaries.append((start, end))

    # For subsequent months
    for weeks in pattern[1:]:
        if boundaries[-1][1] >= dec31:
            break
        start = boundaries[-1][1] + Timedelta(days=1)
        length_days = weeks * 7 - 1
        end = start + Timedelta(days=length_days)
        if end > dec31:
            end = dec31
        boundaries.append((start, end))
    return boundaries


def assign_fiscal_periods_strict(
    df: pd.DataFrame, date_col: str, boundaries_by_year: dict
) -> pd.DataFrame:
    """
    Assign ITT fiscal months to each row in the DataFrame based on precomputed boundaries.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing a datetime column.
    date_col : str
        Name of the datetime column.
    boundaries_by_year : dict
        Dictionary mapping years to lists of (start, end) tuples for fiscal periods.

    Returns
    -------
    pd.DataFrame
        DataFrame with an added 'ITTFiscalMonth' column.
    """
    fiscal_months = []
    fiscal_years = []

    utc = pytz.UTC

    for dt in df[date_col]:
        # Ensure dt is timezone-aware
        if dt.tzinfo is None:
            dt = utc.localize(dt)

        year = dt.year
        if year not in boundaries_by_year:
            fiscal_months.append(None)
            fiscal_years.append(None)
            continue

        for i, (start, end) in enumerate(boundaries_by_year[year]):
            # Ensure start and end are timezone-aware
            if start.tzinfo is None:
                start = utc.localize(start)
            if end.tzinfo is None:
                end = utc.localize(end)

            if start <= dt <= end:
                fiscal_months.append(i + 1)
                fiscal_years.append(year)
                break
        else:
            fiscal_months.append(12)
            fiscal_years.append(year)

    df["ITTFiscalMonth"] = fiscal_months
    # df['ITTFiscalYear'] = fiscal_years
    return df


def assign_itt_fiscal_weeks(
    df: pd.DataFrame, date_col: str, boundaries_by_year: dict
) -> pd.DataFrame:
    """
    Assign ITT fiscal week numbers to each row in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing a datetime column.
    date_col : str
        Name of the datetime column.
    boundaries_by_year : dict
        Dictionary mapping years to lists of (start, end) tuples for fiscal periods.

    Returns
    -------
    pd.DataFrame
        DataFrame with an added 'ITTFiscalWeek' column.
    """
    itt_weeks = []

    for dt in df[date_col]:
        year = dt.year
        if year not in boundaries_by_year:
            itt_weeks.append(None)
            continue

        fiscal_start = boundaries_by_year[year][0][0]
        if dt < fiscal_start:
            itt_weeks.append(None)
            continue

        week_number = ((dt - fiscal_start).days // 7) + 1
        itt_weeks.append(week_number)

    df["ITTFiscalWeek"] = itt_weeks
    return df


def calculate_itt_fiscal_columns(
    df: pd.DataFrame, date_col: str = "datetime_utc"
) -> pd.DataFrame:
    """
    ITT fiscal calendar logic commented out as requested.
    """
    df["ITTFiscalMonth"] = None
    df["ITTFiscalWeek"] = None
    df["is_first_day_of_fiscal_period"] = False
    df["is_last_day_of_fiscal_period"] = False
    return df


def additional_calendar_columns(
    df: pd.DataFrame, date_col: str = "datetime_utc"
) -> pd.DataFrame:
    """
    Add extended calendar attributes to a DataFrame, including both standard ISO week logic
    and a year-bounded week logic that prevents weeks from crossing calendar year boundaries.
    """
    dt = df[date_col]

    # Ensure all datetime values are timezone-aware (UTC)
    if dt.dt.tz is None:
        dt = dt.dt.tz_localize("UTC")
    else:
        dt = dt.dt.tz_convert("UTC")

    df[date_col] = dt

    # Standard ISO week logic
    df["WeekStart_ISO"] = dt - pd.to_timedelta(dt.dt.dayofweek, unit="D")
    df["WeekEnd_ISO"] = df["WeekStart_ISO"] + pd.Timedelta(days=6)

    # Year-bounded week logic
    df["WeekStart_YearBounded"] = df.apply(
        lambda row: max(
            row["WeekStart_ISO"], pd.Timestamp(row[date_col].year, 1, 1, tz="UTC")
        ),
        axis=1,
    )
    df["WeekEnd_YearBounded"] = df.apply(
        lambda row: min(
            row["WeekEnd_ISO"],
            pd.Timestamp(row[date_col].year, 12, 31, 23, 59, 59, tz="UTC"),
        ),
        axis=1,
    )

    # Week of month and last week of month
    first_day = dt.dt.to_period("M").dt.start_time.dt.tz_localize("UTC")
    df["WeekOfMonth"] = np.ceil((dt.dt.day + first_day.dt.weekday) / 7).astype(int)
    df["IsLastWeekOfMonth"] = (dt + pd.Timedelta(days=7)).dt.month != dt.dt.month

    # Month and quarter boundaries
    df["MonthStart"] = dt.dt.to_period("M").dt.start_time.dt.tz_localize("UTC")
    df["MonthEnd"] = dt.dt.to_period("M").dt.end_time.dt.tz_localize("UTC")
    df["DaysInMonth"] = df["MonthEnd"].dt.day

    df["QuarterStart"] = dt.dt.to_period("Q").dt.start_time.dt.tz_localize("UTC")
    df["QuarterEnd"] = dt.dt.to_period("Q").dt.end_time.dt.tz_localize("UTC")
    df["DaysInQuarter"] = (df["QuarterEnd"] - df["QuarterStart"]).dt.days + 1

    # Business day and formatting
    df["YearMonth"] = dt.dt.strftime("%Y-%m")
    df["YearWeek"] = dt.dt.strftime("%Y-W%U")
    df["ISOWeekYear"] = dt.dt.isocalendar().year

    return df


def add_country_business_day_flags(
    df, date_col="datetime_utc", countries=["IT", "CZ", "CN", "MX"]
):
    """
    Add business day flags for specified countries to a DataFrame based on weekends and national holidays.
    Also adds holiday name.

    This function adds two columns per country:
    - 'IsHolidayDay_<country>': True if the date is a public holiday in the specified country.
    - 'IsBusinessDay_<country>': True if the date is a business day (i.e., not a weekend and not a holiday).
    - 'HolidayName_<country>': Name of the holiday if it's a holiday, otherwise None.
    - 'HolidayName_<country>': Name of the holiday if it's a holiday, otherwise None.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing a datetime column.
    date_col : str, default='datetime'
        Name of the column in `df` containing datetime values. This column must be of datetime type.
    countries : list of str, default=['IT', 'CZ', 'CN', 'MX']
        List of ISO 3166-1 alpha-2 country codes for which to compute business day flags.
        Holidays are determined using the `holidays` Python package.

    Returns
    -------
    pd.DataFrame
        The original DataFrame with additional columns for each country:
        - 'IsHolidayDay_<country>'
        - 'IsBusinessDay_<country>'
        - 'HolidayName_<country>'

    Notes
    -----
    - If holiday data is not available for a given country, a warning is printed and the corresponding
      'IsBusinessDay_<country>' column will contain None.
    - The function assumes that weekends are Saturday and Sunday.
    """
    years = df[date_col].dt.year.unique().tolist()
    all_dates = df[date_col].dt.date.unique()

    for country in countries:
        df[f"HolidayName_{country}"] = None # Initialize with None
        try:
            holiday_calendar = holidays.CountryHoliday(country, years=years)
            # Create a Series mapping dates to holiday names
            holiday_names_map = {date: name for date, name in holiday_calendar.items()}

            df[f"IsHolidayDay_{country}"] = df[date_col].dt.date.isin(holiday_calendar)
            df.loc[df[f"IsHolidayDay_{country}"], f"HolidayName_{country}"] = \
                df.loc[df[f"IsHolidayDay_{country}"], date_col].dt.date.map(holiday_names_map)

            df[f"IsBusinessDay_{country}"] = (~df["is_weekend"]) & (
                ~df[f"IsHolidayDay_{country}"]
            )
        except Exception as e:
            print(f"[Warning] Could not generate holidays for {country}: {e}")
            df[f"IsHolidayDay_{country}"] = False  # Default to False on error
            df[f"IsBusinessDay_{country}"] = False  # Default to False on error
            df[f"HolidayName_{country}"] = None # Ensure it's None on error
    return df


def save_calendar(df, filename, format="csv"):
    """
    Save the calendar DataFrame to a file in the specified format and display summary statistics.

    Parameters
    ----------
    df : pd.DataFrame
        The calendar DataFrame to save.
    filename : str
        The name of the output file (without extension).
    format : str, default='csv'
        The format to save the file in. Options:
        - 'csv'   : Comma-separated values
        - 'excel' : Excel spreadsheet (.xlsx)
        - 'json'  : JSON format

    Returns
    -------
    None
        Saves the file and prints a summary message.
    """
    # Ensure the directory exists before saving
    if not filename or not isinstance(filename, str) or filename.strip() == "":
        raise ValueError("Filename must be a non-empty string.")
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    format = format.lower()
    if format == "csv":
        full_path = f"{filename}.csv"
    elif format == "excel":
        full_path = f"{filename}.xlsx"
    elif format == "json":
        full_path = f"{filename}.json"
    else:
        raise ValueError("Unsupported format. Choose from 'csv', 'excel', or 'json'.")

    print(f"[Info] Saving to {full_path} ...")
    try:
        if format == "csv":
            df.to_csv(full_path, index=False)
        elif format == "excel":
            df.to_excel(full_path, index=False)
        elif format == "json":
            df.to_json(full_path, orient="records", date_format="iso")
    except Exception as e:
        raise IOError(f"Error saving calendar to {full_path}: {e}")

    # Define the date column explicitly
    date_col = "date_utc"  # or set to the correct column name if different
    start_date = df[date_col].min()
    end_date = df[date_col].max()
    total_rows = len(df)
    print(f"[Success] File saved: {full_path}")
    print(f"[Info] Date range: {start_date} to {end_date} - {total_rows:,} rows\n")


def add_time_components(df, datetime_col="datetime_utc"):
    """Add hour, minute, second columns."""
    df["hour"] = df[datetime_col].dt.hour
    df["minute"] = df[datetime_col].dt.minute
    df["second"] = df[datetime_col].dt.second
    return df


def add_standard_calendar_columns(df, datetime_col="datetime_utc"):
    """Add standard calendar columns (month, week, day, etc.)."""
    dt = df[datetime_col]
    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["quarter"] = dt.dt.quarter
    df["month_name"] = dt.dt.month_name()
    df["week_ISO"] = dt.dt.isocalendar().week
    df["iso_weekday"] = dt.dt.isocalendar().day
    df["Week_US"] = dt.dt.strftime("%W").astype(int) + 1
    df["day_name"] = dt.dt.day_name()
    df["day_of_week"] = dt.dt.dayofweek
    df["day_of_year"] = dt.dt.dayofyear
    df["is_weekend"] = df["day_of_week"] >= 5
    df["is_month_start"] = dt.dt.is_month_start
    df["is_month_end"] = dt.dt.is_month_end
    df["is_quarter_start"] = dt.dt.is_quarter_start
    df["is_quarter_end"] = dt.dt.is_quarter_end
    df["is_year_start"] = dt.dt.is_year_start
    df["is_year_end"] = dt.dt.is_year_end
    df["is_leap_year"] = dt.dt.is_leap_year
    df["days_in_month"] = dt.dt.days_in_month
    df["days_in_year"] = dt.dt.is_leap_year.apply(lambda x: 366 if x else 365)
    df["week_of_month"] = (dt.dt.day - 1) // 7 + 1
    return df


def add_regional_columns(df, regions, datetime_col="datetime_utc"):
    """Add timezone-localized columns and business day flags for each region."""
    for region in regions:
        tz = pytz.timezone(region)
        region_col = region.replace("/", "_").replace("-", "_")
        dt_col = f"datetime_{region_col}"
        df[dt_col] = df[datetime_col].dt.tz_convert(tz)
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
        # Fix DST flag calculation
        df[f"is_dst_{region_col}"] = df[dt_col].apply(
            lambda x: bool(x.dst() and x.dst().total_seconds() != 0)
        )
        # Add UTC offset in minutes
        df[f"utc_offset_minutes_{region_col}"] = df[dt_col].apply(
            lambda x: int(x.utcoffset().total_seconds() / 60)
            if x.utcoffset() is not None else 0
        )
        # Identify ambiguous and imaginary times for DST transitions
        # Need to re-localize to handle ambiguous/imaginary times, passing 'ambiguous' and 'nonexistent'
        # First, remove timezone to re-localize
        localized_dt_naive = df[datetime_col].dt.tz_localize(None) # Ensure naive for pytz.localize

        def check_ambiguous(naive_dt, timezone):
            try:
                timezone.localize(naive_dt, is_dst=None)
                return False
            except pytz.exceptions.AmbiguousTimeError:
                return True
            except pytz.exceptions.NonExistentTimeError:
                return False # Not ambiguous, but non-existent

        def check_imaginary(naive_dt, timezone):
            try:
                timezone.localize(naive_dt, is_dst=None)
                return False
            except pytz.exceptions.NonExistentTimeError:
                return True
            except pytz.exceptions.AmbiguousTimeError:
                return False # Not non-existent, but ambiguous

        df[f"is_ambiguous_time_{region_col}"] = localized_dt_naive.apply(lambda x: check_ambiguous(x, tz))
        df[f"is_imaginary_time_{region_col}"] = localized_dt_naive.apply(lambda x: check_imaginary(x, tz))
    return df


def add_extra_calendar_columns(df, datetime_col="datetime_utc"):
    """
    Add extra calendar columns that may be useful for analytics or reporting.
    """
    dt = df[datetime_col]
    # Semester (1 or 2)
    df["semester"] = dt.dt.month.apply(lambda m: 1 if m <= 6 else 2)
    # Half of quarter (1 or 2)
    df["half_of_quarter"] = dt.dt.month.apply(lambda m: 1 if (m - 1) % 3 < 1.5 else 2)
    # Day of quarter
    df["day_of_quarter"] = (dt - dt.dt.to_period("Q").dt.start_time.dt.tz_localize(dt.dt.tz)).dt.days + 1
    # Fiscal year (if different from calendar year, e.g., starts in July)
    df["fiscal_year_jul"] = dt.apply(lambda x: x.year if x.month >= 7 else x.year - 1)
    # Week of quarter
    df["week_of_quarter"] = (
        dt.dt.dayofyear - dt.dt.to_period("Q").dt.start_time.dt.dayofyear
    ) // 7 + 1
    # Is last day of week (Sunday)
    df["is_week_end"] = dt.dt.weekday == 6
    # Is penultimate day of month
    df["is_penultimate_day_of_month"] = dt.dt.day == (dt.dt.days_in_month - 1)
    # Is first business day of month (UTC)
    df["is_first_business_day_month"] = (dt.dt.is_month_start) & (dt.dt.dayofweek < 5)
    # Is last business day of year (UTC)
    df["is_last_business_day_year"] = False
    last_biz_idx = df[df["day_of_week"] < 5].groupby("year")["datetime_utc"].idxmax()
    df.loc[last_biz_idx, "is_last_business_day_year"] = True
    # Biweekly period number (1-26 per year)
    df["biweekly_period_number"] = (dt.dt.dayofyear - 1) // 14 + 1
    return df


def add_seasonality_columns(df: pd.DataFrame, datetime_col: str = "datetime_utc") -> pd.DataFrame:
    """
    Add seasonality columns to the DataFrame (Northern Hemisphere based).
    """
    dt = df[datetime_col]
    month = dt.dt.month
    day = dt.dt.day

    # Astronomical Season (Northern Hemisphere) - Simplified
    # Spring: March (20-31), April, May, June (1-20)
    # Summer: June (21-30), July, August, September (1-22)
    # Autumn: September (23-30), October, November, December (1-21)
    # Winter: December (22-31), January, February, March (1-19)
    conditions_astronomical = [
        ((month == 3) & (day >= 20)) | (month.isin([4, 5])) | ((month == 6) & (day < 21)), # Spring
        ((month == 6) & (day >= 21)) | (month.isin([7, 8])) | ((month == 9) & (day < 23)), # Summer
        ((month == 9) & (day >= 23)) | (month.isin([10, 11])) | ((month == 12) & (day < 22)), # Autumn
        ((month == 12) & (day >= 22)) | (month.isin([1, 2])) | ((month == 3) & (day < 20)), # Winter
    ]
    choices_astronomical = ["Spring", "Summer", "Autumn", "Winter"]
    df["season_astronomical"] = np.select(conditions_astronomical, choices_astronomical, default=None)

    # Meteorological Season (Northern Hemisphere)
    # Spring: March, April, May
    # Summer: June, July, August
    # Autumn: September, October, November
    # Winter: December, January, February
    conditions_meteorological = [
        (month.isin([3, 4, 5])),
        (month.isin([6, 7, 8])),
        (month.isin([9, 10, 11])),
        (month.isin([12, 1, 2]))
    ]
    choices_meteorological = ["Spring", "Summer", "Autumn", "Winter"]
    df["season_meteorological"] = np.select(conditions_meteorological, choices_meteorological, default=None)

    return df


def add_key_columns(df: pd.DataFrame, datetime_col: str = "datetime_utc") -> pd.DataFrame:
    """
    Add interoperability and master key columns to the DataFrame.
    """
    dt = df[datetime_col]
    df["date_key"] = dt.dt.strftime("%Y%m%d").astype(int)
    df["datetime_key"] = dt.dt.strftime("%Y%m%d%H%M%S").astype(np.int64)
    return df


def get_column_group_functions():
    """
    Returns a mapping of group names to their corresponding functions.
    """
    return {
        "time": add_time_components,
        "standard": add_standard_calendar_columns,
        "fiscal": calculate_itt_fiscal_columns,
        "additional": additional_calendar_columns,
        "country_business": add_country_business_day_flags,
        "regional": add_regional_columns,
        "extra": add_extra_calendar_columns,
        "keys": add_key_columns,
        "seasonality": add_seasonality_columns,
    }


def apply_column_groups(df, column_groups, datetime_col="datetime_utc"):
    """
    Apply a series of column addition functions to a DataFrame based on specified groups.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to which columns will be added.
    column_groups : list of str
        A list of group names indicating which column addition functions to apply.
    datetime_col : str, default='datetime'
        The name of the datetime column in `df`.

    Returns
    -------
    pd.DataFrame
        The DataFrame with the new columns added.

    Notes
    -----
    - The order of operations is determined by the order of groups in the `column_groups` list.
    - Not all functions need to be applied every time; use `column_groups` to specify desired groups.
    """
    all_functions = get_column_group_functions()

    for group in column_groups:
        if group in all_functions:
            func = all_functions[group]
            df = func(df, datetime_col=datetime_col)

    return df


def get_available_workers():
    """
    Returns the number of available CPU workers (logical cores) on this machine.
    """
    return multiprocessing.cpu_count()


# All functions are already compartmentalized and efficient.
# If you want to add more utility columns, do so in calendar_generator.py for clarity.
# - assign_fiscal_periods_strict
# - assign_itt_fiscal_weeks
# - calculate_itt_fiscal_columns
# - additional_calendar_columns
# - add_country_business_day_flags
# - save_calendar
# - save_calendar
# - save_calendar
