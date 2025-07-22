# Performance

The Calendar Table Generator is designed for efficiency, especially when dealing with large date ranges. It leverages parallel processing to utilize multiple CPU cores, significantly reducing generation time.

## Key Performance Features

-   **Chunking:** The generation process divides the total date range into smaller chunks. This helps manage memory usage and allows for parallel processing of these chunks.

-   **Parallel Processing:** By default, the generator uses all available CPU cores on your system. Each chunk is processed independently by a separate worker process, leading to faster overall completion times for large datasets.

    You can explicitly control the number of workers using the `n_workers` argument in the `generate_calendar_table` function or the `--n_workers` option in the CLI.

    To see the number of available CPU workers on your system, you can use the `get_available_workers` function:

    ```python
    from calendar_utils import get_available_workers
    print(get_available_workers())
    ```

-   **Optimized Column Generation:** The functions for adding various calendar columns are optimized for performance, using vectorized pandas operations where possible.

## Performance Considerations

-   **Date Range and Frequency:** The total number of rows generated directly impacts performance. A larger date range or a finer frequency (e.g., `min` vs. `D`) will result in more rows and thus longer generation times.

    The generator will issue a warning if you attempt to generate more than 10 million rows, suggesting a coarser frequency or a smaller date range.

-   **Number of Column Groups and Regions:** Including more column groups or a large number of regions will increase the computational load per row, as more calculations and data manipulations are performed.

-   **I/O Performance:** Saving the generated DataFrame to disk (especially for very large files) can be a bottleneck. Choosing an efficient format like Parquet can help, as it's optimized for columnar storage and faster read/write operations compared to CSV.

## Monitoring Progress

When running the `calendar_generator.py` or `calendar_generator_cli.py` scripts, you will see progress updates in your terminal, indicating the overall generation progress and the processing of individual chunks.
