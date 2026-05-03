# Aura Calendar

## Overview

Aura Calendar is a high-density, professional planning suite and a comprehensive calendar table generator. The project has evolved to include a modern web application consisting of a React/Vite frontend and a FastAPI backend, alongside its original robust calendar table generator script.

## Main Features

### Web Application
- **Frontend:** A React/Vite based user interface designed for a professional visual organization, including a continuous multi-day event banners system, "Day Explosion" modal, and dynamic color mapping.
- **Backend:** A lightweight FastAPI server providing endpoints to generate calendar data and load events.
- **Dockerized Environment:** The entire application stack is containerized using Docker and Docker Compose for easy deployment and development.

### Calendar Table Generator (CLI/Python)
- **Standard & Extended Columns:** date, time, year, month, week, ITT 4-4-5 pattern, week of month, leap year flags, etc.
- **Regional Support:** Localized datetimes, DST, business EOM flags, holidays for IT, CZ, CN, MX.
- **Performance:** Parallel processing for fast generation on multi-core systems.

## Documentation

For detailed information on usage, architecture, and running the web app, please refer to the [full documentation](./docs/index.md).

## Running the Web Application

The easiest way to run the web application (both frontend and backend) is via Docker Compose:

```sh
docker-compose up --build
```

- **Frontend:** Available at `http://localhost:5173`
- **Backend API:** Available at `http://localhost:8000`

For more detailed instructions, including running locally without Docker, see the [Running the App Documentation](./docs/running_the_app.md).

## Usage - Calendar Table Generator (CLI)

To generate a calendar table using the command-line interface:

```sh
python src/calendar_generator_cli.py --start 2023-01-01 --end 2023-12-31 --freq D --regions Europe/Rome US/Eastern --output calendar_2023 --format csv
```

For more detailed usage instructions and examples, see the [Usage Documentation](./docs/usage.md).

## License

MIT License
