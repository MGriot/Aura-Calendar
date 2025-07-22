# Modules and API Reference

This document provides a detailed reference for the functions and modules within the Calendar Table Generator project.

## `src/calendar_generator.py`

This module contains the core logic for generating the calendar table, including parallel processing capabilities.

### `generate_calendar_table`

```python
def generate_calendar_table(
    start_datetime,
    end_datetime,
    freq="min",
    date_format=None,
    chunk_size=500_000,
    regions=None,
    column_groups=None,
    n_workers=None,
) -> pd.DataFrame:
```

Generate a comprehensive calendar table with user-selectable column groups, using parallel processing.

**Parameters:**

-   `start_datetime` : `str | datetime.date | datetime.datetime`
    The start of the calendar range.
-   `end_datetime` : `str | datetime.date | datetime.datetime`
    The end of the calendar range.
-   `freq` : `str`, default='min'
    Frequency string for the datetime range. See pandas offset aliases.
-   `date_format` : `str`, optional
    Optional format string to parse the input dates.
-   `chunk_size` : `int`, default=500_000
    Number of rows to process per chunk for memory efficiency.
-   `regions` : `list of str`, optional
    List of timezone region names for regional columns.
-   `column_groups` : `list of str`, optional
    List of column group names to include. Defaults to all.
-   `n_workers` : `int`, optional
    Number of parallel processes to use. Defaults to number of CPU cores.

**Returns:**

-   `pd.DataFrame`
    A DataFrame with the selected calendar columns.

### `process_chunk`

```python
def process_chunk(args):
```

Helper function to process a chunk of datetime data and add specified column groups. This function is designed for internal use with `ProcessPoolExecutor`.

## `src/calendar_utils.py`

This module contains various utility functions for generating specific calendar columns, handling fiscal periods, and saving data.

### `generate_boundaries_with_alignment`

```python
def generate_boundaries_with_alignment(year: int, pattern: list) -> list:
```

Generate fiscal period boundaries for a given year based on a repeating week pattern.

**Parameters:**

-   `year` : `int`
    The calendar year for which to generate fiscal boundaries.
-   `pattern` : `list`
    A list of integers representing the number of weeks in each fiscal month (e.g., `[4, 4, 5]`).

**Returns:**

-   `list of tuple`
    A list of `(start_date, end_date)` tuples for each fiscal period in the year.

### `assign_fiscal_periods_strict`

```python
def assign_fiscal_periods_strict(
    df: pd.DataFrame, date_col: str, boundaries_by_year: dict
) -> pd.DataFrame:
```

Assign ITT fiscal months to each row in the DataFrame based on precomputed boundaries.

**Parameters:**

-   `df` : `pd.DataFrame`
    DataFrame containing a datetime column.
-   `date_col` : `str`
    Name of the datetime column.
-   `boundaries_by_year` : `dict`
    Dictionary mapping years to lists of `(start, end)` tuples for fiscal periods.

**Returns:**

-   `pd.DataFrame`
    DataFrame with an added 'ITTFiscalMonth' column.

### `assign_itt_fiscal_weeks`

```python
def assign_itt_fiscal_weeks(
    df: pd.DataFrame, date_col: str, boundaries_by_year: dict
) -> pd.DataFrame:
```

Assign ITT fiscal week numbers to each row in the DataFrame.

**Parameters:**

-   `df` : `pd.DataFrame`
    DataFrame containing a datetime column.
-   `date_col` : `str`
    Name of the datetime column.
-   `boundaries_by_year` : `dict`
    Dictionary mapping years to lists of `(start, end)` tuples for fiscal periods.

**Returns:**

-   `pd.DataFrame`
    DataFrame with an added 'ITTFiscalWeek' column.

### `calculate_itt_fiscal_columns`

```python
def calculate_itt_fiscal_columns(
    df: pd.DataFrame, date_col: str = "datetime_utc"
) -> pd.DataFrame:
```

Add ITT fiscal calendar columns to the DataFrame using a 4-4-5 pattern.

**Parameters:**

-   `df` : `pd.DataFrame`
    DataFrame with a datetime column.
-   `date_col` : `str`, default='datetime'
    Name of the datetime column.

**Returns:**

-   `pd.DataFrame`
    DataFrame with added 'ITTFiscalMonth' column.

### `additional_calendar_columns`

