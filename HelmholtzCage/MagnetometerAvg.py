from Sensors import Magnetometer2 as Magnetometer
from OutputPipeline import Pinout
import time
import os
import sys

mag = Magnetometer.Magnetometer()
mag.setup()

# Output path for file
out_path = os.path.join(os.getcwd(), 'magnetometer_readings.txt')

numReads = 5 #Magnometer reads X times
if (len(sys.argv) == 2):
    numReads = int(sys.argv[1])
xSum = 0
ySum = 0
zSum = 0

try:
    with open(out_path, 'w') as f:
        for i in range(numReads):
            mag.read()
            f.write("Reading " + str(i+1) + ":\n")
            f.flush() # Ensure data is written to file
            f.write(str(mag.display('G')) + '\n')
            xSum+=mag.Mx
            ySum+=mag.My
            zSum+=mag.Mz
            f.flush() # Ensure data is written to file
            f.write("-----------------------------\n")
            f.flush() # Ensure data is written to file
            time.sleep(1)
    print("Average X B-field:", (xSum * 10000 / numReads))
    print("Average Y B-field:", (ySum * 10000 / numReads))
    print("Average Z B-field:", (zSum * 10000 / numReads))
except KeyboardInterrupt:
    print("Exiting Program")
