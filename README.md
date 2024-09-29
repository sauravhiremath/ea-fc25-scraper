
# EA FC 25 Player Data Scraper and Database

This project is a Python-based scraper that fetches player data from EA Sports FC 25 (formerly known as FIFA) and stores it in both JSON and compressed formats (GZIP).

## Features

- Asynchronous data fetching for improved performance
- Caching mechanism to avoid unnecessary API calls
- Compression of output data
- Comprehensive test suite

## Installation

1. Clone the repository
2. Install dependencies using Poetry (tested with Python 3.12):
    ```bash
    poetry install
    ```

## Usage

Run the main script:
```bash
poetry run python -m ea_fc25_scraper.index
```

This will fetch the player data and save it in the current directory.

## Testing

Run the tests:
```bash
poetry run pytest
```

## License
This project is licensed under the MIT License.
