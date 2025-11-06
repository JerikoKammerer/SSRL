from InputPipeline import currentGenerator as cg
from OutputPipeline import DutyCycle as dc
from OutputPipeline import PWM
from Sensors import Magnetometer2 as mag
from OutputPipeline import Pinout
from time import sleep

Mag = mag.Magnetometer()
Mag.setup()

pins = Pinout.Pins()
pins.set_directions(0, 0, 0)

X = cg.Coil('X-axis', 50000, 30, 1, .5)
X_Cur = X.single_current()

Y = cg.Coil('Y-axis', 50000, 30, 1, .5445)
Y_Cur = Y.single_current()

Z = cg.Coil('Z-axis', 50000, 30, 1, .5)
Z_Cur = Z.single_current()

print("Calculated Currents:")
print("X Current: " + str(X_Cur) + " A")
print("Y Current: " + str(Y_Cur) + " A")
print("Z Current: " + str(Z_Cur) + " A")

DC = dc.DutyCycle(X_Cur, Y_Cur, Z_Cur)
DC.single_calc()

print("Duty Cycles:")
print("X Duty Cycle: " + str(DC.xDutyCycle))
print("Y Duty Cycle: " + str(DC.yDutyCycle))
print("Z Duty Cycle: " + str(DC.zDutyCycle))

PWM = PWM.PWM()
PWM.connectI2C()
PWM.set_frequency(1000)

def manual_test():
    Mag.read()
    Mag.display('G')
    PWM.set_DutyCycles(int(DC.xDutyCycle), int(DC.yDutyCycle), int(DC.zDutyCycle))
    pins.set_directions(DC.dir_x, DC.dir_y, DC.dir_z)
    sleep(5)
    Mag.read()
    Mag.display('G')
    sleep(5)
    PWM.set_DutyCycles(0, 0, 0)
    pins.set_directions(0, 0, 0)

def automatic_test():
    print("Not implemented yet :(")

try:
    print("Manual or Automatic Test? (m/a): ")
    choice = input().lower()
    if choice == 'm':
        manual_test()
    elif choice == 'a':
        automatic_test()
    else: 
        print("Invalid choice. Exiting.")   
except KeyboardInterrupt:
    PWM.set_DutyCycles(0, 0, 0)
    print("Exiting Program")
