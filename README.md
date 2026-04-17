# Supermileage Pi Server

The primary service running on the Raspberry Pi to collect, format, and distribute data for the cars. 

## Description

The service takes in data from the Arduino board over serial, and sends the data to the local driver display and the remote cloud-based services, if available. It is a continually running service, and as such needs to have the robustness to survive various production-level failures.

This project uses the `uv` package manager to handle its dependencies and `pytest` to test it's base functionality.

## Environment Variables

| Variable Name         | Description                                                                    | Example                                      |
| --------------------- | ------------------------------------------------------------------------------ | -------------------------------------------- |
| MQTT_HOST             | the host address for the MQTT Broker                                           | localhost                                    |
| MQTT_PORT             | the port for the MQTT Broker                                                   | 9001                                         |
| MQTT_PUBLISH_TOPIC    | the topic to publish data packets to                                           | cars/car_a/data                              |
| MQTT_SUBSCRIBE_TOPIC  | the topic to receive messages from, primarily for config                       | cars/car_a/config                            |
| MQTT_SIMULATION_TOPIC | the topic to receive messages regarding the simulation from                    | cars/car_a/sim                               |
| MQTT_USERNAME         | the username credential of the computer for the MQTT Broker                    | car_a                                        |
| MQTT_PASSWORD         | the password credential of the computer for the MQTT Broker                    | password1                                    |
| CONFIG_FILE_PATH      | path to the sensor channel configuration file                                  | path/to/config.json                          |
| DATA_PACKET_SIZE      | **OPTIONAL** the size of the data packet expected from the Arduino             | 23                                           |
| TESTING               | **OPTIONAL** boolean to enable testing behavior, including mocking connections | True                                         |
| TEST_MQTT_MESSAGE     | **OPTIONAL** test message to be sent via test scripts                          | this is a test                               |
| DISABLE_REMOTE        | **OPTIONAL** boolean to disable the remote data connection                     | True                                         |
| DISABLE_LOCAL         | **OPTIONAL** boolean to disable the local file cache                           | True                                         |
| DISABLE_DISPLAY       | **OPTIONAL** boolean to disable the local display data connection              | True                                         | 
| CURRENT_CAR           | **OPTIONAL** The car that the computer is currently in                         | "karch"                                      |

## Getting Started

### Dependencies

- Python 3.11 or higher
- `pip`

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/HEEV/supermileage-pi-server.git
   cd supermileage-pi-server
   ```

2. Install `uv` and `Ruff` if you do not already have them.

   `uv` is our package manager for the project.

   ```bash
   pip install uv
   ```

   `Ruff` is the formatter/linter of choice.

   ```bash
   pip install ruff
   ```

### Executing Program

1. Create and fill a `.env` file for your local environment. See the environment section for what is needed to run the service.

2. To run the server within the uv environment, execute the following command:

   ```bash
   uv run src/main.py
   ```

### Testing Program

To run the test suite, simply execute the following:

```bash
uv run pytest
ruff check
```

These commands will ensure that your code does not have any regressions in functionality and still meets general formatting guidelines.

### Contribution Guidelines

To build the dependencies needed for this repository, run the following command:

```bash
# normal
uv sync

# with dev dependencies
uv sync --dev
```

Please refer to the [uv documentation](https://docs.astral.sh/uv/getting-started/) for more details on adding packages, removing packages, and more.

To be able to merge code into the main trunk of this repo, your changes are required to pass both our unit test suite (pytest) and ruff format checking. It is enforced by Github Actions.

## Authors

[@NathanielCavallaro](https://github.com/NathanielCavallaro)  
[@lkr33](https://github.com/lkr33)  
[@ZGeek03](https://github.com/ZGeek03) (Zaine F.)  
[@ArkinSolomon](https://github.com/ArkinSolomon) (Arkin Solomon)

## Version History

See [CHANGELOG.md](/CHANGELOG.md)