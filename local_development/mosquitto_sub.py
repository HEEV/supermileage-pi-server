import time
from os import getenv

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()


# The callback for when the client receives a CONNACK response from the broker.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(getenv("MQTT_PUBLISH_TOPIC", "cars/sting/data"))  # Subscribe to the topic
    client.subscribe(getenv("MQTT_SUBSCRIBE_TOPIC", "cars/sting/data"))  # Subscribe to the topic


# The callback for when a PUBLISH message is received from the broker.
def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

# Create an MQTT client instance
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2, "test_subscriber", transport="websockets"
)  # Assign a client ID

# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

print(f"connecting to {getenv('MQTT_HOST', 'localhost')}:{getenv('MQTT_PORT', 1883)}")

# Connect to the broker (defaults to localhost:1883)
broker_address = getenv("MQTT_HOST", "localhost")  # Replace with your broker's IP if needed
client.ws_set_options(path=getenv("MQTT_PATH", "/mqtt"))  # Set the WebSocket path if your broker uses one
client.username_pw_set(getenv("MQTT_USERNAME", "pits_crew"), getenv("MQTT_PASSWORD", "password3"))
client.connect(broker_address, int(getenv("MQTT_PORT", 1883)))

# Start the network loop in a non-blocking way.
client.loop_start()

try:
    # Keep the script running to receive messages
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Subscriber stopped by user")

client.loop_stop()
client.disconnect()
