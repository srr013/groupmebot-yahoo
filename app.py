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
		groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	#logging.warn("initializing: %i"% (group_id))
	bot_id = ''
	if request.args.get("bot_id"):
		bot_id = request.args['bot_id']
	group_data = groupme_bot.get_group_data(group_id, bot_id)
	if not group_data:
		logging.warn("Group data not found for group %s"%group_id)
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
	groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	if request.method == 'GET':
		return display_status(groupme_bot=groupme_bot)
	elif request.method == 'POST' and groupme_bot.monitoring_status:
		message = request.get_json()
		logging.warn(message)
		groupme_bot.save_message(message)
		if not m.sender_is_bot(message):
			group_data = initialize_group(message['group_id'], groupme_bot=groupme_bot)
			groupme_bot.check_messages(group_data)
			active_triggers = groupme_bot.check_triggers(group_data)
			if active_triggers:
				groupme_bot.send_trigger_messages(group_data, active_triggers)
			elif int(group_data['status']) > 0:
				groupme_bot.increment_message_num(group_data['index'])
				if group_data['message_num'] >= group_data['message_limit']:
					logging.warning("message: "+ message['text']+", "+
						str(group_data['message_num']+1)+" / "+str(group_data['message_limit'])+
						"message_full: " +str(json.dumps(message))+", Chat: "+group_data['bot_id'])
					groupme_bot.reset_message_data(group_data['index'])
					m.reply_with_mention(m.get_message(message['name']),
					message['name'], message['sender_id'], group_data['bot_id'])
				#f.post_trans_list(groupme_bot, group_data, group_data['bot_id'])
				return "ok", 200
			return "ok", 200
	return "not found", 404

def display_status(groupme_bot=None):
	if not groupme_bot:
		groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	data = groupme_bot.display_status()
	key = app.config.from_envvar('CONSUMER_KEY')
	secret = app.config.from_envvar('CONSUMER_SECRET')
	logging.warn(config)
	return render_template("index.html", groupme_groups=data['group_data'],	groupme_headers=data['headers'], global_data=data['global_data'])

@app.route('/create_group/<int:groupme_id>')
def create_group(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	return display_status(groupme_bot=groupme_bot)

@app.route('/toggle/<int:groupme_id>')
def toggle_status(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	s = 0
	if not group_data['status']:
		s = 1
	query = 'UPDATE groupme_yahoo SET status='+str(s)+', messaging_status= '+str(s)+' WHERE groupme_group_id='+str(groupme_id)+';'
	db.execute_table_action(query)
	return display_status(groupme_bot=groupme_bot)

@app.route('/transactions/<int:groupme_id>')
def transactions(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	if group_data['status'] > 0:
		return (groupme_bot.post_trans_list(group_data), 200)
	else:
		return (display_status(groupme_bot=groupme_bot), 200)

@app.route('/group/<int:groupme_id>')
def display_group(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	if group_data:
		top = {'Bot Status':group_data['status'], 
		'Messaging Status': group_data['messaging_status']}
		t1 = {'GroupMe Group ID': group_data['groupme_group_id'], 
		'Current Message Count': group_data['message_num'], 
		'Current Message Cap': group_data['message_limit'],
		'Bot ID (do not share)': group_data['bot_id']}
		member_list = []
		for k, v in group_data['members'].items():
			member_list.append({'Name': v['name'], 
			'GroupMe ID': v['user_id'], 'GroupMe Nickname': v['nickname']})
		return render_template("group.html", top = top, group_table = t1, 
		member_list=member_list,triggers=group_data['triggers'], group_data=group_data)
	else:
		return ("No group found", 404)


@app.route('/checkTriggers/<int:groupme_id>')
def check_triggers(groupme_id):
	groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	group_data = initialize_group(groupme_id, groupme_bot=groupme_bot)
	if request.values:
		groupme_bot.create_trigger(group_data, request.values)
	triggers = groupme_bot.check_triggers(group_data)
	logging.warn("t %s"%json.dumps(triggers))
	if triggers:
		m = ''
		for t in triggers:
			m += json.dumps(t)
		return m,200
	return "No trigger found", 404

# @app.route('/messages/<int:groupme_id>')
# def get_messages(groupme_id):
# 	groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
# 	messages = groupme_bot.load_messages()
# 	return (groupme_bot.)

# @app.route('/name-changes/*')
# def name_changes():	
# 	groupme_bot, group_data = initialize_group(group_id)
# 	return (groupme.update_group_membership(group_data))

# @app.errorhandler(404)
# def not_found(error):
#     return render_template('error.html'), 404