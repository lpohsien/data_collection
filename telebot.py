import glob
import os
import time
import requests
import json
from data_utils import getLastRowReadable


class TeleBot:

    def __init__(self, 
                 token_file=os.path.join(os.path.dirname(__file__), "secrets.txt"),
                 image_dir="/mnt/USBDRIVE/cp4101_data"):
        self.token_file = token_file
        self.token = None
        self.url = None
        self.offset = 0
        self.image_dir = image_dir

    def getAPIToken(self):
        with open(self.token_file, "r") as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN"):
                    self.token = line.split("=")[1].strip()
                    break
        if not self.token:
            raise ValueError("Token not found")
        self.url = f"https://api.telegram.org/bot{self.token}/"

    def getMe(self):
        url = self.url + "getMe"
        response = requests.get(url)
        return response.json()
        
    def getLastUpdate(self):
        url = self.url + "getUpdates"
        response = requests.get(url)
        return response.json().get("result")[-1]

    def getAllUpdates(self):
        url = self.url + "getUpdates"
        params = {"offset": 0, 
                  "limit": 10, 
                  "timeout": 60, 
                  "allowed_updates": []}
        response = requests.get(url, params=params)
        return response.json()
    
    def popleft(self):
        url = self.url + "getUpdates"
        params = {"offset": self.offset, 
                  "limit": 1, 
                  "timeout": 60, 
                  "allowed_updates": []}
        response = requests.get(url, params=params).json()
        if not response.get("result") or len(response.get("result")) == 0:
            return None
        oldest = response.get("result")[0]
        self.offset = oldest.get("update_id") + 1
        return oldest
    
    def popRight(self):
        url = self.url + "getUpdates"
        params = {"offset": 0, 
                  "limit": 1, 
                  "timeout": 60, 
                  "allowed_updates": []}
        response = requests.get(url, params=params).json()
        if not response.get("result") or len(response.get("result")) == 0:
            return None
        newest = response.get("result")[-1]
        self.offset = newest.get("update_id") + 1
        return newest
    
    @staticmethod
    def unpack(update):
        if not update:
            return None, None
        chat_id = update.get("message").get("chat").get("id")
        text = update.get("message").get("text")
        return chat_id, text
    
    def sendMessage(self, chat_id, text):
        url = self.url + "sendMessage"
        params = {"chat_id": chat_id, 
                  "text": text}
        response = requests.get(url, params=params)
        return response.json().get("ok")    

    def sendLatestPhoto(self, chat_id, photo):
        url = self.url + "sendPhoto"
        params = {"chat_id": chat_id}
        with open(photo, "rb") as f:
            files = {"photo": f}
            response = requests.post(url, params=params, files=files)
        return response.json().get("ok")  

    def sendFile(self, chat_id, file):
        url = self.url + "sendDocument"
        params = {"chat_id": chat_id}
        with open(file, "rb") as f:
            files = {"document": f}
            response = requests.post(url, params=params, files=files)
        return response.json().get  
    
    def getLatestPhoto(self):
        latest_photo = sorted(glob.glob(os.path.join(self.image_dir, "*.jpg")))
        return latest_photo[-1]
    
    def getLatestData(self):
        return getLastRowReadable(os.path.join(self.image_dir, "data.csv"))

    def getCount(self):
        return len(glob.glob(os.path.join(self.image_dir, "*.jpg")))


bot = TeleBot()
bot.getAPIToken()
print(bot.getMe())
while True:
    
    # Input from user
    chat_id, text = bot.unpack(bot.popleft())

    # Response
    if not chat_id:
        time.sleep(1)
        continue
    elif text == "/photo":
        photo = bot.getLatestPhoto()
        print(f"Sending photo: {photo} to {chat_id}")
        res = bot.sendLatestPhoto(chat_id, photo) and \
                bot.sendMessage(chat_id, f"Latest Photo: {photo.split('/')[-1]}")
    elif text == "/data":
        data = bot.getLatestData()
        print(f"Sending data to {chat_id}")
        res = bot.sendMessage(chat_id, f"Latest data:\n{data}")
    elif text == "/count":
        count = bot.getCount()
        print(f"Sending count to {chat_id}")
        res = bot.sendMessage(chat_id, f"Number of photos: {count}")
    else:
        print(f"Received: {text} on {chat_id}")
        res = bot.sendMessage(chat_id, f"Received: {text} on at {time.ctime()}")
        print("----")

    print("Replied" if res else "Failed")
    time.sleep(1)

