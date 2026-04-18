# Changelog

## Spring 2026

### Added

- Created Github Actions workflow to validate unit tests and code formatting ([#23](https://github.com/HEEV/supermileage-pi-server/pull/23)) (ZGeek03)
- Created DataTransmitter class structure to handle different types of data transmission ([#24](https://github.com/HEEV/supermileage-pi-server/pull/24)) (ZGeek03)
- Added function docstrings to all classes ([#24](https://github.com/HEEV/supermileage-pi-server/pull/24)) (ZGeek03)
- Added MQTT functionality, including local testing environment ([#26](https://github.com/HEEV/supermileage-pi-server/pull/26)) (ZGeek03)
- Added simluation message handling through SimulationHandler class ([#27](https://github.com/HEEV/supermileage-pi-server/pull/27)) (NathanielCavallaro)

### Changed

- Refactored codebase to pull functionality out of main.py, making it more testable ([#24](https://github.com/HEEV/supermileage-pi-server/pull/24)) (ZGeek03)

## Fall 2025

### Fixed

- Moved credentials to environment variables ([#9](https://github.com/HEEV/supermileage-pi-server/pull/9)) (ZGeek03)
- Fixed some bugs in serial connection usage ([#19](https://github.com/HEEV/supermileage-pi-server/pull/19)) (ZGeek03)

### Added

- Added wrapper class for serial connections ([#12](https://github.com/HEEV/supermileage-pi-server/pull/12)) (ZGeek03)
- Implemented pytest unit testing framework ([#13](https://github.com/HEEV/supermileage-pi-server/pull/13)) (lkr33)
- Added local testing functionality through environment variables ([#14](https://github.com/HEEV/supermileage-pi-server/pull/14)) (lkr33)
- Added ConfigurationGenerator and DataReader classes to handle new generalized sensor inputs and files ([#21](https://github.com/HEEV/supermileage-pi-server/pull/21)) (ZGeek03)

### Changed

- Standardized the python project file structure ([#21](https://github.com/HEEV/supermileage-pi-server/pull/21)) (ZGeek03)
