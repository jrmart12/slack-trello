# Slack-Trello

This bot will start making it's magic once slack user sends a message to the bot. This will go to a specified Trello board, search
for a card with title that matches the slack user handle; if no matching card is found then the bot will create a new card and add
a comment with the contents of the slack message

## Requirements
- Python 3
- `py-trello`
- `slackclient`
- `Flask`
- `slackeventsapi`
- `ngrok`