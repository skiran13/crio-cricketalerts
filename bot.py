import requests as requests
from globals import TOKEN 
import getMatches as match
url = "https://api.telegram.org/bot"+TOKEN

# Function to get the chat id
def get_chat_id(update):
    chat_id = update['message']['chat']['id']
    return chat_id

# Function to get the message text
def get_message_text(update):
    message_text = update["message"]["text"]
    return message_text

# Function to get the last update
def last_update(req):
    response = requests.get(req + "/getUpdates")
    response = response.json()
    result = response["result"]
    total_updates = len(result) - 1
    return result[total_updates]

# Function to reply back to the user
def send_message(chat_id, message_text):
    params = { "chat_id": chat_id, "text": message_text }
    response = requests.post(url + "/sendMessage", data=params)
    return response

# Main function for business logic and reply
def main():
    update_id = last_update(url)["update_id"]
    while True:
        update = last_update(url)
        if update_id == update["update_id"]:
            if get_message_text(update).lower() == "hi" or get_message_text(update).lower() == "hello":
                send_message(get_chat_id(update), 'Hello welcome to CricAlert Bot. Here is the list of Live matches available')
            else:
                send_message(get_chat_id(update),"Sorry cant understand")
            update_id +=1
main()