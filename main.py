import os
from flask import Flask, Response
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from trello import TrelloClient
import requests
import threading

app = Flask(__name__)

slack_events_adapter = SlackEventAdapter(os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app)

slack_web_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
BOT_ID = slack_web_client.api_call("auth.test")['user_id']
TRELLO_API_KEY = os.environ.get('TRELLO_API_KEY')
TRELLO_API_SECRET = os.environ.get('TRELLO_API_SECRET')
TRELLO_BOARD_NAME = os.environ.get('TRELLO_BOARD_NAME')

trello_client = TrelloClient(
    api_key=TRELLO_API_KEY,
    token=TRELLO_API_SECRET,
)

def get_user_name(user_id):
        slack_users = slack_web_client.users_list()
        user_name = ""
        for user in slack_users["members"]:
            if not user["is_bot"] and "real_name" in user:
                if(user['id']==user_id):
                    user_name = user['real_name']  
        return user_name   
        
def get_channel_name(channel_id):
        slack_channels = slack_web_client.conversations_list(types="private_channel, public_channel")
        channel_name = ""
        for channel in slack_channels['channels']:
            if(channel['id']==channel_id):
                channel_name = channel['name']   
        return channel_name

def get_boards():
        boards = trello_client.list_boards(board_filter="all")
        board = ""
        for board in boards:
            if board.name == TRELLO_BOARD_NAME:
                return board
        return None

def get_first_list(board):
    list_array = []
    lists = board.all_lists()
    for t_list in lists:
        list_array.append(t_list)
    return list_array[0]
        
def fetch_cards(board, slack_handle, comment_text, get_first_list, channel_name):
    result = ""
    comment_with_slack_handle = comment_text + "  ("+slack_handle+")"
    cards = board.all_cards()   
    for card_data in cards:
        if card_data.name == channel_name:
            result = "Found"
            card_data.comment(comment_with_slack_handle )  
            card_data.set_closed(False)
    if result == "":
        url = "https://api.trello.com/1/cards"
        querystring = {"name": channel_name, "idList": get_first_list.id, "key": TRELLO_API_KEY, "token": TRELLO_API_SECRET}
        print(get_first_list.id)
        requests.request("POST", url, params=querystring)
        cards_new = board.all_cards()
        for card_data in cards_new:
            if card_data.name == channel_name:
                print("entro")
                comment_url = "https://api.trello.com/1/cards/{card_data.id}/actions/comments"
                comment_querystring = {"key": TRELLO_API_KEY, "token": TRELLO_API_SECRET, "text": comment_with_slack_handle}
                requests.request("POST", comment_url, params=comment_querystring)   

@slack_events_adapter.on("message")
def receive_message(payload):
    event = payload.get("event", {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    def main_thread():
        if BOT_ID != user_id:
            user_name = get_user_name(user_id)
            channel_name = get_channel_name(channel_id)
            board = get_boards() 
            board_list = get_first_list(board)
            fetch_cards(board,user_name,text,board_list, channel_name)
    thread1 = threading.Thread(target=main_thread)
    thread1.start()
    return Response(status=200)

@slack_events_adapter.on("error")
def error_handler(err):
     print("ERROR: " + str(err))

if __name__ == "__main__":
    app.run()