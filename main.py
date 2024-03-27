import asyncio
import datetime
import math
from dataclasses import dataclass
import serial
import socketio
from aiohttp import web
import aiohttp.web_runner

# async in python is dumb idek what this does but stackoverflow said to do it and now it works
import nest_asyncio

nest_asyncio.apply()
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

sio_client = socketio.SimpleClient()
sio_client.connect('http://judas.arkinsolomon.net')
sio_client.emit('request_write_permission', 'squid')

distance_traveled = 0
last_update = 0


def new_race_created():
    global distance_traveled, last_update
    distance_traveled = 0
    last_update = 0


@sio.event
async def request_new_race(sid):
    sio_client.emit('request_new_race')


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


def parse_line(line: str) -> CarData:
    global last_update, distance_traveled
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
    port = '/dev/tty.usbserial-14140'
    baud_rate = 9600
    ser = serial.Serial(port, baud_rate, timeout=0.025)

    runner = aiohttp.web.AppRunner(app)

    await runner.setup()
    await aiohttp.web.TCPSite(runner, '0.0.0.0', 8080).start()

    while True:

        try:
            event = sio_client.receive(timeout=1)
            if event is not None:
                event_name = event[0]
                if event_name == 'permission_granted':
                    sio_client.emit('request_new_race')
                elif event_name == 'new_race_created':
                    new_race_created()

            # print(f'received event: "{event[0]}" with arguments {event[1:]}')
        except:
            pass

        try:
            last_line = ser.readline().decode('utf-8')
            next_line = ser.readline().decode('utf-8')
            while next_line != '':
                last_line = next_line
                next_line = ser.readline().decode('utf-8')
        except:
            continue

        try:
            data = parse_line(last_line)
            print(data)
            await sio.emit('new_data', data.to_map())
            sio_client.emit('write_data', data.to_map())
            await asyncio.sleep(.25)
        except:
            print(f'Exception while parsing/sending data: {last_line}')
            pass


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
