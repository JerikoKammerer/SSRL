from Sensors import Magnetomerer2 as Magnetomerer
from OutputPipeline import Pinout
import time
import os

mag = Magnetomerer.Magnetomerer()
mag.setup()

numReads = 5 #Magnometer reads X times

try:
    for i in range(numReads):
        mag.read()
        mag.display('G')
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting Program")