```python
def additional_calendar_columns(
    df: pd.DataFrame, date_col: str = "datetime_utc"
) -> pd.DataFrame:
```

Add extended calendar attributes to a DataFrame, including both standard ISO week logic and a year-bounded week logic that prevents weeks from crossing calendar year boundaries.

### `add_country_business_day_flags`

```python
def add_country_business_day_flags(
    df, date_col="datetime_utc", countries=["IT", "CZ", "CN", "MX"]
):
```

Add business day flags for specified countries to a DataFrame based on weekends and national holidays.

This function adds two columns per country:
-   `'IsHolidayDay_<country>'`: True if the date is a public holiday in the specified country.
-   `'IsBusinessDay_<country>'`: True if the date is a business day (i.e., not a weekend and not a holiday).

**Parameters:**

-   `df` : `pd.DataFrame`
    DataFrame containing a datetime column.
-   `date_col` : `str`, default='datetime'
    Name of the column in `df` containing datetime values. This column must be of datetime type.
-   `countries` : `list of str`, default=`['IT', 'CZ', 'CN', 'MX']`
    List of ISO 3166-1 alpha-2 country codes for which to compute business day flags.
    Holidays are determined using the `holidays` Python package.

**Returns:**

-   `pd.DataFrame`
    The original DataFrame with additional columns for each country:
    -   `'IsHolidayDay_<country>'`
    -   `'IsBusinessDay_<country>'`

**Notes:**

-   If holiday data is not available for a given country, a warning is printed and the corresponding
    `'IsBusinessDay_<country>'` column will contain None.
-   The function assumes that weekends are Saturday and Sunday.

### `save_calendar`

```python
def save_calendar(df, filename, format="csv"):
```

Save the calendar DataFrame to a file in the specified format and display summary statistics.

**Parameters:**

-   `df` : `pd.DataFrame`
    The calendar DataFrame to save.
-   `filename` : `str`
    The name of the output file (without extension).
-   `format` : `str`, default='csv'
    The format to save the file in. Options:
    -   `'csv'`   : Comma-separated values
    -   `'excel'` : Excel spreadsheet (.xlsx)
    -   `'json'`  : JSON format

**Returns:**

-   `None`
    Saves the file and prints a summary message.

### `add_time_components`

```python
def add_time_components(df, datetime_col="datetime_utc"):
```

Add hour, minute, second columns.

### `add_standard_calendar_columns`

```python
def add_standard_calendar_columns(df, datetime_col="datetime_utc"):
```

Add standard calendar columns (month, week, day, etc.).

### `add_regional_columns`

```python
def add_regional_columns(df, regions, datetime_col="datetime_utc"):
```

Add timezone-localized columns and business day flags for each region.

### `add_extra_calendar_columns`

```python
def add_extra_calendar_columns(df, datetime_col="datetime_utc"):
```

Add extra calendar columns that may be useful for analytics or reporting.

### `get_column_group_functions`

```python
def get_column_group_functions():
```

Returns a mapping of group names to their corresponding functions.

### `apply_column_groups`

```python
def apply_column_groups(df, column_groups, datetime_col="datetime_utc"):
```

Apply a series of column addition functions to a DataFrame based on specified groups.

**Parameters:**

-   `df` : `pd.DataFrame`
    The DataFrame to which columns will be added.
-   `column_groups` : `list of str`
    A list of group names indicating which column addition functions to apply.
-   `datetime_col` : `str`, default='datetime'
    The name of the datetime column in `df`.

**Returns:**

-   `pd.DataFrame`
    The DataFrame with the new columns added.

**Notes:**

-   The order of operations is determined by the order of groups in the `column_groups` list.
-   Not all functions need to be applied every time; use `column_groups` to specify desired groups.

### `get_available_workers`

```python
def get_available_workers():
```

Returns the number of available CPU workers (logical cores) on this machine.

## `src/visualize_business_eom.py`

This module provides functionality to visualize business end-of-month (EOM) days from a generated calendar table.

### `load_calendar_data`

```python
def load_calendar_data(file_path):
```

Load calendar data from CSV.

### `extract_business_eom_flags`

```python
def extract_business_eom_flags(df):
```

Identify columns that represent business end-of-month flags.

### `plot_business_eom_heatmap`

```python
def plot_business_eom_heatmap(
    df, region_flag_col, date_col="datetime_utc", save_path=None
):
```

Plot and optionally save a heatmap of business EOM days.
