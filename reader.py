import serial

# Read data from serial
class Reader:

    # Class constructor, open the serial file
    def __init__(self, file):

        # Set up serial
        self.ser = serial.Serial(file, 9600)

    # Read a line from the serial
    def readline(self) -> str:
        return self.ser.readline().decode('ascii').strip()
