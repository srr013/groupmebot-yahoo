from yahoo_oauth import OAuth2
import json
import logging
import os
import random
from datetime import datetime
import pytz
import db
import groupme
import utilities
import fantasy as f
import message as m
import Triggers


#"70e9ad5bc50020fdb3a14dbca1", "test_bot_id": "566e3b05b73cb551006cf34410"
tz = pytz.timezone('US/Eastern')
groupme_access_token = os.environ.get('GM_ACCESS_TOKEN')
consumer_key = os.environ.get('CONSUMER_KEY')
consumer_secret = os.environ.get('CONSUMER_SECRET')
access_token = os.environ.get('ACCESS_TOKEN')
refresh_token = os.environ.get('REFRESH_TOKEN')

def yahoo_login():
	if consumer_key:
		oauth = OAuth2(consumer_key, consumer_secret, access_token=access_token, refresh_token=refresh_token, token_type="bearer", token_time=1599612658.9733138)
	else:
		oauth = OAuth2(None, None, from_file='helpers/oauth2yahoo.json')
	# if not oauth.token_is_valid():
	# 	oauth.refresh_access_token()
	return oauth

def get_application_status():
	query = """SELECT * FROM application_data"""
	monitoring_status, messaging_status = db.fetch_one(query)
	return monitoring_status, messaging_status


def create_group(group_id, bot_id):
	#does not set the bot_id for the group - manuually set this in order to post messages
	query = """INSERT INTO groupme_yahoo 
	(groupme_group_id, message_num, message_limit,
		num_past_transactions,
		status, messaging_status, bot_id, members) 
		VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"""
	members = groupme.get_group_membership(group_id, groupme_access_token)
	values = (str(group_id),0,1,0,1,1,str(bot_id),utilities.dict_to_json(members))
	db.execute_table_action(query, values)

def post_group(group_data):
	oauth = yahoo_login()
	group_data = f.append_league_data(group_data, oauth)

def get_group_data(group_id):
	logging.debug("Fetching group data from DB")
	if group_id:
		query = """SELECT index, groupme_group_id, message_num, message_limit, 
		num_past_transactions, league_data, status, messaging_status, bot_id, members
		FROM groupme_yahoo WHERE groupme_group_id = %s"""
		values = (group_id,)
		results = db.fetch_one(query, values)
		if results:
			group_data = {'index': results[0], 
						'message_num':results[2], 
						'message_limit': results[3],
						'transaction_num': results[4],
						'status': int(results[6]), 
						'messaging_status': int(results[7]),
						'bot_id': results[8],
						'groupme_group_id': results[1],
						'members': results[9] if results[9] else {}
						}
			group_data['triggers'] = load_triggers(group_data['index'])
			delete_messages(load_messages(group_data['groupme_group_id']), msg_limit=10)
			return group_data
	logging.error("No Group Found in fetch_group_data")
	return {}


def build_url(req):
	base_url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
	sport = 'nfl'
	league_id = '186306' #TODO: Manage multiple leagues 
	request = "/"+str(req)
	league_key = sport + '.l.'+ league_id 
	return str(base_url + league_key + request)

def get_display_status():
	group_data = []
	# _login()
	monitoring_status, messaging_status = get_application_status()
	headers = ["GroupMe Group ID","Bot ID","Bot Monitoring Status",
	"Bot Messaging Status", "Current Message", "Triggering Message"]
	global_data = ["Global monitoring status: "+"On" if monitoring_status else "Off",
	"Global messaging status: "+ "On" if messaging_status else "Off"]
	if monitoring_status:
		query = "SELECT groupme_group_id FROM groupme_yahoo"
		groups = db.fetch_all(query)
		# logging.warn("groups: %s"%groups)
		for group in groups:
			g = get_group_data(group[0])
			# logging.warn("g %s"%g)
			bot_id = g['bot_id'][0:4]
			group_data.append([group[0],bot_id,"On" if g['status'] else "Off","On" if g['messaging_status'] else "Off", g['message_num'], g['message_limit']])
	display = {"headers": headers, "group_data": group_data, "global_data": global_data}
	return display



def increment_message_num(group):
	query = "UPDATE groupme_yahoo SET message_num = message_num + 1 WHERE index = %s;"
	values = (str(group),)
	db.execute_table_action(query, values)

def reset_message_data(group):
	lim = random.randint(7, 22)
	query = "UPDATE groupme_yahoo SET message_num = 0, message_limit = %s WHERE index = %s;"
	values = (str(lim), str(group))
	db.execute_table_action(query, values)

