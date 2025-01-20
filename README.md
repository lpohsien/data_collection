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