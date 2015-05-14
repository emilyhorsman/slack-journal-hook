#!/usr/bin/env python

import time
from os.path import join, getmtime, isfile
from os import listdir

import slack
import slack.chat
import slack.search
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import config

already_sent = []

def message_sent(msg, channel):
    # Check the local cache first
    if channel + msg in already_sent:
        return True
    else:
        already_sent.append(channel + msg)

    query   = "in:{} from:{} {}".format(channel, config.bot_username, msg)
    results = slack.search.messages(query, count=1)
    if not results["ok"]:
        # Couldn't get the results, assume message already sent to avoid
        # duplicates at all costs (really annoying).
        return True

    return results["messages"]["total"] > 0

def send_message(msg, channel=config.default_channel):
    slack.chat.post_message(channel, msg, username=config.bot_username, icon_emoji=config.bot_emoji)

def process_journal_line(line):
    if line.find(config.prompt) != 0:
        return

    msg = line[len(config.prompt):].strip()
    channel = config.default_channel
    if msg.find("#") == 0: # See if a channel has been specified.
        l = msg.split(" ", 1)
        if len(l) == 2:
            channel, msg = l
        else:
            # The channel wasn't actually specified, highlight just included a
            # hashtag.
            msg = l[0]

    if not message_sent(msg, channel):
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
    slack.api_token = config.slack_api_token

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
