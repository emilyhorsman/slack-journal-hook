#### Purpose

I've been keeping a journal of text-based entries in a Dropbox folder ever since moving away from Day One. I had been wanting a way to note key things in each entry so that I could review them later. Initially, I wrote a script to go through the entries and print out highlights from the last few days. Highlights were any line in the journal starting with a `Highlight: ` prompt. Remembering to run the script and read through everything was a pain though. I stumbled across the idea of using a personal Slack team as a stream of consciousness/knowledge archive and organizer.

#### dropboxdriver.py

This driver uses the Dropbox API to monitor changes in a journal folder.

#### watchdogdriver.py

This driver uses the Python module [watchdog](https://pypi.python.org/pypi/watchdog) to monitor changes in a local journal folder.

#### Journal Usage

```
Highlight: This highlight goes to the default channel specified in config.py.
Highlight: #random This highlight goes to the #random channel.
```
