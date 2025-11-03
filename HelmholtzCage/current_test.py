from InputPipeline import currentGenerator as cg
from OutputPipeline import PWM

X = cg.Coil('X-axis', 1, 30, 1, .5)
X_Cur = X.single_current()

Y = cg.Coil('Y-axis', 1, 30, 1, .5445)
Y_Cur = Y.single_current()

Z = cg.Coil('Z-axis', 1, 30, 1, .5)
Z_Cur = Z.single_current()

print("Calculated Currents:")
print("X Current: " + str(X_Cur) + " A")
print("Y Current: " + str(Y_Cur) + " A")
print("Z Current: " + str(Z_Cur) + " A")

X_DC = 7.5/65535 * abs(X_Cur)
Y_DC = 7.5/65535 * abs(Y_Cur)
Z_DC = 7.5/65535 * abs(Z_Cur)

print("Duty Cycles:")
print("X Duty Cycle: " + str(X_DC))
print("Y Duty Cycle: " + str(Y_DC))
print("Z Duty Cycle: " + str(Z_DC))

PWM = PWM.PWM()
PWM.connectI2C()
PWM.set_frequency(1000)

try:
    DC = PWM.set_DutyCycles(int(X_DC), int(Y_DC), int(Z_DC))
except KeyboardInterrupt:
    PWM.set_DutyCycles(0, 0, 0)
    print("Exiting Program")
