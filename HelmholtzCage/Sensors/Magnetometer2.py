import board
import time
import adafruit_mlx90393

class Magnetometer:
    def __init__(self):
        self.Mx = []
        self.My = []
        self.Mz = []
        self.SENSOR = None

    def setup(self):
        "Connect board to I2C an set the gain"
        i2c = board.I2C()  # uses board.SCL and board.SDA
        self.SENSOR = adafruit_mlx90393.MLX90393(i2c, gain=adafruit_mlx90393.GAIN_1X)

    def read(self):
        "Read one measurement for each axis in [T]"
        self.Mx, self.My, self.Mz = self.SENSOR.magnetic
        self.Mx = self.Mx
        self.My = self.My
        self.Mz = self.Mz
        if self.SENSOR.last_status > adafruit_mlx90393.STATUS_OK:
            self.SENSOR.display_status()
        time.sleep(1)

    def display(self, unit):
        "Show last Read values 'T' or 'G'"
        if unit == 'T':
            self.MxT = self.Mx*0.000001
            self.MyT = self.My*0.000001
            self.MzT = self.Mz*0.000001
            print("X: {} T".format(self.MxT))
            print("Y: {} T".format(self.MyT))
            print("Z: {} T".format(self.MzT))
        elif unit == 'uT':
            print ("X: {} uT".format(self.Mx))
            print ("Y: {} uT".format(self.My))
            print ("Z: {} uT".format(self.Mz))
        elif unit == 'G':
            self.Mx2 = self.Mx*0.01
            self.My2 = self.My*0.01
            self.Mz2 = self.Mz*0.01
            print("X: {} G".format(self.Mx2))
            print("Y: {} G".format(self.My2))
            print("Z: {} G".format(self.Mz2))
        else:
            print("Please select T, uT, or G")
    def status(self):
        "Show the staus of the device"
        self.SENSOR.display_status()
