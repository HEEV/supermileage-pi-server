# Python Server Test Environment

To test the full functionality of the server locally, we need to run mocks of the external services it relies on. Currently, the only external service we rely on is the MQTT broker hosted at <supermileage.cedarville.edu/mqtt>.
Instead of hitting that, we want to perform all our testing on a local environment so as not to saturate the production services.

## Requirements

* Docker Desktop installation
* Python >3.11

## Environment

See `README.md` for a breakdown of typical environment variables.

## Setup

1. Stand up docker containers

We have a docker container set up for running locally. To spin this up, run the following commands.

```sh
cd local_development
docker compose up -d
```

This spins up a local Mosquitto broker instance on localhost. Check to make sure it is running correctly by running:

```sh
docker ps
```

and checking the output.

2. Set up environment variables

The server requires some environment variables to set up. These default `.env` values should get you started.

```sh
# Local MQTT
MQTT_HOST='localhost'
MQTT_PORT='9001'
MQTT_PATH='/mqtt'
MQTT_PUBLISH_TOPIC='cars/car_a/data'
MQTT_SUBSCRIBE_TOPIC='cars/car_a/config'
MQTT_USERNAME='car_a'
MQTT_PASSWORD='password1'
TEST_MQTT_MESSAGE='{"cars":{"car1":{"active":true,"theme":"color-theme","metadata":{"weight":200,"power_plant":"gasoline"},"sensors":{"channelA0":{"name":"voltage","unit":"volts","conversion_factor":0.35,"input_type":"analog","limits":{"min":0.0,"max":36.0}},"channel2":{"name":"button","unit":"","conversion_factor":0.0,"input_type":"digital","limits":{}}}},"car2":{"active":false,"theme":"color-theme","metadata":{},"sensors":{}}}}'

# Other Config
CONFIG_FILE_PATH="./test/testfiles/car_config.json"

# Testing Settings
TESTING="True"
DISABLE_REMOTE="False"
DISABLE_LOCAL="False"
DISABLE_DISPLAY="False"
```

3. Run test script for monitoring

To monitor the MQTT broker traffic, you can use the `mosquitto_sub.py` script. It subscribes to both the data and config topics and reports the output to stdout, so you can see the messages being passed around.

```sh
uv run mosquitto_sub.py
```

If you want to validate that the broker is functioning without running the server, you can run the `mosquitto_pub.py` script. It sends a single message over the subscribe topic, to emulate a message being sent to the server. To modify the message being sent, you can set the `TEST_MQTT_MESSAGE` environment variable.

```sh
uv run mosquitto_pub.py
```

4. Run server

To run the server, run this command at the root project directory.

```sh
uv run src/main.py
```

You can then use a combination of the above two scripts to test out different parts of the MQTT interactions with the server.
Additionally, the server will also run the other data transmission modes, including writing locally, so that the developer can monitor.