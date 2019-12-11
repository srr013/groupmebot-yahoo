import os
import json
from flask import Flask, request, session, render_template
import logging
import GroupMe_Bot
import message as m
import fantasy as f
from helpers.secrets import secrets
import db
import groupme

app = Flask(__name__)
app.secret_key = secrets["secret_key"]

def initialize_group(group_id, groupme_bot = None):
	if not groupme_bot:
		groupme_bot = GroupMe_Bot.GroupMe_Bot()
	#logging.warn("initializing: %i"% (group_id))
	bot_id = ''
	if request.args.get("bot_id"):
		bot_id = request.args['bot_id']
	group_data = groupme_bot.get_group_data(group_id, bot_id)
	# if transaction_list:
	# 	s = "Recent transactions: \n"
	# 	for t in transaction_list:
	# 		s += t 
	# 	m.reply(s, bot_id)
	return group_data


# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['GET','POST'])
def webhook():
	groupme_bot = GroupMe_Bot.GroupMe_Bot()
	if request.method == 'GET':
		return display_status(groupme_bot=groupme_bot)
	elif request.method == 'POST' and groupme_bot.monitoring_status:
		message = request.get_json()
		logging.warn(message)
		group_data = initialize_group(message['group_id'], groupme_bot=groupme_bot)
		if int(group_data['status']) > 0:
			groupme_bot.increment_message_num(group_data['index'])
			if group_data['message_num'] >= group_data['message_limit'] and not m.sender_is_bot(message):
				logging.warning("message: "+ message['text']+", "+
					str(group_data['message_num']+1)+" / "+str(group_data['message_limit'])+
					"message_full: " +str(json.dumps(message))+", Chat: "+group_data['bot_id'])
				groupme_bot.reset_message_data(group_data['index'])
				m.reply_with_mention(m.get_message(message['name']),
				message['name'], message['sender_id'], group_data['bot_id'])
			#f.post_trans_list(groupme_bot, group_data, group_data['bot_id'])
			return "ok", 200
	return "not found", 404

def display_status(groupme_bot=None):
	if not groupme_bot:
		groupme_bot = GroupMe_Bot.GroupMe_Bot()
	data = groupme_bot.display_status()
	return render_template("index.html", groupme_groups=data['group_data'],	groupme_headers=data['headers'], global_data=data['global_data'])

@app.route('/create_group/<int:groupme_id>')
def create_group(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot()
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	return display_status(groupme_bot=groupme_bot)

@app.route('/toggle/<int:groupme_id>')
def toggle_status(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot()
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	s = 0
	if not group_data['status']:
		s = 1
	query = 'UPDATE groupme_yahoo SET status='+str(s)+' WHERE groupme_group_id='+str(groupme_id)+';'
	db.execute_table_action(query)
	return display_status(groupme_bot=groupme_bot)

@app.route('/transactions/<int:groupme_id>')
def transactions(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot()
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	if group_data['status'] > 0:
		return (groupme_bot.post_trans_list(group_data), 200)
	else:
		return (display_status(groupme_bot=groupme_bot), 200)

@app.route('/checkTriggers/<int:groupme_id>')
def check_triggers(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot()
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	if request.values:
		groupme_bot.create_trigger()
	if groupme_bot.check_triggers(group_data):
		return "Trigger found", 200
	return "No trigger found", 404

# @app.route('/name-changes/*')
# def name_changes():	
# 	groupme_bot, group_data = initialize_group(group_id)
# 	return (groupme.update_group_membership(group_data))

# @app.errorhandler(404)
# def not_found(error):
#     return render_template('error.html'), 404