import os
import logging
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

app = Flask(__name__)

slack_events_adapter = SlackEventAdapter(os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app)


slack_web_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
BOT_ID = slack_web_client.api_call("auth.test")['user_id']

@slack_events_adapter.on("message")
def receive_message(payload):
    event = payload.get("event", {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if BOT_ID != user_id:
        slack_web_client.chat_postMessage(channel=channel_id, text=text)

if __name__ == "__main__":
    app.run(port=3000)