import asyncio
import datetime
import math
from dataclasses import dataclass
import serial
import socketio
from aiohttp import web
import aiohttp.web_runner
from csv import writer

# async in python is dumb idek what this does but stackoverflow said to do it and now it works
import nest_asyncio

nest_asyncio.apply()

# initialize the local python server
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# initialize server object for remote connection
# TODO: update connect url for new server
#sio_client = socketio.SimpleClient(ssl_verify=False)
#sio_client.connect('https://judas.arkinsolomon.net')
# Get permission from the remote server to transmit
#sio_client.emit('request_write_permission', 'squid')

#Create CSV for this session
data_file_name = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_car_data.csv')
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
@sio.event
async def request_new_race(sid):
    print("requesting new race...")
    #sio_client.emit('request_new_race')

# The data object format for sending arduino data to display servers
@dataclass
class CarData:
    time: int
    voltage: float
    speed: float
    distance_traveled: float

    def to_map(self):
        return {
            "time": self.time,
            "velocity": self.speed,
            "distanceTraveled": self.distance_traveled,
            "batteryVoltage": self.voltage,
            "engineTemp": 0,
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
    if last_update > 0:
        delta = timestamp - last_update

        # mph -> Ft/ms
        speedFtms = 0.00146667 * car_speed
        distance_traveled += speedFtms * delta
    last_update = timestamp
    # print(timestamp)
    return CarData(time=timestamp, voltage=float(output[0]), speed=car_speed, distance_traveled=distance_traveled)


async def main():
    # arduino serial connection initialization
    port = '/dev/tty.usbserial-14130' #COM6
    baud_rate = 9600
    ser = serial.Serial(port, baud_rate, timeout=0.025)


    # Spinning up the local python server
    runner = aiohttp.web.AppRunner(app)

    await runner.setup()
    await aiohttp.web.TCPSite(runner, '0.0.0.0', 8080).start()

    # Main server loop
    while True:

        # check for events from the remote server
        try:
            event = None# sio_client.receive(timeout=1)
            if event is not None:
                event_name = event[0]
                
                # If we got write permission, get a new race save. 
                # If the race is successfully created, set up to deliver data
                if event_name == 'permission_granted':
                    print("requesting new race...")# sio_client.emit('request_new_race')
                elif event_name == 'new_race_created':
                    new_race_created()

            # print(f'received event: "{event[0]}" with arguments {event[1:]}')
        except:
            pass

        # read serial data from arduino
        try:
            last_line = ser.readline().decode('utf-8')
            next_line = ser.readline().decode('utf-8')
            while next_line != '':
                last_line = next_line
                next_line = ser.readline().decode('utf-8')
        except:
            continue

        # parse the arduino data, send data to local (sio) and remote (sio_client)
        try:
            data = parse_line(last_line)
            print(data)
            # Broadcast to connected clients
            await sio.emit('new_data', data.to_map())
            # Broadcast to remote server
            # sio_client.emit('write_data', data.to_map())
            await asyncio.sleep(.05)
        except Exception as e:
            print(f'Exception while parsing/sending data: {last_line}, {e}')
            pass

        try: 
            with open(data_file_name, 'a') as file:
                csv_writer = writer(file)
                data = parse_line(last_line)
                data_tuple = [data.time, data.voltage, data.speed, data.distance_traveled]
                csv_writer.writerow(data_tuple)
        except: pass

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
