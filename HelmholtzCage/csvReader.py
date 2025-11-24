import csv

mag490m1s = [] # List to store magnitude values at 490m for 1s steps
mag520m1s = [] # List to store magnitude values at 520m for 1s steps
mag490mhalfs = [] # List to store magnitude values at 490m for 0.5s steps
mag520mhalfs = [] # List to store magnitude values at 520m for 0.5s steps

# converts curly braces B-field entries into floats
def filterForXYZ(entry):
    components = entry.split()
    components[3] = components[3].replace('}', '')
    return [float(components[1]),
            float(components[2]),
            float(components[3])]

# this is intended to read in the CSV file and populate the lists above
# it is only tested to work with the specific MagArrayVals.csv file structure
def readMagData():
    with open('MagArrayVals.csv', mode='r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)  # Skip the header row

        for row in csv_reader:
            while (not row[0].startswith("{")):
                row.pop(0) # Remove non-data entries
            if (len(row) > 0):
                mag490m1s.append(filterForXYZ(row[0]))
            if (len(row) > 1):
                mag520m1s.append(filterForXYZ(row[1]))
            if (len(row) > 3):
                mag490mhalfs.append(filterForXYZ(row[2]))
            if (len(row) > 3):
                mag520mhalfs.append(filterForXYZ(row[3]))
        
readMagData()
print(mag490m1s[0], mag520m1s[0], mag490mhalfs[0], mag520mhalfs[0])