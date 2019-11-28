import os
import json
from flask import Flask, request, session
import logging
import League_Bot
import message as m
from helpers.secrets import secrets
import db

app = Flask(__name__)
app.secret_key = secrets["secret_key"]
test_bot_id = "566e3b05b73cb551006cf34410"
prd_bot_id = "70e9ad5bc50020fdb3a14dbca1"
league_bot = None
bot_id = ''

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
	global league_bot, bot_id
	message_data = initialize()
	league_bot.increment_message_num()
	logging.warning("message: "+ message['text']+", "+
	str(message_data['message_num'])+" / "+str(message_data['message_limit'])+
					"message_full: " +str(json.dumps(message)))
	if message_data['message_num'] >= message_data['message_limit'] and not m.sender_is_bot(message):
		league_bot.reset_message_data()
		m.reply_with_mention(m.get_message(message['name']),
		message['name'], message['sender_id'], bot_id)
	return "ok", 200

def initialize():
	global league_bot
	if not league_bot:
		league_bot = League_Bot.League_Bot(1)
	message_data = league_bot.initialize_bot()
	# if transaction_list:
	# 	s = "Recent transactions: \n"
	# 	for t in transaction_list:
	# 		s += t 
	# 	m.reply(s, bot_id)
	return message_data

@app.route('/initialize')
def initialize_to_window():
	logging.debug("initializing")
	message_data = initialize()
	return json.dumps(message_data)

@app.route('/toggle')
def toggle_status():
	message_data = initialize()
	s = 0
	if not message_data['status']:
		s = 1
	query = 'UPDATE groupme_yahoo SET status='+s+' WHERE session=1'
	db.execute_table_action(query)
	return json.dumps(message_data)

@app.route('/toggle')
def swap_bots():
	message_data = initialize()
	s = 0
	if not message_data['bot_status']:
		s = 1
	query = 'UPDATE groupme_yahoo SET bot_status='+s+' WHERE session=1'
	db.execute_table_action(query)
	get_bot_status(message_data['bot_status'])
	return json.dumps(message_data)

@app.route('/transactions')
def transactions():
	global league_bot, bot_id
	if not league_bot:
		league_bot = League_Bot.League_Bot(1)
	message_data = initialize()
	data = league_bot.get_league_data()
	trans_list = league_bot.get_transactions_list(data, message_data['transaction_num'])
	s='None'
	if trans_list:
		s = "Recent transactions: \n"
		for t in trans_list:
			s += t 
		m.reply(s, bot_id)
	return s

@app.route('/')
def home():
	return 'Hello'

def get_bot_status(message_bot_status):
	global test_bot_id, prd_bot_id, bot_id
	if message_bot_status > 0:
		bot_id = prd_bot_id
	else:
		bot_id = test_bot_id
		




