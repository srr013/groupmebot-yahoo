import os
import json
import datetime
from flask import Flask, request, session, render_template
import logging
import GroupMe_Bot
import message as m
import fantasy as f
#from helpers.secrets import secrets
import db
import groupme

app = Flask(__name__)
key =  os.environ.get('CONSUMER_KEY')
if not key:
	key = app.config.from_envvar('CONSUMER_KEY')
secret = os.environ.get('CONSUMER_SECRET')
if not secret:
	secret = app.config.from_envvar('CONSUMER_SECRET')
app.secret_key = secret

# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['GET','POST'])
def webhook():
	monitoring_status, messaging_status = GroupMe_Bot.get_application_status()
	if request.method == 'GET':
		return display_status()
	elif request.method == 'POST' and monitoring_status:
		message = request.get_json()
		logging.warn("Message received from %s at %s" % (str(message['name']), datetime.datetime.strftime(datetime.datetime.now(), '%d-%m-%Y %H:%M')))
		group_data = GroupMe_Bot.get_group_data(message['group_id'])
		GroupMe_Bot.save_message(message)
		msg_ready = False
		msg_type = 'reply'
		msg = ''
		if not m.sender_is_bot(message):
			msg_ready, msg, msg_type = GroupMe_Bot.check_msg_for_command(message, group_data)
			if int(group_data['messaging_status']) > 0 or msg_ready:
				GroupMe_Bot.increment_message_num(group_data['index'])
				logging.warn("Checking for active triggers")
				active_triggers = GroupMe_Bot.check_triggers(group_data)
				if active_triggers:
					trigger_msg = GroupMe_Bot.get_trigger_messages(group_data, active_triggers)
					if trigger_msg:
						m.send_message(trigger_msg, group_data['bot_id'])
				logging.warn("Processing user message")
				# logging.info(group_data)
				if not msg_ready:
					msg_ready, msg, msg_type = GroupMe_Bot.talking_to_self(group_data)
				if not msg_ready:
					msg_ready, msg, msg_type = GroupMe_Bot.talking_to_bot(message, group_data)
				if not msg_ready:
					if group_data['message_num'] >= group_data['message_limit']:
						msg_ready, msg, msg_type = GroupMe_Bot.insult(message, group_data)
				if msg_ready:
					if msg_type == 'mention':
						m.send_with_mention(msg, message['name'], message['sender_id'], group_data['bot_id'])
					elif msg_type == 'image':
						m.send_with_image(group_data['bot_id'], msg)
					else:
						m.send_message(msg, group_data['bot_id'])
		return "ok", 200
	return "not found", 404

@app.route('/create_group/<int:groupme_id>')
def create_group(groupme_id):
	# groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	group_data = GroupMe_Bot.get_group_data(groupme_id)
	return display_status()

@app.route('/toggle/<int:groupme_id>')
def toggle_status(groupme_id):
	group_data = GroupMe_Bot.get_group_data(groupme_id)
	GroupMe_Bot.toggle_group_messaging_status(group_data)
	return display_status()

@app.route('/transactions/<int:groupme_id>')
def transactions(groupme_id):
	# groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	# group_data = initialize_group(groupme_id)
	group_data = GroupMe_Bot.get_group_data(groupme_id)
	if group_data['status'] > 0:
		logging.warn("Getting league transactions")
		transaction_msg = GroupMe_Bot.get_transaction_msg(group_data)
		logging.warn("Transaction message: %s" %(transaction_msg))
		if transaction_msg:
			m.send_message(transaction_msg, group_data['bot_id'])
	return display_status()

@app.route('/group/<int:groupme_id>')
def display_group(groupme_id):
	# groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	group_data = GroupMe_Bot.get_group_data(groupme_id)
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
	# groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	group_data = GroupMe_Bot.get_group_data(groupme_id)
	if request.values:
		if request.values.get('type') and request.values.get('days') and request.values.get('periods'):
			GroupMe_Bot.create_trigger(group_data, request.values)
		else:
			return "Bad parameters", 404
	triggers = GroupMe_Bot.check_triggers(group_data)
	# logging.warn("t %s"%json.dumps(triggers))
	if triggers:
		m = ''
		for t in triggers:
			m += json.dumps(t)
			#not rendering active versus inactive/fired vs waiting to fire
	return json.dumps(group_data['triggers']), 200


# @app.errorhandler(404)
# def not_found(error):
#     return render_template('error.html'), 404


def display_status():
	# if not groupme_bot:
	# 	groupme_bot = GroupMe_Bot.GroupMe_Bot(app)
	data = GroupMe_Bot.get_display_status()
	#logging.warn(config)
	return render_template("index.html", groupme_groups=data['group_data'],	groupme_headers=data['headers'], global_data=data['global_data'])