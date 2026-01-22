import main

def test_create_serial_conn_while_testing(default_env):
    ser = main.create_serial_conn()
    assert ser is not None
    assert ser.read_response() is not None
    assert ser.is_open()