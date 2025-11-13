import asyncio
import datetime
import math
from dataclasses import dataclass
from os import getenv
from psycopg2 import DatabaseError
from serial import serialutil
import socketio
from aiohttp import web
from csv import writer
from time import sleep
import asyncpg
from data_reader import DataReader
from sm_serial import SmSerial
from configuration_generator import ConfigurationGenerator
from dotenv import load_dotenv

# async in python is dumb idek what this does but stackoverflow said to do it and now it works
import nest_asyncio

nest_asyncio.apply()

# Load environment variables from .env file
load_dotenv()

# Automatically generate configuration from a JSON file defined in the environment.
config_gen = ConfigurationGenerator()

data_reader = DataReader(config_gen)

# initialize the local python server
localDisplaySio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
localDisplaySio.attach(app)

#Create CSV for this session
data_file_name = datetime.datetime.now().strftime('Data/%Y-%m-%d_%H-%M-%S_car_data.csv')
with open(data_file_name, 'w') as file:
    csv_writer = writer(file)
    csv_writer.writerow(["time", "voltage", "speed", "distance_traveled"])

distance_traveled = 0
last_update = 0
# reset base variables when new race is requested
def new_race_created():
    data_reader.reset_distance()

# Send request for a new race to remote server, not used?
@localDisplaySio.event
async def request_new_race(sid):
    print("requesting new race...")
    #sio_client.emit('request_new_race')

# Environment variable flags to enable/disable data sending
def get_env_flags():
    return {
        'DISABLE_REMOTE': getenv('DISABLE_REMOTE', 'False') == 'True',
        'DISABLE_LOCAL': getenv('DISABLE_LOCAL', 'False') == 'True',
        'DISABLE_DISPLAY': getenv('DISABLE_DISPLAY', 'False') == 'True', 
        'TESTING': getenv('TESTING', 'False') == 'True'
    }

# create a serial connection to the arduino
def create_serial_conn() -> SmSerial | None:
    ser = None
    arduino_connected = False
    while not arduino_connected:
        try:
            #port='COM6' #for testing on Windows only
            ser = SmSerial(timeout=0.025)
            arduino_connected = True
        except serialutil.SerialException as e:
            if "PermissionError" in str(e):
                print(f'Permission Error, try unplugging and replugging arduino. Retrying in 3 seconds...')
            else:
                print(f'Arduino is missing, please connect the arduino. Retrying in 3 seconds... \n {e}')
            sleep(3)
        except:
            print("Unknown error occurred, retrying in 3 seconds...")
            sleep(3)
    return ser

# Database init
async def db_conn_init():
    conn = None
    try:
        conn = await asyncpg.connect(database=getenv('DB'),
                                     host=getenv('DB_HOST'),
                                     user=getenv('DB_USER'),
                                     password=getenv('DB_PASSWORD'),
                                     port=getenv('DB_PORT'))
    except:
        conn = None
    return conn

async def main():

    flags = get_env_flags()
    DISABLE_REMOTE = flags['DISABLE_REMOTE']
    DISABLE_LOCAL = flags['DISABLE_LOCAL']
    DISABLE_DISPLAY = flags['DISABLE_DISPLAY']
    TESTING = flags['TESTING']
    print("Initializing Server...")
    datapoint_count = 0
    db_live = False

    # arduino serial connection initialization
    ser = create_serial_conn() 

    # initialize server object for remote connection to database
    conn = await db_conn_init()

    # Spinning up the local python server
    runner = web.AppRunner(app)

    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 8080).start()

    # Main server loop
    #sleep(3)
    if ser is not None:
        while True:
            # Re-instantiate database if it died at some point
            if not db_live and not DISABLE_REMOTE:
                print("Database is down, attempting reconnect...")
                conn = await db_conn_init()
                if conn is None:
                    db_live = False
                else:
                    db_live = True

            try:
                # read serial data from arduino
                try:
                    last_line = ser.read_response()
                    next_line = ser.read_response()
                    while next_line != '':
                        last_line = next_line
                        next_line = ser.read_response()
                except serialutil.SerialException:
                    print(f'error reading serial, check Arduino connection')
                    ser = create_serial_conn()
                except Exception as e:
                    print(f'Unknown error reading from serial: {e}')
                    continue

                # parse the arduino data, send data to local (sio) and remote (cursor)
                try:
                    data = data_reader.read_sensor_data(last_line)
                    print(data)
                    # Broadcast to connected clients
                    if not DISABLE_DISPLAY:
                        await localDisplaySio.emit('new_data', data)
                        # TODO: Create way to identify which car we are using
                        # insert values into database, but only every 20th datapoint
                        # This prevents over-saturation of the database connection
                    try:
                        datapoint_count += 1
                        if datapoint_count >= 20 and db_live and not DISABLE_REMOTE:
                            await asyncio.wait_for(
                                conn.execute(
                                    f'insert into car_acquisition.car_data (car_id, time, voltage, speed, engine_temp, rad_temp, distance_traveled) VALUES ({0}, {data["time"]}, {data["voltage"]}, {data["speed"]}, {data["engine_temp"]}, {data["rad_temp"]}, {data["distance_traveled"]})'),
                                timeout=1.0  # Set your desired timeout in seconds
                            )
                            datapoint_count = 0
                    except DatabaseError as e:
                        print(f'Error inserting into database, rolling back query: {e}')
                        db_live = False
                        conn = None
                    except (TimeoutError, asyncio.exceptions.CancelledError):
                        print(f'Timeout error inserting into database')
                        db_live = False
                        conn = None

                    await asyncio.sleep(.05)
                except Exception as e:
                    print(f'Exception while parsing/sending data: {last_line}, {e}')
                    pass

                # Write data locally to a CSV file
                if not DISABLE_LOCAL:
                    try:
                        with open(data_file_name, 'a') as file:
                            csv_writer = writer(file)
                            data_list = [data["time"], data["voltage"], data["speed"], data["distance_traveled"]]
                            csv_writer.writerow(data_list)
                    except:
                        print("Error writing to CSV")
            except KeyboardInterrupt as e:
                print("Keyboard Interrupt, closing connections")
                ser.close()
                await conn.close()
                break

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
