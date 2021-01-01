from telegram.ext import Updater,MessageHandler, Filters, CommandHandler,ConversationHandler,RegexHandler
from pycricbuzz import Cricbuzz
import requests
import json
from globals import TOKEN
import availableMatches as match
import logging

# Initializing job queue as None
jobQueue, job, length = None, None, 0

# Logging information enabled
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

# Constants used to define differnt stages of the chatbot
LIVE_LIST,CHOICE = range(2)

# Entry point of the chatbot
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello welcome to CricAlert Bot. Use /live command to list the Live matches available")
    return LIVE_LIST

# Function to get the live matches available
def live(update, context):
    replyText=match.show_current() + "\n Enter your choice"
    context.bot.send_message(chat_id=update.effective_chat.id, text=replyText)
    return CHOICE

# Function to choose a particular match and send updates accordingly
def get_match(update, context):
    matchNumber = int(update.message.text)
    
    # If invalid match is choosen, return and ask to choose again
    if(matchNumber>len(match.matchTitles)):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Enter a correct value!")
        return LIVE_LIST
    
    matchTitle = match.matchTitles[matchNumber-1]
    matchLink = match.matchLinks[matchNumber-1]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Displaying details of match: " + matchTitle)
    return match_updates(matchLink, update, context)
    

# Function used to send updates to the user according to the satus of the match
def match_updates(link, update, context):
    matchID = link.split('/')[2]
    c = Cricbuzz()
    minfo = c.matchinfo(matchID)
    if minfo["mchstate"] == "preview":
        reply = 'Match has not started yet. Match will start at '+ minfo['start_time'] + '\nPlease send a request after the match has started\nSend /live to view other matches'
        update.message.reply_text(reply)
        return LIVE_LIST
    elif minfo['mchstate'] == "complete" or minfo['mchstate'] == "stump" or minfo['mchstate'] == "mom":
        reply = 'Match is over and '+ minfo['status'] 
        update.message.reply_text(reply)
        lscore = c.livescore(matchID)
        reply = 'Final Score: ' + lscore['batting']['score'][0]['runs'] + '/' + lscore['batting']['score'][0]['wickets'] + ' in ' + lscore['batting']['score'][0]['overs'] + ' overs' + '\nSend /live to view other matches'
        update.message.reply_text(reply)
        return LIVE_LIST
    elif minfo['mchstate'] == "toss":
        update.message.reply_text(minfo['toss'])
        reply = 'Match has not started yet. Match will start at '+ minfo['start_time'] + '\nPlease send a request after the match has started\nSend /live to view other matches'
        update.message.reply_text(reply)
        return LIVE_LIST
    else:
        update.message.reply_text(minfo['toss'])
        lscore = c.livescore(matchID)
        reply = 'Current Score: ' + lscore['batting']['score'][0]['runs'] + '/' + lscore['batting']['score'][0]['wickets'] + ' in ' + lscore['batting']['score'][0]['overs'] + ' overs'
        update.message.reply_text(reply)
        global job, jobQueue, length
        data = requests.get('http://mapps.cricbuzz.com/cbzios/match/'+ matchID + '/highlights.json').json()
        length = len(data["comm_lines"])
        job = jobQueue.run_repeating(live_updates, interval=10, first=0, context={"update":update, "matchID":matchID}) # Runs a repeating call to live_updates which checks for events such as boundaries and wickets
        return ConversationHandler.END

# Function to trigger event for boundaries and wickets
def live_updates(bot):
    data = requests.get('http://mapps.cricbuzz.com/cbzios/match/'+ bot.job.context["matchID"] + '/highlights.json').json()
    global length
    if length < len(data["comm_lines"]):
        if data["comm_lines"][0]["evt"] == "wicket":
            reply = "It's a wicket.\nCurrent Score: " + data["comm_lines"][0]["score"] + " in " + data["comm_lines"][0]["o_no"] + " overs."
            bot.job.context["update"].message.reply_text(reply)
        elif data["comm_lines"][0]["evt"] == "four":
            reply = "It's a boundary.\nCurrent Score: " + data["comm_lines"][0]["score"] + " in " + data["comm_lines"][0]["o_no"] + " overs."
            bot.job.context["update"].message.reply_text(reply)
        elif data["comm_lines"][0]["evt"] == "six":
            reply = "It's a Huge Six.\nCurrent Score: " + data["comm_lines"][0]["score"] + " in " + data["comm_lines"][0]["o_no"] + " overs."
            bot.job.context["update"].message.reply_text(reply)
        length+=1


# Function to resond for messages which are out of the scope of the bot
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that.")

# Function to end the conversation
def cancel(update, context):
    user = update.message.from_user
    logging.info("User %s canceled the conversation.", user.first_name)
    global job
    if(job!= None):
        job.schedule_removal()
    update.message.reply_text('Bye! To start again, send /start command.')
    return ConversationHandler.END

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Conversation Handler defines the structure of the message that is given as input to the bot
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LIVE_LIST: [CommandHandler('live', live)],
            CHOICE: [MessageHandler(Filters.regex('^[0-9]+$'), get_match),MessageHandler(Filters.regex('^\D*$'),unknown)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    # Initializing the job queue for recurring updates
    global jobQueue
    jobQueue = updater.job_queue

    # Adding the conversational handler to the dispatcher
    dispatcher.add_handler(conv_handler)
    
    # Command to activate the bot
    updater.start_polling()
    updater.dispatcher.add_handler(CommandHandler('cancel',cancel))
    # Run the bot until Ctrl+C is pressed
    updater.idle()

main()