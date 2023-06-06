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
client_msg_ids = set()


def send_message(channel, text, user=None):
    try:
        response = slack_client.chat_postMessage(channel=channel, text=text, user=user)
        return response
    except SlackApiError as e:
        return f"Error sending message to Slack: {e.response['error']}"


def gpt_api_request(msg):
    resp = requests.get(f'http://localhost:3002/message/{msg}')
    return resp.json()['message']

'''
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

    if user_id != BOT_ID and (last_message_ts is None or message_ts > last_message_ts):
        response = gpt_api_request(text)
        response = response + f' -*- {text}'
        #send_message(channel_id, response)
        print(response)
        last_message_ts = message_ts'''


def converter(txt):
    return int(txt.replace('.', ''))


@slack_event_adapter.on('message')
def message(payload):
    '''

    {'token': '3ww4aS4X8Fw2qxvL25Havyl4', 'team_id': 'T05AV2JHQ4V', 'context_team_id': 'T05AV2JHQ4V', 'context_enterprise_id': None, 'api_app_id': 'A05AY2KGKJN', 'event': {'client_msg_id': '46b863a2-b5cc-4a25-ab7f-ef5237c00b87', 'type': 'message', 'text': 'who does şeyma sarıgil hate in this company?', 'user': 'U05BAKT7KKK', 'ts': '1686040749.902439', 'blocks': [{'type': 'rich_text', 'block_id': 'RWJ9b', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'text', 'text': 'who does şeyma sarıgil hate in this company?'}]}]}], 'team': 'T05AV2JHQ4V', 'channel': 'C05ARK2JQ3G', 'event_ts': '1686040749.902439', 'channel_type': 'channel'}, 'type': 'event_callback', 'event_id': 'Ev05B22FU5EH', 'event_time': 1686040749, 'authorizations': [{'enterprise_id': None, 'team_id': 'T05AV2JHQ4V', 'user_id': 'U05AY1RGYTD', 'is_bot': True, 'is_enterprise_install': False}], 'is_ext_shared_channel': False, 'event_context': '4-eyJldCI6Im1lc3NhZ2UiLCJ0aWQiOiJUMDVBVjJKSFE0ViIsImFpZCI6IkEwNUFZMktHS0pOIiwiY2lkIjoiQzA1QVJLMkpRM0cifQ'}

    :param payload:
    :return:
    '''

    global last_message_ts
    global client_msg_ids

    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    client_msg_id = event.get('client_msg_id')
    message_ts = converter(event.get('ts'))
    bot_check = bool(event.get('is_bot'))

    if user_id != BOT_ID and not bot_check:
        if last_message_ts is None or float(message_ts) > float(last_message_ts):
            if client_msg_id in client_msg_ids:
                return '', 200
            client_msg_ids.add(client_msg_id)
            response = gpt_api_request(text)
            response = response + f' -*- {text}'

            send_message(channel_id, response)
            last_message_ts = float(message_ts)

    return '', 200


if __name__ == '__main__':
    app.run(debug=True)
