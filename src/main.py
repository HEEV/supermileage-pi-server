import asyncio
from os import getenv
from time import sleep

import nest_asyncio  # async in python is dumb idek what this does but stackoverflow said to do it and now it works
import socketio
from aiohttp import web
from dotenv import load_dotenv

from configuration_generator import ConfigurationGenerator
from data_reader import DataReader
from data_transmitter import LocalTransmitter, RemoteTransmitter, TransmitterError
from sm_serial import SmSerial, SmSerialError
from utils import get_env_flags

nest_asyncio.apply()

# initialize the local python server
localDisplaySio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
app = web.Application()
localDisplaySio.attach(app)


async def main():
    print("Initializing Server...")
    load_dotenv()
    # Load environment variables from .env file
    flags = get_env_flags()
    DISABLE_REMOTE = flags["DISABLE_REMOTE"]
    DISABLE_LOCAL = flags["DISABLE_LOCAL"]
    DISABLE_DISPLAY = flags["DISABLE_DISPLAY"]

    # Automatically generate configuration from a JSON file defined in the environment.
    config_gen = ConfigurationGenerator()
    data_reader = DataReader(config_gen)

    # Create CSV for this session
    car_cache = LocalTransmitter(config_gen.get_sensors()) if not DISABLE_LOCAL else None
    car_remote = RemoteTransmitter()if not DISABLE_REMOTE else None

    # port='COM6' #for testing on Windows only
    # TODO: Figure out exception handling here. Ultimately we do not want the server to fail here, just to crashloop until successful connection
    ser = SmSerial(timeout=0.025, crashloop=True)

    PACKET_SIZE = int(getenv("DATA_PACKET_SIZE")) if getenv("DATA_PACKET_SIZE") else 23

    # Spinning up the local python server
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 8080).start()

    # Main server loop
    while True:
        if ser.is_open():
            try:
                # read serial data from arduino
                last_line = ser.read_response(PACKET_SIZE)

                # parse the arduino data, send data to local (sio) and remote (cursor)
                data = data_reader.parse_sensor_data(last_line)
                print(data)
                if data:
                    # Broadcast to connected clients
                    if not DISABLE_DISPLAY:
                        await localDisplaySio.emit("new_data", data)
                        # TODO: Create way to identify which car we are using
                    await asyncio.sleep(0.05)

                    # Transmit to the cloud
                    if not DISABLE_REMOTE:
                        car_remote.handle_record(data)

                    # Write data locally to a CSV file
                    if not DISABLE_LOCAL:
                        car_cache.handle_record(data)
            except SmSerialError as exc:
                print(exc)
            except TransmitterError:
                print("Error writing to local cache.")
            except KeyboardInterrupt:
                print("Keyboard Interrupt, closing connections")
                ser.close()
                break
        else:
            # Serial is not open, give time to open
            ser.reconnect()
            sleep(3)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
