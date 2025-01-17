import csv
from datetime import datetime

# CSV_FILE = '../data.csv'
CSV_FILE = '/mnt/USBDRIVE/cp4101_data/data.csv'
TEXT_FILE = 'data.txt'
COLUMNS_OF_INTEREST = ['amb', 'r', 'g', 'b', 'temp', 'pressure', 'co2', 'humidity', 'gas', 'Lux']
PROPER_NAMES = {
    'amb': 'Ambient Light',
    'r': 'Ambient red channel',
    'g': 'Ambient green channel',
    'b': 'Ambient blue channel',
    'temp': 'Temperature',
    'pressure': 'Pressure',
    'co2': 'CO2 Level',
    'humidity': 'Humidity',
    'gas': 'Gas',
    'Lux': 'Lux'
}

def roundData(data, ndigits):
    ''' 
    Round the data in the CSV file to the specified number of digits
    '''
    if data and '.' in data:
        return round(float(data), ndigits)
    return data

def readableTimestamp(timestamp):
    ''' 
    Convert the timestamp to a human-readable format
    '''
    timestamp = datetime.strptime(timestamp,"%Y%m%d%H%M%S")
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def convertToReadable():
    ''' 
    Create plaintext representation of the data row-wise by selecting columns of interest 
    and putting in a key-value pair format
    '''
    with open(CSV_FILE, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        with open(TEXT_FILE, 'w', encoding='utf-8') as text_file:
            for row in csv_reader:
                filtered = [f'{PROPER_NAMES[x]}:{roundData(row[x], 2)}' for x in COLUMNS_OF_INTEREST if row[x] != '']
                text_file.write(','.join(filtered)[:-1] + '\n')

def getLastRowReadable(file):
    ''' 
    Get the last row of the CSV file and convert it to a key-value pair format
    '''
    with open(file, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        last_row = list(csv_reader)[-1]
        filtered = [f'{PROPER_NAMES[x]} : {roundData(last_row[x], 2)}\n' for x in COLUMNS_OF_INTEREST if last_row[x] != '']
        filtered.append(f'Timestamp : {readableTimestamp(last_row["timestamp"])}\n')
        filtered.reverse()
        return ''.join(filtered)[:-1]

# print(getLastRowReadable(CSV_FILE))
convertToReadable()
        