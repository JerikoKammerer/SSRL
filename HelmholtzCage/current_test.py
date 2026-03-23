from tkinter.filedialog import test
from InputPipeline import orbitPropagator as op
from InputPipeline import fieldGenerator as fg
from InputPipeline import currentGenerator as cg
from InputPipeline import orbitPropagator as op
from OutputPipeline import DutyCycle as dc
from OutputPipeline import PWM
from Sensors import Magnetometer2 as mag
from OutputPipeline import Pinout
from csvReader import readMagData
from time import sleep

# Baseline B values for calibration
bX_base = 0.091139
bY_base = -0.108239
bZ_base = -0.0128744

# Orbit Propagation
day = 2
month = 2
year = 2023
test_length = 4
segments = 4


PWM = PWM.PWM()
PWM.connectI2C()
PWM.set_frequency(1000)

pins = Pinout.Pins()
pins.set_directions(0, 0, 0)

# Propagate Orbits


# Calculates currents for each axis based on desired magnetic field strenghts
def calculateCurrents(bX, bY, bZ):
    X = cg.Coil('X-axis', (bX - bX_base), 30, 1, 0.5) # should it be bX - bX_base?
    X_Cur = X.single_current()

    Y = cg.Coil('Y-axis', (bY - bY_base), 30, 1, 0.55)
    Y_Cur = Y.single_current()

    Z = cg.Coil('Z-axis', (bZ - bZ_base), 30, 1, 0.525)
    Z_Cur = Z.single_current()

    print("Calculated Currents:")
    print("X Current: " + str(X_Cur) + " A")
    print("Y Current: " + str(Y_Cur) + " A")
    print("Z Current: " + str(Z_Cur) + " A")
    
    # sets coil directions
    X_Dir = X_Cur > 0
    Y_Dir = Y_Cur > 0
    Z_Dir = Z_Cur > 0
    pins.set_directions(X_Dir, Y_Dir, Z_Dir)

    return abs(X_Cur), abs(Y_Cur), abs(Z_Cur)
# Sets duty cycles based on calculated currents
def setDutyCycle(xCur, yCur, zCur):
    DC = dc.DutyCycle(xCur, yCur, zCur)
    DC.single_calc()

    print("Duty Cycles:")
    print("X Duty Cycle: " + str(DC.xDutyCycle))
    print("Y Duty Cycle: " + str(DC.yDutyCycle))
    print("Z Duty Cycle: " + str(DC.zDutyCycle))

    print("Setting PWM duty cycles...")
    PWM.set_DutyCycles(DC.xDutyCycle, DC.yDutyCycle, DC.zDutyCycle)

def manual_test():
    print("Enter desired magnetic field strength for X-axis in Gauss (G):")
    bX = float(input())
    print("Enter desired magnetic field strength for Y-axis in Gauss (G):")
    bY = float(input())
    print("Enter desired magnetic field strength for Z-axis in Gauss (G):")
    bZ = float(input())

    X_Cur, Y_Cur, Z_Cur = calculateCurrents(bX, bY, bZ)
    setDutyCycle(X_Cur, Y_Cur, Z_Cur)

def csv_test(data):
    mag490m1s, mag520m1s, mag490mhalfs, mag520mhalfs = readMagData()
    if data == 1:
        print("CSV Data Loaded: running 490 meter 1 second step test...")
        for entry in mag520m1s:
            bX = entry[0]
            bY = entry[1]
            bZ = entry[2]
            print("Setting B-field to: X: {}, Y: {}, Z: {}".format(bX, bY, bZ))
            X_Cur, Y_Cur, Z_Cur = calculateCurrents(bX, bY, bZ)
            setDutyCycle(X_Cur, Y_Cur, Z_Cur)
            sleep(1)  # wait for 1 second between steps
    elif data == 2:
        print("CSV Data Loaded: running 520 meter 1 second step test...")
        for entry in mag520m1s:
            bX = entry[0]
            bY = entry[1]
            bZ = entry[2]
            print("Setting B-field to: X: {}, Y: {}, Z: {}".format(bX, bY, bZ))
            X_Cur, Y_Cur, Z_Cur = calculateCurrents(bX, bY, bZ)
            setDutyCycle(X_Cur, Y_Cur, Z_Cur)
            sleep(1)  # wait for 1 second between steps
    elif data == 3:
        print("CSV Data Loaded: running 490 meter 0.5 second step test...")
        for entry in mag490mhalfs:
            bX = entry[0]
            bY = entry[1]
            bZ = entry[2]
            print("Setting B-field to: X: {}, Y: {}, Z: {}".format(bX, bY, bZ))
            X_Cur, Y_Cur, Z_Cur = calculateCurrents(bX, bY, bZ)
            setDutyCycle(X_Cur, Y_Cur, Z_Cur)
            sleep(0.5)  # wait for 0.5 second between steps
    elif data == 4:
        print("CSV Data Loaded: running 520 meter 0.5 second step test...")
        for entry in mag520mhalfs:
            bX = entry[0]
            bY = entry[1]
            bZ = entry[2]
            print("Setting B-field to: X: {}, Y: {}, Z: {}".format(bX, bY, bZ))
            X_Cur, Y_Cur, Z_Cur = calculateCurrents(bX, bY, bZ)
            setDutyCycle(X_Cur, Y_Cur, Z_Cur)
            sleep(0.5)  # wait for 0.5 second between steps
    else:
        print("Invalid data choice. Exiting CSV test.")    

def automatic_test():
    test = op.Orbit('ISS', test_length, segments)
    test.generate()
    test.display()

    mag = fg.MagneticField(test.positions, day, month, year, test_length, segments)
    mag.calculate()
    mag.fix_datatype()
    mag.display()
    mag.plot_fields()

    X_cur, Y_cur, Z_cur = calculateCurrents(mag.Bx[0], mag.By[0], mag.Bz[0])
    setDutyCycle(X_cur, Y_cur, Z_cur)
    
try:
    print("Manual or Automatic Test? (m/a): ")
    choice = input().lower()
    if choice == 'm':
        manual_test()
    elif choice == 'a':
        print("Which CSV data to use? (1: 490m 1s steps, 2: 520m 1s steps, 3: 490m 0.5s steps, 4: 520m 0.5s steps): ")
        data = int(input())
        csv_test(data)
    else: 
        print("Invalid choice. Exiting.")
    while True:
        sleep(1) #wait for keyboard interrupt   
except KeyboardInterrupt:
    PWM.set_DutyCycles(0, 0, 0)
    print("Exiting Program")
