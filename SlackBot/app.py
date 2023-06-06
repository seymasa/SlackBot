import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests


app = Flask(__name__)
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

signing_secret = os.environ['SIGNING_SECRET']
bot_token = os.environ['SLACK_BOT_KEY']
channel_name = os.environ['CHANNEL_NAME']

slack_client = WebClient(token=bot_token)
slack_event_adapter = SlackEventAdapter(signing_secret=signing_secret, endpoint='/slack/events', server=app)

BOT_ID = slack_client.auth_test()['user_id']
last_message_ts = None


def send_message(channel, text, user=None):
    try:
        response = slack_client.chat_postMessage(channel=channel, text=text, user=user)
        return response
    except SlackApiError as e:
        return f"Error sending message to Slack: {e.response['error']}"


def gpt_api_request(msg):
    resp = requests.get(f'http://localhost:3002/message/{msg}')
    return resp.json()['message']


@slack_event_adapter.on('message')
def message(payload):
    """
    :param payload: It contains information about the triggered event.
    :return:
    {
       ...
    }
    """
    global last_message_ts
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    message_ts = event.get('ts')

    if user_id != BOT_ID and (last_message_ts is None or message_ts > last_message_ts  ):
        response = gpt_api_request(text)
        response = response + f' -*- {text}'
        send_message(channel_id, response)
        last_message_ts = message_ts


if __name__ == '__main__':
    app.run(debug=True)