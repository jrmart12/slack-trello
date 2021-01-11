import os
import logging
from flask import Flask, request, Response
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from trello import Board, Card, TrelloClient, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from time import sleep
import requests
import traceback

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
        slack_channels = slack_web_client.conversations_list()
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
    cards = board.all_cards()   
    for card_data in cards:
        if card_data.name == channel_name:
            result = "Found"
            card_data.comment(comment_text )  
            card_data.set_closed(False)
    if result == "":
        url = f"https://api.trello.com/1/cards"
        querystring = {"name": channel_name, "idList": get_first_list.id, "key": TRELLO_API_KEY, "token": TRELLO_API_SECRET}
        requests.request("POST", url, params=querystring)
        comment_url = "https://api.trello.com/1/cards/{id}/actions/comments"
        comment_querystring = {"key": TRELLO_API_KEY, "token": TRELLO_API_SECRET, "text": comment_text}
        requests.request("POST", comment_url, params=comment_querystring)   

@slack_events_adapter.on("message")
def receive_message(payload):
    event = payload.get("event", {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if BOT_ID != user_id:
        user_name = get_user_name(user_id)
        print(user_name)
        channel_name = get_channel_name(channel_id)
        print(channel_name)
        board = get_boards() 
        print(board.name)
        print(board.id)
        board_list = get_first_list(board)
        fetch_cards(board,user_name,text,board_list, channel_name)
        print("ready")
        return Response(status=200)
    else:
         return 

@slack_events_adapter.on("error")
def error_handler(err):
     print("ERROR: " + str(err))

if __name__ == "__main__":
    app.run()