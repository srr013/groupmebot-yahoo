import os
import json
from flask import Flask, request, session
import logging
import League_Bot
import message as m
from helpers.secrets import secrets

app = Flask(__name__)
app.secret_key = secrets["secret_key"]
bot_id = "566e3b05b73cb551006cf34410"#"70e9ad5bc50020fdb3a14dbca1"#
#566 - test chat
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
	message = request.get_json()
	global league_bot
	data, transaction_list, message_data = initialize()
	league_bot.increment_message_num()
	logging.warning("message: "+ message['text']+", "+str(message_data['message_num'])+" / "+str(message_data['message_limit']))
	if message_data['message_num'] >= message_data['message_limit'] and not m.sender_is_bot(message):
		league_bot.reset_message_data()
		m.reply(m.get_message(message['name']), bot_id)
	return "ok", 200

def initialize():
	global league_bot
	if not league_bot:
		league_bot = League_Bot.League_Bot(1)
	data, transaction_list, message_data = league_bot.initialize_bot()
	if transaction_list:
		s = "Today's transactions: \n"
		for t in transaction_list:
			s += t 
		m.reply(s, bot_id)
	return data, transaction_list, message_data

@app.route('/initialize')
def initialize_to_window():
	logging.debug("initializing")
	data, transaction_list, message_data = initialize()
	return json.dumps(data)


@app.route('/')
def home():
	return 'Hello'



