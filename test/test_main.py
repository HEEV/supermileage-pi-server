import os
from unittest import mock

import main

def test_new_race_created_resets_globals():
    # set nonzero globals
    main.distance_traveled = 12345.6
    main.last_update = 999999999
    with mock.patch('data_reader.DataReader.reset_distance') as mock_reset:
        main.new_race_created()
        mock_reset.assert_called_once()

def test_create_serial_conn_while_testing():
    os.environ['TESTING'] = 'True'
    ser = main.create_serial_conn()
    assert ser is not None
    assert ser.read_response() is not None
    assert ser.is_open() == True