import slack
import slack.chat
import slack.search
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

def process(line):
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

slack.api_token = config.slack_api_token
