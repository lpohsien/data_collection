import csv
from datetime import datetime
import argparse
from collections import deque
import os

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
CSV_FILE = os.path.join(ROOT_DIR, 'data.csv')
TEXT_FILE = os.path.join(ROOT_DIR, 'plaintext_data.csv')
TRAIN_FILE = os.path.join(ROOT_DIR, 'train.csv')
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
    if timestamp.endswith('_base'):
        timestamp = timestamp[:-5]
    timestamp = datetime.strptime(timestamp,"%Y%m%d%H%M%S")
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def convertToPlaintext(csv_path=CSV_FILE, text_path=TEXT_FILE, neutral_only=True):
    ''' 
    Create plaintext representation of the data row-wise by selecting columns of interest 
    and putting in a key-value pair format. If neutral_only is set to True, only rows with
    ev = 0.0 will be included in the plaintext file
    '''
    with open(csv_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        curr_image_grp = 0
        with open(text_path, 'w', encoding='utf-8') as text_file:
            for row in csv_reader:

                if "base" in row['timestamp']:
                    curr_image_grp += 1

                if row['ev'] == None: 
                    print(row['image'])
                    assert False

                if neutral_only and float(row['ev']) != 0.0: continue # Skip rows with no data

                filtered = [f'{PROPER_NAMES[x]}:{roundData(row[x], 2)}' for x in COLUMNS_OF_INTEREST if row[x] != '']

                text_file.write(f"{curr_image_grp}>{row['image']}>{','.join(filtered)[:-1]}\n")

def extracImageGroup(input_path=TEXT_FILE, output_path=TRAIN_FILE, num=10):
    ''' 
    Extract the group of image taken from the same scene and perspective. The first image of the group is the on
    suffixed with "_base" for its timestamp entry, while the last image is the one right before the next group. 
    text_path: path to the plaintext file containing all data entries (generated by convertToPlaintext)
    train_path: path to store the extracted image group. This will be used by the dataloader subsequently
    num: number of image groups to extract counting from the back
    '''
    print('Extracting image groups...')
    buffer = deque(iterable=[], maxlen=num) if num >= 0 else deque([]) # Circular buffer
    num_total = 0
    num_extracted = 0
    num_groups = 0
    curr_grp = 0
    
    # Read in `num` many groups of images
    with open(input_path, 'r', encoding='utf-8') as input_file:
        for line in input_file:
            
            num_total += 1
            line = line.strip()
            group, image, caption = line.strip().split('>')

            if group != curr_grp:
                num_groups += 1
                curr_grp = group
                if num != 0:
                    buffer.append([]) # Create anew image group

            # Process the data
            _, image, caption = line.strip().split('>')
            if num != 0:
                buffer[-1].append((image, caption)) # Append to the latest image group



    # Write the extracted image groups to the train file
    for i, group in enumerate(buffer):
        grp_count = 0
        group_output_path = output_path.replace('.csv', f'{i}.csv')
        with open(group_output_path, 'w', encoding='utf-8') as output_file:
            for image, caption in group:
                output_file.write(f'{image}>{caption}\n')
                num_extracted += 1
        print(f'{grp_count} entries extracted to {group_output_path}')

    print(f'Number of image groups extracted: {len(buffer)}/{num_groups}')
    print(f'Number of images extracted: {num_extracted}/{num_total}')
    print('Percentage of images extracted:', num_extracted / num_total * 100)



def getLastRowReadable(file):
    ''' 
    Get the last row of the CSV file and convert it to a key-value pair format
    '''
    with open(file, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        last_row = list(csv_reader)[-1]
        filtered = [f'{PROPER_NAMES[x]} : {roundData(last_row[x], 2)}\n' for x in COLUMNS_OF_INTEREST if last_row[x] != '']
        filtered.append(f'Image : {last_row["image"]}\n')
        filtered.append(f'Timestamp : {readableTimestamp(last_row["timestamp"])}\n')
        filtered.reverse()
        return ''.join(filtered)[:-1]

convertToPlaintext()
extracImageGroup(num=-1)
