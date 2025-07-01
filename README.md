# Calendar Table Generator

## Overview

This project provides a highly customizable and comprehensive calendar table generator in Python.  
It supports:
- Standard calendar columns (date, time, year, month, week, etc.)
- Fiscal calendar columns (ITT 4-4-5 pattern)
- Extended columns (week of month, leap year, business day flags, etc.)
- Regional columns (localized datetimes, DST, business EOM, etc.)
- Business day and holiday flags for multiple countries
- Extra analytics columns (semester, half of quarter, fiscal year July, week of quarter, etc.)
- Parallel processing for fast generation on multi-core systems

The generator is modular, efficient, and suitable for large date ranges and multiple timezones.

---

## Main Features

- **Standard Columns:** year, month, quarter, week, day, hour, minute, second, etc.
- **Fiscal Columns:** ITT fiscal month, week, and period boundaries.
- **Extended Columns:** week of month, is leap year, is year start/end, days in month/year, etc.
- **Regional Columns:** Localized datetimes, DST flag, business day flags, business EOM flags for each region.
- **Holiday/Business Day Flags:** For IT, CZ, CN, MX (customizable).
- **Extra Columns:** semester, half_of_quarter, day_of_quarter, fiscal_year_jul, week_of_quarter, is_week_end, is_penultimate_day_of_month, is_first_business_day_month, is_last_business_day_year, etc.
- **Parallel Processing:** Uses all available CPU cores by default for fast generation.

---

## Usage

### CLI

```sh
python src/calendar_generator.py
```

Or use the CLI version:

```sh
python src/calendar_generator_cli.py --start 2023-01-01 --end 2023-12-31 --freq D --regions Europe/Rome US/Eastern --output calendar_2023 --format csv
```

### Visualization

```sh
python src/visualize_business_eom.py calendar_2023.csv --region Europe_Rome --save eom_heatmap.png
```

### Test

```sh
python -m unittest src/test_calendar_generator.py
```

---

## Column Explanations

| Column Name                      | Description                                                      |
|----------------------------------|------------------------------------------------------------------|
| datetime_utc                     | UTC datetime                                                     |
| date_utc                         | Date (UTC)                                                       |
| hour, minute, second             | Time components                                                  |
| year, month, quarter             | Calendar year, month, quarter                                    |
| month_name, day_name             | Month and day names                                              |
| week_ISO, Week_US                | ISO week number, US week number                                  |
| iso_weekday, day_of_week         | ISO weekday (1=Mon), pandas weekday (0=Mon)                      |
| day_of_year                      | Day of year (1-366)                                              |
| is_weekend                       | True if Saturday or Sunday                                       |
| is_month_start, is_month_end     | True if first/last day of month                                  |
| is_quarter_start, is_quarter_end | True if first/last day of quarter                                |
| is_year_start, is_year_end       | True if first/last day of year                                   |
| is_leap_year                     | True if leap year                                                |
| days_in_month, days_in_year      | Number of days in month/year                                     |
| week_of_month                    | Week number within the month (1-based)                           |
| ITTFiscalMonth                   | ITT fiscal month (4-4-5 pattern)                                 |
| ...                              | Additional fiscal/extended columns (see code)                    |
| datetime_<region>                | Localized datetime for region (e.g., datetime_Europe_Rome)       |
| is_month_end_<region>            | True if last day of month in region                              |
| is_business_day_<region>         | True if business day in region                                   |
| is_business_month_end_<region>   | True if last business day of month in region                     |
| is_dst_<region>                  | True if DST is active in region                                  |
| date_<region>                    | Local date in region                                             |
| IsHolidayDay_<country>           | True if public holiday in country (IT, CZ, CN, MX, etc.)         |
| IsBusinessDay_<country>          | True if business day in country                                  |
| semester                         | 1 if Jan-Jun, 2 if Jul-Dec                                       |
| half_of_quarter                  | 1 or 2, half of the quarter                                      |
| day_of_quarter                   | Day number within the quarter                                    |
| fiscal_year_jul                  | Fiscal year starting in July                                     |
| week_of_quarter                  | Week number within the quarter                                   |
| is_week_end                      | True if Sunday                                                   |
| is_penultimate_day_of_month      | True if second-to-last day of month                              |
| is_first_business_day_month      | True if first business day of month                              |
| is_last_business_day_year        | True if last business day of year                                |

---

## Customization

- Add/remove regions or countries in the generator arguments.
- Extend with more fiscal or business logic as needed.
- Select which column groups to include via the `column_groups` argument.
- Use all available CPU cores by default, or specify `n_workers` for parallel processing.

---

## Performance

- Uses chunking and parallel processing for large date ranges.
- To see available CPU workers, use:
  ```python
  from calendar_utils import get_available_workers
  print(get_available_workers())
  ```
- Progress and chunk status are printed to the terminal during generation.

---

## License

MIT License

---

## Authors

- Your Name

---
