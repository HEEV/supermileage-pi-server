import os
import main

def test_cardata_to_map_and_fields():
    cd = main.CarData(
        time=123456789,
        voltage=11.1,
        speed=42.0,
        distance_traveled=100.5,
        car_id=7,
        user_input1=0,
        user_input2=1,
        engine_temp=95.2,
        rad_temp=60.3
    )
    m = cd.to_map()
    # keys from to_map
    expected_keys = {
        "time",
        "velocity",
        "distanceTraveled",
        "batteryVoltage",
        "engineTemp",
        "radTemp",
        "timerResetButton",
        "toggleTimeButton",
        "wind",
        "tilt"
    }
    assert set(m.keys()) == expected_keys
    assert m["time"] == 123456789
    assert m["batteryVoltage"] == 11.1
    assert m["velocity"] == 42.0
    assert m["distanceTraveled"] == 100.5
    assert m["timerResetButton"] == 0
    assert m["toggleTimeButton"] == 1
    assert m["engineTemp"] == 95.2
    assert m["radTemp"] == 60.3
    assert m["wind"] == 0
    assert m["tilt"] == 0


def test_parse_line():
    # [voltage, speed, unused, car_id, user_input1, user_input2, engine_temp, rad_temp]
    line = "12.5,30.0,ignored,2,1,0,85.5,70.2"

    # First parse: should set last_update but distance remains 0 (initially)
    data1 = main.parse_line(line)
    assert data1.voltage == 12.5
    assert data1.speed == 30.0
    assert data1.car_id == 2
    assert data1.engine_temp == 85.5
    assert data1.rad_temp == 70.2
    assert main.distance_traveled == 0

    # Simulate that last_update was earlier by 1000 ms so next call increases distance
    main.last_update = data1.time - 1000
    data2 = main.parse_line(line)

    # distance_traveled should have increased after the second parse
    assert main.distance_traveled > 0
    assert data2.distance_traveled == main.distance_traveled

def test_new_race_created_resets_globals():
    # set nonzero globals
    main.distance_traveled = 12345.6
    main.last_update = 999999999
    main.new_race_created()
    assert main.distance_traveled == 0
    assert main.last_update == 0

def test_create_serial_conn_while_testing():
    os.environ['TESTING'] = 'True'
    ser = main.create_serial_conn()
    assert ser is not None
    assert ser.read_response() is not None
    assert ser.is_open() == True