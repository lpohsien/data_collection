import csv

CSV_FILE = '../data.csv'
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
    'humidity': 'Percentage humidity',
    'gas': 'Gas',
    'Lux': 'Lux'
}

def convert():
    ''' 
    Create plaintext representation of the data row-wise by selecting columns of interest 
    and putting in a key-value pair format
    '''
    with open(CSV_FILE, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        with open(TEXT_FILE, 'w', encoding='utf-8') as text_file:
            for row in csv_reader:
                filtered = [f'{PROPER_NAMES[x]}:{row[x]}' for x in COLUMNS_OF_INTEREST if row[x] != '']
                text_file.write(','.join(filtered)[:-1] + '\n')


convert()
        