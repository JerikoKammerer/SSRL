from InputPipeline import currentGenerator as cg
from OutputPipeline import DutyCycle
from OutputPipeline import PWM

X = cg.Coil('X-axis', 3, 30, 1, .5)
X.single_current()

Y = cg.Coil('Y-axis', 4, 30, 1, .5445)
Y.single_current()

Z = cg.Coil('Z-axis', 5, 30, 1, .5)
Z.single_current()

