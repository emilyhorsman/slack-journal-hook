#!/usr/bin/env python

import json
import time
from hashlib import md5
from os.path import join, getmtime, isfile
from os import listdir

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import config

def log_string(msg, channel):
    return md5(channel + msg).digest()

def log_message(msg, channel):
    with open(config.archive_path, "a") as f:
        f.write(log_string(msg, channel) + "\n")

def in_log(msg, channel):
    if not isfile(config.archive_path):
        return False

    t = log_string(msg, channel)
    with open(config.archive_path, "r") as f:
        for line in f:
            if line.strip() == t:
                return True

    return False

def send_message(msg, channel=config.default_channel):
    payload = {
        "text": msg,
        "channel": channel,
        "icon_emoji": config.bot_emoji,
        "username": config.bot_username
        }
    r = requests.post(config.webhook_url, data=json.dumps(payload))

def process_journal_line(line):
    if line.find(config.prompt) != 0:
        return

    msg = line[len(config.prompt):].strip()
    channel = config.default_channel
    if msg.find("#") == 0: # See if a channel has been specified.
        channel, msg = msg.split(" ", 1)

    if not in_log(msg, channel):
        log_message(msg, channel)
        send_message(msg, channel)

def process(path):
    with open(path, "r") as f:
        for line in f: process_journal_line(line)

class JournalHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            # FSEvents in OS X only returns the directory when a file is
            # modified, so get the most recently modified folder.
            files = [ join(event.src_path, f) for f in listdir(event.src_path) ]
            modified = max(files, key=getmtime)
            process(modified)

if __name__ == "__main__":
    event_handler = JournalHandler()
    observer = Observer()
    observer.schedule(event_handler, config.journal_entry_path)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
