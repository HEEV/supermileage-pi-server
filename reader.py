import serial

# Read data from serial
class Reader:

    # Class constructor, open the serial file
    def __init__(self, file):

        # Set up serial
        self.ser = serial.Serial(file, 9600)

    # Read a line from the serial
    def readline(self) -> int:
        binary = self.ser.readline()
        print(binary)
        return int.from_bytes(binary, "big")
