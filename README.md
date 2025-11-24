# Supermileage Pi Server

This project is designed to run on a Raspberry Pi and uses the `uv` package manager to handle its dependencies and `pytest` to test it's base functionality.

## Prerequisites

- Python 3.8 or higher
- `pip`

## Environment

| Variable Name    | Description                                                                    | Example                                     |
| ---------------- | ------------------------------------------------------------------------------ | ------------------------------------------- |
| DB_HOST          | Database host URL                                                              | 123abc-postgresql.services.clever-cloud.com |
| DB_USER          | Database username                                                              | username                                    |
| DB_PASSWORD      | Database password                                                              | password                                    |
| DB_PORT          | Database port number                                                           | 6642                                        |
| DB               | Database name                                                                  | b7ghmkoed5btwtb6org5                        |
| CONFIG_FILE_PATH | path to the sensor channel configuration file                                  | path/to/config.json                         |
| DATA_PACKET_SIZE | **OPTIONAL** the size of the data packet expected from the Arduino             | 23                                          |
| TESTING          | **OPTIONAL** boolean to enable testing behavior, including mocking connections | True                                        |
| DISABLE_REMOTE   | **OPTIONAL** boolean to disable the remote data connection                     | True                                        |
| DISABLE_LOCAL    | **OPTIONAL** boolean to disable the local file cache                           | True                                        |
| DISABLE_DISPLAY  | **OPTIONAL** boolean to disable the local display data connection              | True                                        | 

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/HEEV/supermileage-pi-server.git
    cd supermileage-pi-server
    ```

2. Install `uv`:
    ```bash
    pip install uv
    ```

## Usage

To build the dependencies needed for this repository, run the following command:
```bash
# normal
uv sync

# with dev dependencies
uv sync --dev
```

To run the server within the uv environment, execute the following command:
```bash
uv run main.py
```

To run the test suite [with or without the verbose option], simply execute the following:
```bash
uv run pytest
```

Please refer to the [uv documentation](https://docs.astral.sh/uv/getting-started/) for more details on adding packages, removing packages, and more.

