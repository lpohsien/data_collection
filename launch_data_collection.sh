#!/bin/bash
sudo mount /dev/lithium1 /mnt/USBDRIVE/ -o umask=000
echo 'Launching MQTT Broker and Subscriber'
tmux new-session -d -s sub
tmux split-window -vb             # Split vertically for Pane 2
tmux split-window -h -t 0         # Split horizontally Pane 0 to create Pane 1
tmux select-pane -t 1
tmux split-window -vb             # Split Pane 1 vertically to create Pane 3
tmux send-keys -t 0 'mosquitto -v -c /etc/mosquitto/user-pw.conf' C-m
tmux send-keys -t 1 'mosquitto_sub -h 192.168.0.117 -p 1883 -u cloud -P 3 -t feedback/#' C-m
tmux send-keys -t 2 'python3 /mnt/USBDRIVE/data_collection/telebot.py' C-m
tmux send-keys -t 3 'source ~/data_collection_env/bin/activate && python3 /mnt/USBDRIVE/data_collection/server.py' C-m
tmux attach


#tmux new-session -d -s sub \
#  split-window -v \
#  send-keys 'python3 subscriber.py' C-m \
#  select-pane -D \
#  send-keys 'mosquitto -v -c /etc/mosquitto/user-pw.conf' C-m \
#  attach

