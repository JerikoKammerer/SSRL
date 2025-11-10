from Sensors import Magnetometer2 as Magnetometer
from OutputPipeline import Pinout
import time
import os

mag = Magnetometer.Magnetometer()
mag.setup()

numReads = 5 #Magnometer reads X times

try:
    for i in range(numReads):
        mag.read()
        mag.display('G')
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting Program")
