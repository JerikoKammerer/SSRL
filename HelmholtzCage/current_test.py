from tkinter.filedialog import test
from InputPipeline import orbitPropagator as op
from InputPipeline import fieldGenerator as fg
from InputPipeline import currentGenerator as cg
from InputPipeline import orbitPropagator as op
from OutputPipeline import DutyCycle as dc
from OutputPipeline import PWM
from Sensors import Magnetometer2 as mag
from OutputPipeline import Pinout
from time import sleep

# Baseline B values for calibration
bX_base = 0.0573
bY_base = 0.1365
bZ_base = 0.00242

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
    return X_Cur, Y_Cur, Z_Cur

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
        automatic_test()
    else: 
        print("Invalid choice. Exiting.")
    while True:
        sleep(1) #wait for keyboard interrupt   
except KeyboardInterrupt:
    PWM.set_DutyCycles(0, 0, 0)
    print("Exiting Program")
