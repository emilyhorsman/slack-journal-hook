#!/usr/bin/env python

import time
from os.path import join, getmtime, isfile
from os import listdir

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import config
import hook

def process(path):
    with open(path, "r") as f:
        for line in f: hook.process(line)

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
