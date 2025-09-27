import asyncio
import datetime
import glob
import math
from dataclasses import dataclass
from psycopg2 import DatabaseError
from serial import Serial
from serial import serialutil
import socketio
from aiohttp import web
import aiohttp.web_runner
from csv import writer
from time import sleep
import asyncpg

# async in python is dumb idek what this does but stackoverflow said to do it and now it works
import nest_asyncio

nest_asyncio.apply()

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
    global distance_traveled, last_update
    distance_traveled = 0
    last_update = 0

# Send request for a new race to remote server, not used?
@localDisplaySio.event
async def request_new_race(sid):
    print("requesting new race...")
    #sio_client.emit('request_new_race')

# The data object format for sending arduino data to display servers
@dataclass
class CarData:
    time:              int
    voltage:           float
    speed:             float
    distance_traveled: float
    car_id:            int
    user_input1:       int
    user_input2:       int
    engine_temp:       float
    rad_temp:          float

    def to_map(self):
        return {
            "time": self.time,
            "velocity": self.speed,
            "distanceTraveled": self.distance_traveled,
            "batteryVoltage": self.voltage,
            "engineTemp": self.engine_temp,
            "radTemp": self.rad_temp,
            "timerResetButton": self.user_input1,
            "toggleTimeButton": self.user_input2,
            "wind": 0,
            "tilt": 0
        }

# parse the serial data from the arduino into CarData object
def parse_line(line: str) -> CarData:
    global last_update, distance_traveled

    if distance_traveled > 100000000:
        distance_traveled = 0

    output = line.split(',')
    utc_dt_aware = datetime.datetime.now(datetime.timezone.utc)
    timestamp = math.floor(utc_dt_aware.timestamp() * 1000)

    car_speed = float(output[1])
    car_id = int(output[3])
    user_input1 = int(output[4])
    user_input2 = int(output[5])
    engine_temp = float(output[6])
    rad_temp = float(output[7])
    if last_update > 0:
        delta = timestamp - last_update

        # mph -> Ft/ms
        speedFtms = 0.00146667 * car_speed
        distance_traveled += speedFtms * delta
    last_update = timestamp
    # print(timestamp)

    return CarData(time=timestamp, voltage=float(output[0]), speed=car_speed, distance_traveled=distance_traveled,
                    car_id=car_id, user_input1=user_input1, user_input2=user_input2, engine_temp=engine_temp, rad_temp=rad_temp)

# create a serial connection to the arduino
def create_serial_conn():
    usb_devices = glob.glob("/dev/ttyUSB*")
    port = ''
    if usb_devices:
        port = usb_devices[0] #COM6
    else:
        port = '/dev/ttyUSB1'

    # port='COM6' #for testing only
    baud_rate = 9600
    ser = None
    arduino_connected = False
    while not arduino_connected:
        try:
            ser = Serial(port, baud_rate, timeout=0.025)
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
        conn = await asyncpg.connect(database="b7ghmkoed5btwtb6org5",
                                     host="b7ghmkoed5btwtb6org5-postgresql.services.clever-cloud.com",
                                     user="uoh8y5okijoz5xxdiqit",
                                     password="qFhTMlsKuzHqobkU2z24AzIOxXYisS",
                                     port="6642")
    except:
        conn = None
    return conn

async def main():
    print("Initializing Server...")
    datapoint_count = 0
    db_live = False
    # arduino serial connection initialization
    ser = create_serial_conn()

    # initialize server object for remote connection to database
    conn = await db_conn_init()

    # Spinning up the local python server
    runner = aiohttp.web.AppRunner(app)

    await runner.setup()
    await aiohttp.web.TCPSite(runner, '0.0.0.0', 8080).start()

    # Main server loop
    #sleep(3)
    while True:
        # Re-instantiate database if it died at some point
        if not db_live:
            print("Database is down, attempting reconnect...")
            conn = await db_conn_init()
            if conn is None:
                db_live = False
            else:
                db_live = True


        try:
            # read serial data from arduino
            try:
                last_line = ser.readline().decode('utf-8')
                next_line = ser.readline().decode('utf-8')
                while next_line != '':
                    last_line = next_line
                    next_line = ser.readline().decode('utf-8')
            except serialutil.SerialException:
                print(f'error reading serial, check Arduino connection')
                ser = create_serial_conn()
            except Exception as e:
                print(f'Unknown error reading from serial: {e}')
                continue

            # parse the arduino data, send data to local (sio) and remote (cursor)
            try:
                data = parse_line(last_line)
                print(data)
                # Broadcast to connected clients
                await localDisplaySio.emit('new_data', data.to_map())
                # TODO: Create way to identify which car we are using
                # insert values into database, but only every 20th datapoint
                # This prevents over-saturation of the database connection
                try:
                    datapoint_count += 1
                    if datapoint_count >= 20 and db_live:
                        await asyncio.wait_for(
                            conn.execute(
                                f'insert into car_acquisition.car_data (car_id, time, voltage, speed, engine_temp, rad_temp, distance_traveled) VALUES ({data.car_id}, {data.time}, {data.voltage}, {data.speed}, {data.engine_temp}, {data.rad_temp}, {data.distance_traveled})'),
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
            try:
                with open(data_file_name, 'a') as file:
                    csv_writer = writer(file)
                    data = parse_line(last_line)
                    data_tuple = [data.time, data.voltage, data.speed, data.distance_traveled]
                    csv_writer.writerow(data_tuple)
            except:
                print("Error writing to CSV")
        except KeyboardInterrupt as e:
            print("Keyboard Interrupt, closing connections")
            ser.close()
            await conn.close()
            break

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