#refresh
def save_league_data(group, data):
	data = json.dumps(data)
	data.strip("'")
	query = "UPDATE groupme_yahoo SET league_data = %s WHERE index = %s;"
	values = (data, str(group))
	db.execute_table_action(query, values)

def get_transaction_msg(group_data):
	logging.warn("Defining transaction message for group %s" %(group_data['groupme_group_id']))
	oauth = yahoo_login()
	league_data = f.get_league_data(oauth)
	teams = f.get_fantasy_teams(league_data)
	trans_list = f.get_transaction_list(league_data, group_data['transaction_num'])
	s = ''
	new_trans_num = 0
	if trans_list:
		new_trans_num = f.get_transaction_total(league_data)
		s = "Recent transactions: \n"
		for t in trans_list:
			team_id = t['team_key'].split('.')[-1]
			s += teams[team_id]['name'] + ' ('+teams[team_id]['owner']+') ' + t['trans_type']+ 's '+ t['player_name']+'('+t['player_position']+')\n'
		set_new_transaction_total(new_trans_num, group_data)
	return str(s)

def set_new_transaction_total(new_trans_num, group_data):
	query = "UPDATE groupme_yahoo SET num_past_transactions = "+str(new_trans_num)+" WHERE index = "+str(group_data['index'])+";"
	logging.warn("Setting new transaction figure %s"%str(new_trans_num))
	db.execute_table_action(query)

def check_msg_for_command(message, group_data):
	ready = False
	msg = ''
	help_text = """
	Bot Help Text: \n
	--help : this help text screen \n
	-stop : turn off all bot GroupMe messages \n
	--start : restart GroupMe messaging \n
	--status : return the messaging status of the bot \n
	--transactions: show fantasy league transactions \n
	"""
	msg = ''
	msg_type = 'reply'
	if message:
		insult_type = ''
		if "--stop" in message['text'].lower():
			msg = 'Stopping GroupMe Bot messaging service'
			toggle_group_messaging_status(group_data, val=0)
		elif "--start" in message['text'].lower():
			msg = 'Starting GroupMe Bot messaging service'
			toggle_group_messaging_status(group_data, val=1)
		elif "--status" in message['text'].lower():
			s = 'On' if int(group_data['messaging_status']) else 'Off'
			msg = 'GroupMe Bot messaging status is: ' + s
		elif "--help" in message['text'].lower():
			msg = help_text
		elif "--transactions" in message['text'].lower():
			msg = get_transaction_msg(group_data)
			if not msg:
				msg = 'No new transactions' #if someone requests transactions they should get a specific message back instead of defaulting to standard response stream
		elif "--insult" in message['text'].lower():
			if '--response' in message['text'].lower():
				insult_type = 'response'
			elif '--self-aware' in message['text'].lower():
				insult_type = 'self-aware'
			elif '--encouragement' in message['text'].lower():
				insult_type = 'encouragement'
			elif '--image' in message['text'].lower():
				insult_type = 'image'
			ready, msg, msg_type = random_insult(message, group_data, insult_type=insult_type)
		if msg:
			ready = True
			logging.warn("Command identified in message")
	return ready, msg, msg_type

def talking_to_self(group_data):
	messages = load_messages(group_data['groupme_group_id'])
	ready = False
	msg = ''
	if messages:
		messages.sort(key=lambda t: t[1])
		if len(messages) > 5:
			msg, msg_type = m.talking_to_self(messages)
			if msg:
				logging.warn("Someone's talking to themselves. Insulting.")
				ready = True
	return ready, msg, msg_type

def talking_to_bot(message, group_data):
	# logging.info(message['text'].lower())
	names = ['insultbot', 'insult bot']
	ready = False
	msg = ''
	msg_type = 'reply'
	if any(name in message['text'].lower() for name in names):
		ready = True
		logging.info("Responding to comment to bot")
		msg =  m.talking_to_bot()
	return ready, msg, msg_type

def random_insult(message, group_data, insult_type=''):
	# logging.warning("message: "+ message['text']+", "+
	# 	str(group_data['message_num']+1)+" / "+str(group_data['message_limit'])+
	# 	"message_full: " +str(json.dumps(message))+", Chat: "+group_data['bot_id'])
	ready = True
	reset_message_data(group_data['index'])
	msg, msg_type = m.get_message(message['name'], insult_type)
	return ready, msg, msg_type

