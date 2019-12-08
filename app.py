import os
import json
from flask import Flask, request, session
import logging
import GroupMe_Bot
import message as m
import fantasy as f
from helpers.secrets import secrets
import db
import groupme

app = Flask(__name__)
app.secret_key = secrets["secret_key"]

def initialize_group(group_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot()
	logging.warn("initializing: ", group_id)
	group_data = groupme_bot.get_group_data(group_id)
	# if transaction_list:
	# 	s = "Recent transactions: \n"
	# 	for t in transaction_list:
	# 		s += t 
	# 	m.reply(s, bot_id)
	return groupme_bot, group_data


# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['GET','POST'])
def webhook():
	if request.method == 'GET':
		return display_status()
	else:
		message = request.get_json()
		logging.warn(message)
		groupme_bot, group_data = initialize_group(message['group_id'])
		if int(group_data['status']) > 0:
			groupme_bot.increment_message_num(group_data['id'])
			if group_data['message_num'] >= group_data['message_limit'] and not m.sender_is_bot(message):
				logging.warning("message: "+ message['text']+", "+
					str(group_data['message_num'])+" / "+str(group_data['message_limit'])+
					"message_full: " +str(json.dumps(message))+", Chat: "+bot_id)
				groupme_bot.reset_message_data(group_data['id'])
				m.reply_with_mention(m.get_message(message['name']),
				message['name'], message['sender_id'], bot_id)
			#f.post_trans_list(groupme_bot, group_data, bot_id)
			return "ok", 200
	return "not found", 404

def display_status():
	groupme_bot = GroupMe_Bot.GroupMe_Bot()
	return groupme_bot.display_status()

@app.route('/toggle/<int:groupme_id>')
def toggle_status(groupme_id):
	groupme_bot, group_data = initialize_group(groupme_id)
	s = 0
	if not group_data['status']:
		s = 1
	query = 'UPDATE groupme_yahoo SET status='+str(s)+' WHERE groupme_group_id='+str(groupme_id)+';'
	db.execute_table_action(query)
	return display_status()

# @app.route('/refresh')
# def refresh():
# 	transaction_list = groupme_bot.get_transactions_list()
# 	# if transaction_list:
# 	# 	m.reply(format_transaction_list(transaction_list))
# 	return "ok", 200

# @app.route('/swap')
# def swap_bots():
# 	group_data = initialize_group(group_id)
# 	s = 0
# 	status = 'Test'
# 	if not group_data['bot_status']:
# 		s = 1
# 		status = 'PRD'
# 	query = 'UPDATE groupme_yahoo SET bot_status='+str(s)+' WHERE session=1;'
# 	db.execute_table_action(query)
# 	active_status = "Active" if group_data['status'] > 0 else "Inactive"
# 	return json.dumps("Bot is currently "+ active_status +" and in chat "+status)

@app.route('/transactions/<int:groupme_id>')
def transactions(groupme_id):
	groupme_bot, group_data = initialize_group(groupme_id)
	if group_data['status'] > 0:
		return (f.post_trans_list(groupme_bot, group_data), 200)
	else:
		return (display_status(), 200)

# @app.route('/name-changes/*')
# def name_changes():	
# 	groupme_bot, group_data = initialize_group(group_id)
# 	return (groupme.update_group_membership(group_data))

# @app.errorhandler(404)
# def not_found(error):
#     return render_template('error.html'), 404