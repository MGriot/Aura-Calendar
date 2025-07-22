# Calendar Table Generator

## Overview

This project provides a highly customizable and comprehensive calendar table generator in Python, designed for various analytical and reporting needs. It supports:

-   Standard calendar columns (date, time, year, month, week, etc.)
-   Fiscal calendar columns (ITT 4-4-5 pattern)
-   Extended columns (week of month, leap year, business day flags, etc.)
-   Regional columns (localized datetimes, DST, business EOM, etc.)
-   Business day and holiday flags for multiple countries
-   Extra analytics columns (semester, half of quarter, fiscal year July, week of quarter, etc.)
-   Parallel processing for fast generation on multi-core systems

The generator is modular, efficient, and suitable for large date ranges and multiple timezones.

## Documentation

For detailed information on usage, modules, column explanations, customization, and performance, please refer to the [full documentation](./docs/index.md).

## Main Features

-   **Standard Columns:** year, month, quarter, week, day, hour, minute, second, etc.
-   **Fiscal Columns:** ITT fiscal month, week, and period boundaries.
-   **Extended Columns:** week of month, is leap year, is year start/end, days in month/year, etc.
-   **Regional Columns:** Localized datetimes, DST flag, business day flags, business EOM flags for each region.
-   **Holiday/Business Day Flags:** For IT, CZ, CN, MX (customizable).
-   **Extra Columns:** semester, half_of_quarter, day_of_quarter, fiscal_year_jul, week_of_quarter, is_week_end, is_penultimate_day_of_month, is_first_business_day_month, is_last_business_day_year, etc.
-   **Parallel Processing:** Uses all available CPU cores by default for fast generation.

## Usage

### CLI

To generate a calendar table using the command-line interface:

```sh
python src/calendar_generator_cli.py --start 2023-01-01 --end 2023-12-31 --freq D --regions Europe/Rome US/Eastern --output calendar_2023 --format csv
```

For more detailed usage instructions and examples, see the [Usage Documentation](./docs/usage.md).

### Visualization

To visualize business end-of-month (EOM) days from a generated calendar file:

```sh
python src/visualize_business_eom.py calendar_2023.csv --region Europe_Rome --save eom_heatmap.png
```

### Testing

To run the unit tests for the calendar generator:

```sh
pip install pandas pytz
python -m unittest src/test_calendar_generator.py
```

## Customization

The generator is highly customizable. You can:

-   Add/remove regions or countries in the generator arguments.
-   Extend with more fiscal or business logic as needed.
-   Select which column groups to include via the `column_groups` argument.
-   Use all available CPU cores by default, or specify `n_workers` for parallel processing.

For a complete guide on customization options, refer to the [Customization Documentation](./docs/customization.md).

## Performance

The generator is optimized for performance, especially for large date ranges, utilizing chunking and parallel processing. For more details, see the [Performance Documentation](./docs/performance.md).

## License

MIT License

## Authors

- Your Name

---
