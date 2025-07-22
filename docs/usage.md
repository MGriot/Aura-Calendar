# Usage

This section details how to use the Calendar Table Generator.

## Command Line Interface (CLI)

The primary way to generate a calendar table is through the command-line interface.

### Basic Usage

To generate a calendar table, you need to specify a start date, an end date, and an output filename.

```bash
python src/calendar_generator_cli.py --start 2023-01-01 --end 2023-12-31 --output my_calendar
```

This will generate a CSV file named `my_calendar.csv` in the current directory, containing daily entries for the year 2023.

### Full CLI Options

```
usage: calendar_generator_cli.py [-h] --start START --end END [--freq FREQ]
                                 [--regions [REGIONS ...]]
                                 [--column_groups [COLUMN_GROUPS ...]]
                                 [--n_workers N_WORKERS] --output OUTPUT
                                 [--format {csv,parquet,excel,json}]

Generate a comprehensive calendar table with timezone support.

options:
  -h, --help            show this help message and exit
  --start START         Start datetime (e.g., '2020-01-01')
  --end END             End datetime (e.g., '2025-12-31')
  --freq FREQ           Frequency (e.g., '5min', 'D', 'H')
  --regions [REGIONS ...]
                        List of timezones (e.g., 'US/Eastern Europe/Rome')
  --column_groups [COLUMN_GROUPS ...]
                        List of column groups to include (e.g., 'standard fiscal')
  --n_workers N_WORKERS
                        Number of parallel processes to use. Defaults to number of CPU cores.
  --output OUTPUT       Output filename without extension
  --format {csv,parquet,excel,json}
                        Output file format
```

### Examples

-   **Generate daily calendar for a specific year with multiple regions:**

    ```bash
    python src/calendar_generator_cli.py --start 2024-01-01 --end 2024-12-31 --freq D \
        --regions Europe/Rome US/Eastern Asia/Tokyo \
        --output calendar_2024_multi_region --format csv
    ```

-   **Generate hourly calendar with specific column groups:**

    ```bash
    python src/calendar_generator_cli.py --start 2023-01-01 --end 2023-01-02 --freq H \
        --column_groups time standard regional \
        --output hourly_calendar --format parquet
    ```

-   **Generate calendar with a specific number of workers:**

    ```bash
    python src/calendar_generator_cli.py --start 2025-01-01 --end 2025-03-31 --freq D \
        --n_workers 4 --output q1_2025_calendar
    ```

## Visualization

The project also includes a script to visualize business end-of-month (EOM) days.

```bash
python src/visualize_business_eom.py your_calendar_file.csv --region Europe_Rome --save eom_heatmap.png
```

### Visualization CLI Options

```
usage: visualize_business_eom.py [-h] [--region REGION] [--save SAVE] file

Visualize Business End-of-Month Days from Calendar CSV

positional arguments:
  file                  Path to the calendar CSV file

options:
  -h, --help            show this help message and exit
  --region REGION       Region to visualize (e.g., Europe_Rome)
  --save SAVE           Path to save the heatmap image
```

### Visualization Examples

-   **Visualize EOM for a specific region:**

    ```bash
    python src/visualize_business_eom.py calendar_2024_multi_region.csv --region Europe_Rome --save europe_eom.png
    ```

-   **Visualize EOM for all regions found in the file (without specifying `--region`):**

    ```bash
    python src/visualize_business_eom.py calendar_2024_multi_region.csv
    ```

```