def toggle_group_messaging_status(group_data, val=''):
	if val == '':
		s = 0
		if not group_data['status']:
			s = 1
	else:
		if val == 0 or val == 1:
			s = val
	if s:
		query = 'UPDATE groupme_yahoo SET messaging_status= '+str(s)+' WHERE groupme_group_id='+str(group_data['groupme_group_id'])+';'
		db.execute_table_action(query)
	return

def load_messages(groupme_group_id):
	messages = []
	if groupme_group_id:
		select = "SELECT message, i, sender_is_bot FROM messages WHERE groupme_group_id = %s;"
		select_values = (str(groupme_group_id),)
		raw_messages = db.fetch_all(select, values=select_values)
		for msg in raw_messages:
			if not msg[2]:
				messages.append(msg)
	else:
		logging.warn("Attempted save on null message")
	return messages
		
def save_message(message):
	if message:
		is_bot = False
		if message['sender_type'] != 'user':
			is_bot = True
		query = "INSERT INTO messages(message, groupme_group_id, sender_is_bot) VALUES (%s, %s, %s);"
		values = (str(json.dumps(message)), str(message['group_id']), is_bot)
		db.execute_table_action(query, values)
	else:
		logging.warn("Attempted save on null message")

def delete_messages(messages, msg_limit=100):
	if len(messages) > msg_limit:
		index_list = []
		#logging.warn(messages[0])
		for message in messages:
			index_list.append(message[1])
		index_list.sort()
		val = len(index_list) - msg_limit
		query = "DELETE FROM messages WHERE i IN %s"
		values = tuple(index_list[0:val])
		#logging.warn("values: %s" % (values,))
		db.execute_table_action(query, (values,))
		#logging.warn("Old messages deleted")



def check_triggers(group_data):
	trigger_types = ["test", "transactions"]
	active_triggers = []
	triggers = group_data['triggers']
	# logging.warn("triggers: %s"%group_data['triggers'])
	day, period = Triggers.get_date_period(datetime.now(tz=tz))
	for trigger_type in trigger_types:
		for t in triggers:
			if Triggers.check_trigger(t, trigger_type, day, period):
				active_triggers.append(t)
				t['active'] = True
			else:
				if t['status'][0] != day and t['status'][1] != period:
					t['status'] = ['','']
					update_trigger_status(t)
				t['active'] = False
	return active_triggers

def get_trigger_messages(group_data, active_triggers):
	transaction_msg = ''
	day,period = Triggers.get_date_period(datetime.now(tz=tz))
	for trigger in active_triggers:
		trigger['status'] = [day, period]
		if trigger['type'] == 'transactions':
			transaction_msg, new_trans_total = get_transaction_msg(group_data)
			if transaction_msg and new_trans_total:
				set_new_transaction_total(new_trans_total, group_data)
		if trigger['type'] == 'test':
			logging.warn("Test trigger fired successfully")
		update_trigger_status(trigger)
	return transaction_msg

def create_trigger(group_data, req_dict):
	periods = []
	days = []
	for k, v in req_dict.items():
		#logging.warn(v, type(v))
		if k.lower() == 'type':
			trigger_type = v
		elif k.lower() == 'days':
			days = utilities.string_to_list(v)
		elif k.lower() == 'periods':
			#morning, noon, evening, late
			periods = utilities.string_to_list(v)
	new_trigger = Triggers.create_trigger(trigger_type, days, periods)
	logging.warn("Creating trigger: %s"%(new_trigger))
	add_trigger(group_data['index'], new_trigger)

def add_trigger(group, trigger):
	query = """INSERT INTO triggers (type,days,periods,status,group_id) 
	VALUES (%s, %s, %s, %s, %s);"""
	values = (trigger['type'],trigger['days'], trigger['periods'],
	trigger['status'], str(group))
	db.execute_table_action(query, values)

def delete_trigger(index):
	query = """DELETE FROM triggers WHERE index=%s"""
	values = (index,)
	db.execute_table_action(query, values)

def load_triggers(group_id):
	query = """SELECT * FROM triggers WHERE group_id=%s"""
	values = (group_id,)
	l = db.fetch_all(query, values)
	triggers = []
	for trigger in l:
		d = {
			'index':trigger[0],
			'type':trigger[1],
			'days':trigger[2],
			'periods': trigger[3],
			'status':trigger[4],
			'group_id':trigger[5]
		}
		triggers.append(d)
	return triggers

def update_trigger_status(trigger):
	query = """UPDATE triggers SET status=%s WHERE i=%s""" 
	values = (trigger['status'], trigger['index'])
	db.execute_table_action(query, values)