from os import getenv

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    "test_publisher",
    reconnect_on_failure=True,
    transport="websockets",
)  # Assign a client ID and set to reconnect on failure

broker_address = getenv(
    "MQTT_HOST", "localhost"
)  # Replace with your broker's IP if needed
client.ws_set_options(
    path=getenv("MQTT_PATH", "/mqtt")
)  # Set the WebSocket path if your broker uses one
client.username_pw_set(
    getenv("MQTT_USERNAME", "pits_crew"), getenv("MQTT_PASSWORD", "password3")
)
client.tls_set(cert_reqs=mqtt.ssl.CERT_REQUIRED)
client.connect(broker_address, int(getenv("MQTT_PORT", 1883)))

client.publish(
    getenv("MQTT_SUBSCRIBE_TOPIC", "cars/sting/data"),
    getenv("TEST_MQTT_MESSAGE", "Test message"),
    qos=0,
)  # Publish a test message

client.disconnect()
