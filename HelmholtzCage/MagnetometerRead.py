from Sensors import Magnetometer2 as Magnetometer
from OutputPipeline import Pinout
import time
import os

mag = Magnetometer.Magnetometer()
mag.setup()

# Output path for file
out_path = os.path.join(os.getcwd(), 'magnetometer_readings.txt')

numReads = 5 #Magnometer reads X times

try:
    with open(out_path, 'w') as f:
        for i in range(numReads):
            mag.read()
            f.write("Reading " + str(i+1) + ":\n")
            f.flush() # Ensure data is written to file
            f.write(str(mag.display('G')) + '\n')
            f.flush() # Ensure data is written to file
            f.write("-----------------------------\n")
            f.flush() # Ensure data is written to file
            time.sleep(1)
except KeyboardInterrupt:
    print("Exiting Program")
