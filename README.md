# Supermileage Pi Server

This project is designed to run on a Raspberry Pi and uses the `uv` package manager to handle its dependencies and `pytest` to test it's base functionality.

## Prerequisites

- Python 3.8 or higher
- `pip`

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

