# data_collection

# Set-up on Raspberry Pi 4b (OS version: Raspbian GNU/Linux Bookworm)
1. Create virtual environment using `python -m venv --system-site-packages data_collection_env` and activate it
2. Install required packages using `pip install -r requirements.txt`
3. (Optional) To allow live update of the data collection process via Telegram, create a bot using BotFather and obtain the token. Create a file named `secrets.txt` in project root directory and add the following line: `TELEGRAM_BOT_TOKEN=__YOUR_TELEGRAM_BOT_TOKEN__`, replacing `__YOUR_TELEGRAM_BOT_TOKEN__` with the actual token obtained from BotFather.  
4. Run `launch_data_collection.sh` to start data collection

# Framework
The [launch script](launch_data_collection.sh) will launch the following processes:
0. (Optional) Mount external storage device for storing the images and data
1. MQTT broker which listens to incoming messages from the sensors provided by ESP32 and ESP32CAM if any
2. MQTT Subscriber which listens to `feedback/#` topic and logs the feedback messages
3. Telegram bot which listens to incoming messages from Telegram and provide current updates on the data collection process (see [telebot](telebot.py) for more details)
4. [server.py](server.py) which is the main driver for data collection process. It listens to incoming messages from the sensors (via MQTT for ESP32 and via BLE for NICLA Sense ME) at regular intervals and combined together. A delay tolerance of 600s is set by default, such that whenever the interval between two consecutive messages exceeds 600s, the older message from other devices will be discarded. The writing of the records will only be triggered when capturing image using RPi Camera. The structure of the combined sensor data as well as the address output csv file is specified in [dataset.py](dataset.py) depending on the actual set-up of the sensor and storage requirements. 

Note that the telegram bot expect the following directory structure:
```
data
|- data.csv
|- images
    |- image1.jpg
    |- image2.jpg
    |- ...
```

# Data processing

Note that since we might want to differentiate images taken from a different angle, the first timestamp for that camera angle in the `data.csv` can be appended with the `_base` suffix for later preprocessing to differentiate them into different image groups.

The main data post-processing code is specified in [data_utils.py](/data_utils.py). The `convertToPlaintextWithAugmentation` function converts the csv data in `data.csv` to plaintext image-sensor pairs, along with its image and write it to the file as specified by `TEXT_PATH`. Specific image groups can be extracted from the plaintext dile using the `extracImageGroup` function. Each group of image-sensor data corresponding to different camera angle will be saved to its respective csv file (note that in this file, the image and sensor data are `>` separated instead of comma separated).

The `create_train_test_split` function is originally designed to create splits from all the chosen image groups. However, to prevent leakage of information, it might be more sensible to split by image groups (i.e. choosing specific image group as the validation set instead of mixing all the groups and sampling from the mix). With such an approach, the only use of the  `create_train_test_split` function is to help collate the entries from different image groups and convert them back into csv format (the train test split ratio should be set to 0 or 1, with the splits being created manually by running the functions on two different set of image groups). 

To integrate better with the image embedding precomputation and training as specified in [sensor encoder training](https://github.com/lpohsien/CLIP/), the `data` directory should be symlinked to the `collected_data` directory in that repository.