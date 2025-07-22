# Customization

The Calendar Table Generator is designed to be highly customizable. This section explains how you can tailor the calendar generation to your specific needs.

## Column Groups

The `generate_calendar_table` function and the `calendar_generator_cli.py` script allow you to specify which groups of columns to include in the generated calendar. This is done using the `column_groups` argument, which accepts a list of strings.

Available column groups are:

-   `time`: Includes `hour`, `minute`, `second`.
-   `standard`: Includes `year`, `month`, `quarter`, `month_name`, `week_ISO`, `iso_weekday`, `Week_US`, `day_name`, `day_of_week`, `day_of_year`, `is_weekend`, `is_month_start`, `is_month_end`, `is_quarter_start`, `is_quarter_end`, `is_year_start`, `is_year_end`, `is_leap_year`, `days_in_month`, `days_in_year`, `week_of_month`.
-   `fiscal`: Includes `ITTFiscalMonth` (based on a 4-4-5 pattern).
-   `additional`: Includes `WeekStart_ISO`, `WeekEnd_ISO`, `WeekStart_YearBounded`, `WeekEnd_YearBounded`, `WeekOfMonth`, `IsLastWeekOfMonth`, `MonthStart`, `MonthEnd`, `DaysInMonth`, `QuarterStart`, `QuarterEnd`, `DaysInQuarter`, `YearMonth`, `YearWeek`, `ISOWeekYear`.
-   `country_business`: Includes `IsHolidayDay_<country>` and `IsBusinessDay_<country>` for specified countries.
-   `regional`: Includes localized datetime, date, and business day flags for specified timezones (e.g., `datetime_Europe_Rome`, `is_business_day_Europe_Rome`, `is_dst_Europe_Rome`).
-   `extra`: Includes `semester`, `half_of_quarter`, `day_of_quarter`, `fiscal_year_jul`, `week_of_quarter`, `is_week_end`, `is_penultimate_day_of_month`, `is_first_business_day_month`, `is_last_business_day_year`.

**Example (CLI):**

```bash
python src/calendar_generator_cli.py --start 2023-01-01 --end 2023-01-02 --freq D \
    --column_groups standard regional extra \
    --output my_custom_calendar
```

## Regions and Countries

You can specify a list of timezone regions and countries for which to generate localized and business day flags.

-   **Regions:** Use the `--regions` argument in the CLI or the `regions` parameter in `generate_calendar_table`.
    Example: `--regions Europe/Rome US/Eastern Asia/Tokyo`

-   **Countries:** The `country_business` column group automatically generates flags for a default set of countries (`IT`, `CZ`, `CN`, `MX`). You can modify the `countries` parameter in the `add_country_business_day_flags` function within `src/calendar_utils.py` if you need to include different countries.

## Frequency

The `freq` argument (or `--freq` in CLI) allows you to specify the frequency of the datetime range. This uses pandas offset aliases.

**Common Frequencies:**

-   `D`: Daily
-   `H`: Hourly
-   `min`: Minutely
-   `S`: Secondly

**Example (CLI):**

```bash
python src/calendar_generator_cli.py --start 2023-01-01 --end 2023-01-01 --freq H \
    --output hourly_data
```

## Parallel Processing

The generator utilizes parallel processing to speed up the generation of large calendar tables. You can control the number of worker processes using the `n_workers` argument (or `--n_workers` in CLI).

-   By default, `n_workers` is set to the number of available CPU cores.
-   You can specify a custom number of workers, e.g., `--n_workers 4`.

## Output Format

The output format can be specified using the `--format` argument in the CLI or the `format` parameter in the `save_calendar` function.

**Supported Formats:**

-   `csv` (default)
-   `parquet`
-   `excel`
-   `json`

**Example (CLI):**

```bash
python src/calendar_generator_cli.py --start 2023-01-01 --end 2023-01-07 --output weekly_calendar --format parquet
```