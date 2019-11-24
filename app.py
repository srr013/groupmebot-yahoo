# RESOURCE: http://www.apnorton.com/blog/2017/02/28/How-I-wrote-a-Groupme-Chatbot-in-24-hours/


# IMPORTS
import os
import json

from flask import Flask, request
import logging
import random
import League_Bot
import message as m

app = Flask(__name__)
bot_id = "70e9ad5bc50020fdb3a14dbca1"#"566e3b05b73cb551006cf34410"#
league_bot = None

@app.route('/refresh')
def refresh():
	transaction_list = league_bot.get_transactions()
	# if transaction_list:
	# 	m.reply(format_transaction_list(transaction_list))
	return "ok", 200

# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group


@app.route('/', methods=['POST'])
def webhook():
	# 'message' is an object that represents a single GroupMe message.
	message = request.get_json()
	global league_bot
	if not league_bot:
		league_bot = League_Bot.League_Bot()
		league_bot.init()
	league_bot.message_num  += 1
	print(league_bot.message_num, league_bot.message_limit)
	logging.debug("message: "+ message['text']+", "+str(league_bot.message_num)+" / "+str(league_bot.message_limit))
	if league_bot.message_num >= league_bot.message_limit and not m.sender_is_bot(message):
		league_bot.message_num = 0
		league_bot.message_limit = random.randint(15,30)
		m.reply(m.get_message(message['name']))
	return "ok", 200

@app.route('/initialize')
def iniitialize():
	logging.debug("initializing")
	global league_bot
	league_bot.init()


@app.route('/')
def home():
	return 'Hello'

@app.route('/data')
def show_data():
	global league_bot
	return json.dumps(league_bot.data)


