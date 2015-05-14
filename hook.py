import slack
import slack.chat
import slack.search
import redis

import config

class Hook:

    def __init__(self, redis_client=None):
        if redis_client:
            self.r = redis_client
        else:
            self.r = redis.from_url(config.redis_url)

    def d(self, s):
        if config.debug:
            print s
        return config.debug

    def archive_key(self, channel):
        return "{}:archive:{}".format(config.redis_prefix, channel)

    def is_archived(self, msg, channel):
        return self.r.sismember(self.archive_key(channel), msg)

    def archive(self, msg, channel):
        self.r.sadd(self.archive_key(channel), msg)

    def strip_unicode(self, s):
        return "".join([ c if ord(c) < 128 else " " for c in s ])

    def message_already_handled(self, msg, channel):
        if self.is_archived(msg, channel):
            self.d("Already handled: ({}) {}".format(channel, msg))
            return True
        else:
            self.archive(msg, channel)

        # The Slack Web API can't seem to handle searching Unicode. Even
        # searching for a unicode character in the browser doesn't work. So,
        # hacky solution: replace unicode characters with spaces. Search for
        # this modified message, check match against original message to be
        # sure.

        query   = "in:{} from:{} {}".format(channel, config.bot_username, self.strip_unicode(msg))
        results = slack.search.messages(query, count=1)
        if not results["ok"]:
            # Couldn't get the results, assume message already sent to avoid
            # duplicates at all costs (really annoying).
            self.d("Already in Slack {}: {}".format(channel, msg))
            return True

        if results["messages"]["total"] > 0:
            return results["messages"]["matches"][0]["text"] == msg.decode("utf-8")

        return False

    def send_message(self, msg, channel=config.default_channel):
        if not self.d("Posting message into {}: {}".format(channel, msg)):
            slack.chat.post_message(channel, msg, username=config.bot_username, icon_emoji=config.bot_emoji)

    def process(self, line):
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

        self.d(msg)
        if not self.message_already_handled(msg, channel):
            self.send_message(msg, channel)

slack.api_token = config.slack_api_token
