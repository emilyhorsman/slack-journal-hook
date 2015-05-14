#!/usr/bin/env python

from os.path import isfile
from hashlib import sha256
import hmac
import threading
import json

from flask import Flask, request, abort
from dropbox.client import DropboxClient, DropboxOAuth2FlowNoRedirect
import redis

import config
from hook import Hook

def prefix(s):
    return "{}:dropbox:{}".format(config.redis_prefix, s)

def process_user(uid):
    access_token = r.hget(prefix("access_tokens"), uid)
    cursor = r.hget(prefix("cursors"), uid)
    client = DropboxClient(access_token)
    result = client.delta(cursor, path_prefix=config.dropbox_entry_path)
    has_more = True

    while has_more:
        for path, metadata in result["entries"]:
            if metadata is None or metadata["is_dir"] or not path.endswith(".txt"):
                continue

            with client.get_file(path) as f:
                for line in f:
                    h.process(line)

        cursor = result["cursor"]
        has_more = result["has_more"]

    r.hset(prefix("cursors"), uid, cursor)

app = Flask(__name__)

@app.route("/webhook", methods=["GET"])
def verify():
    return request.args.get("challenge")

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Dropbox-Signature")
    if signature != hmac.new(config.dropbox_app_secret, request.data, sha256).hexdigest():
        abort(403)

    for uid in json.loads(request.data)["delta"]["users"]:
        threading.Thread(target=process_user, args=(uid,)).start()
    return ""

if __name__ == "__main__":
    cursor = None
    r = redis.from_url(config.redis_url)
    h = Hook(r)

    if r.hlen(prefix("access_tokens")) == 0:
        flow = DropboxOAuth2FlowNoRedirect(config.dropbox_app_key, config.dropbox_app_secret)
        authorize_url = flow.start()
        print "1. Go to: " + authorize_url
        print "2. Click 'Allow' (you might have to log in first)"
        print "3. Copy the authorization code."
        code = raw_input("Enter the authorization code here: ").strip()
        access_token, user_id = flow.finish(code)
        r.hset(prefix("access_tokens"), user_id, access_token)

    app.debug = config.debug
    app.run(host=config.flask_host, port=config.flask_port, debug=config.debug)
