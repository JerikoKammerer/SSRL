"""Read H-bridge fault flags (FF1, FF2) for each axis."""

import digitalio
import board

pins = {
    "X": {"FF1": board.D21, "FF2": board.D20},
    "Y": {"FF1": board.D25, "FF2": board.D24},
    "Z": {"FF1": board.D27, "FF2": board.D18},
}

for axis, gpio in pins.items():
    ff1 = digitalio.DigitalInOut(gpio["FF1"])
    ff1.direction = digitalio.Direction.INPUT

    ff2 = digitalio.DigitalInOut(gpio["FF2"])
    ff2.direction = digitalio.Direction.INPUT

    print(f"{axis}-axis:  FF1 = {ff1.value}  FF2 = {ff2.value}")

    ff1.deinit()
    ff2.deinit()
