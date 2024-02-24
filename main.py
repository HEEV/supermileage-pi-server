import asyncio
import datetime
import math
from dataclasses import dataclass

import aiohttp.web_runner
# async in python is dumb idek what this does but stackoverflow said to do it and now it works
import nest_asyncio
import serial
import socketio
from aiohttp import web

nest_asyncio.apply()
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)


@dataclass
class CarData:
    time: int
    voltage: float
    speed: float

    def to_map(self):
        return {
            "time": self.time,
            "velocity": self.speed,
            "distanceTraveled": 0,
            "batteryVoltage": self.voltage,
            "engineTemp": 0,
            "wind": 0,
            "tilt": 0
        }


def parse_line(line: str) -> CarData:
    output = line.split(',')
    timestamp = math.floor(datetime.datetime.utcnow().timestamp() * 1000)
    return CarData(time=timestamp, voltage=float(output[0]), speed=float(output[1]))


async def main():
    port = '/dev/tty.usbserial-14110'
    baud_rate = 9600
    ser = serial.Serial(port, baud_rate, timeout=0.025)

    runner = aiohttp.web.AppRunner(app)

    await runner.setup()
    await aiohttp.web.TCPSite(runner, '0.0.0.0', 8080).start()

    while True:
        data = ser.readline()
        if data == b'':
            continue

        data = str(data)[2:-5]

        try:
            data = parse_line(data)
            print(data)
            await sio.emit('new_data', data.to_map())
            await asyncio.sleep(.25)
        except:
            pass


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
