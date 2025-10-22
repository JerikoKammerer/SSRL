class Pins:

    def __init__(self):
        # need catcher to suspend program when flags set to high
        self.FF1_X = 21
        self.FF2_X = 20
        self.FF1_Y = 25
        self.FF2_Y = 24
        self.FF1_Z = 27
        self.FF2_Z = 18

        # direction when set high will flow from OUTA -> OUTB
        self.DIR_X = 19
        self.DIR_Y = 23
        self.DIR_Z = 17

        # pwm outputs
        self.Current_Out_X = 29
        self.Current_Out_Y = 26
        self.Current_Out_Z = 24

        # reset
        self.resetX = 16
        self.resetY = 22
        self.resetZ = 4

        # magnetometer
        self.CS = 11
        self.I2C_SDA = 3
        self.I2C_SCL = 5
        self.VDD_3V3 = 1
        self.VSS_GND = 6

        # currentMonitors
        self.fiveVolt1 = 2
        self.fiveVolt2 = 4

        self.ground = 9
