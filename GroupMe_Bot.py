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

class GroupMe_Bot():
	def __init__(self, app):
		self.high = 16
		self.low = 4
		self.monitoring_status = False
		self.messaging_status = True
		self.tz = pytz.timezone('US/Eastern')
		self.app = app
		# self.auth = {
		# 	"access_token": os.environ["ACCESS_TOKEN"],
		# 	"consumer_key": os.environ["CONSUMER_KEY"],
		# 	"consumer_secret": os.environ["CONSUMER_SECRET"],
		# 	"guid": "DBB4EWZHLD3WLDR6XYRQ6ZPQKQ",
		# 	"refresh_token": os.environ["REFRESH_TOKEN"],
		# 	"token_time": 1576623325.5492997,
		# 	"token_type": "bearer"
		# }
		from boto.s3.connection import S3Connection
		s3 = S3Connection(app.config.from_envvar('CONSUMER_KEY'),
		 app.config.from_envvar('CONSUMER_SECRET'))
		self.oauth = OAuth2(app.config.from_envvar('CONSUMER_KEY'), app.config.from_envvar('CONSUMER_SECRET'))
		self._login()

	def _login(self):

		if not self.oauth.token_is_valid():
			self.oauth.refresh_access_token()
		query = """SELECT * FROM application_data"""
		self.monitoring_status, self.messaging_status = db.fetch_one(query)
    
	def create_group(self, group_id, bot_id):
		#does not set the bot_id for the group - manuually set this in order to post messages
		query = """INSERT INTO groupme_yahoo 
		(groupme_group_id, message_num, message_limit,
			num_past_transactions,
			status, messaging_status, bot_id, members) 
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"""
		members = groupme.get_group_membership(group_id)
		values = (str(group_id),0,1,0,1,1,str(bot_id),utilities.dict_to_json(members))
		db.execute_table_action(query, values)

	def post_group(self, group_data):
		group_data = f.append_league_data(group_data, self.oauth)

	def post_trans_list(self, group_data):
		league_data = f.get_league_data(self.oauth)
		trans_list = f.get_transaction_list(league_data, group_data['transaction_num'])
		s = 'None'
		if trans_list:
			new_trans_num = f.get_transaction_total(league_data)
			s = "Recent transactions: \n"
			for t in trans_list:
				s += t
			logging.warn("s %s" % (s))
			if group_data['status']:
				logging.warn("id %s" %str(group_data['bot_id']))
				m.reply(s, group_data['bot_id'])
				# with open("transaction_list.txt", "w+") as o:
				# 	for l in trans_list:
				# 		o.write(str(l))
			query = "UPDATE groupme_yahoo SET num_past_transactions = "+str(new_trans_num)+" WHERE index = "+str(group_data['index'])+";"
			logging.warn("Setting new transaction figure %s"%str(new_trans_num))
			db.execute_table_action(query)
			return str(s)
		return "No transactions found"
    
	def fetch_group_data(self, group_id):
		#groups: TEST:32836424, PRD:55536872
		logging.debug("Fetching group data from DB")
		if group_id:
			query = """SELECT index, groupme_group_id, message_num, message_limit, 
			num_past_transactions, league_data, status, messaging_status, bot_id, members
			FROM groupme_yahoo WHERE groupme_group_id = %s"""
			values = (group_id,)
			results = db.fetch_one(query, values)
			if results:
				#message_num, message_limit, past_transaction_num, league_data, status, messaging_status, bot_id, members,groupme_group_id, index = results
				# logging.warn("loading trigger: %s"%trigger)
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
				#logging.warn(group_data)
				group_data['triggers'] = self.load_triggers(group_data['index'])
				# logging.warning("Messaging Trigger: %i / %i messages, Messaging Status: %i, Monitoring Status: %i (1 is On)"%
				# (message_num,message_limit,messaging_status, status))
                # if not league_data:
                #     league_data = self.get_league_data()
				return group_data
		return {}

	def get_group_data(self, group_id, bot_id):
		logging.warn("Getting Group Data for group %s"%(group_id))
		group_data = self.fetch_group_data(group_id)
		if not group_data and bot_id:
			logging.warn("Creating new group: %s /n" %(bot_id))
			self.create_group(group_id, bot_id)
			group_data = self.fetch_group_data(group_id)
		#league_data = self.get_league_data()
		return group_data

	def build_url(self, req):
		base_url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
		sport = 'nfl'
		league_id = '186306' #TODO: Manage multiple leagues 
		request = "/"+str(req)
		league_key = sport + '.l.'+ league_id 
		return str(base_url + league_key + request)
    
	def display_status(self):
		group_data = []
		self._login()
		headers = ["GroupMe Group ID","Bot ID","Bot Monitoring Status",
		"Bot Messaging Status", "Current Message", "Triggering Message"]
		global_data = ["Global monitoring status: "+"On" if self.monitoring_status else "Off",
		"Global messaging status: "+ "On" if self.messaging_status else "Off"]
		if self.monitoring_status:
			query = "SELECT groupme_group_id FROM groupme_yahoo"
			groups = db.fetch_all(query)
			logging.warn("groups: %s"%groups)
			for group in groups:
				g = self.get_group_data(group[0],'')
				logging.warn("g %s"%g)
				bot_id = g['bot_id'][0:4]
				group_data.append([group[0],bot_id,"On" if g['status'] else "Off","On" if g['messaging_status'] else "Off", g['message_num'], g['message_limit']])
		display = {"headers": headers, "group_data": group_data, "global_data": global_data}
                # for k,v in g.items():
                #     new_display += str(k) + ": "
                #     new_display += str(v)
		return display

	def check_triggers(self, group_data):
		trigger_types = ["test", "transactions"]
		active_triggers = []
		triggers = group_data['triggers']
		logging.warn("triggers: %s"%group_data['triggers'])
		day, period = Triggers.get_date_period(datetime.now(tz=self.tz))
		for trigger_type in trigger_types:
			for t in triggers:
				if Triggers.check_trigger(t, trigger_type, day, period):
					active_triggers.append(t)
		return active_triggers

	def send_trigger_messages(self, group_data, active_triggers):
		day,period = Triggers.get_date_period(datetime.now(tz=self.tz))
		for trigger in active_triggers:
			if trigger['type'] == 'transactions':
				trigger['status'] = [day, period]
				self.post_trans_list(group_data)
				self.update_trigger_status(trigger)

	def create_trigger(self, group_data, req_dict):
		periods = []
		days = []
		for k, v in req_dict.items():
			#logging.warn(v, type(v))
			if k.lower() == 'type':
				trigger_type = v
			elif k.lower() == 'days':
				days = utilities.string_to_list(v)
			elif k.lower() == 'periods':
				periods = utilities.string_to_list(v)
		new_trigger = Triggers.create_trigger(trigger_type, days, periods)
		logging.warn("Creating trigger: %s"%(new_trigger))
		self.add_trigger(group_data['index'], new_trigger)

	def add_trigger(self, group, trigger):
		query = """INSERT INTO triggers (type,days,periods,status,group_id) 
		VALUES (%s, %s, %s, %s, %s);"""
		values = (trigger['type'],trigger['days'], trigger['periods'],
		trigger['status'], str(group))
		db.execute_table_action(query, values)
	
	def delete_trigger(self, index):
		query = """DELETE FROM triggers WHERE index=%s"""
		values = (index,)
		db.execute_table_action(query, values)
	
	def load_triggers(self, group_id):
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
	
	def update_trigger_status(self, trigger):
		query = """UPDATE triggers SET status=%s WHERE i=%s""" 
		values = (trigger['status'], trigger['index'])
		db.execute_table_action(query, values)

	def increment_message_num(self, group):
		query = "UPDATE groupme_yahoo SET message_num = message_num + 1 WHERE index = %s;"
		values = (str(group),)
		db.execute_table_action(query, values)

	def reset_message_data(self, group):
		lim = random.randint(self.low, self.high)
		query = "UPDATE groupme_yahoo SET message_num = 0, message_limit = %s WHERE index = %s;"
		values = (str(lim), str(group))
		db.execute_table_action(query, values)

	#refresh
	def save_league_data(self, group, data):
		data = json.dumps(data)
		data.strip("'")
		query = "UPDATE groupme_yahoo SET league_data = %s WHERE index = %s;"
		values = (data, str(group))
		db.execute_table_action(query, values)

	def check_messages(self, group_data):
		messages = self.load_messages(group_data['groupme_group_id'])
		if messages:
			messages.sort(key=lambda t: t[1])
			user = ''
			if len(messages) > 5:
				if len(messages) > 100:
					self.delete_messages(messages)
				msg = groupme.talking_to_self(messages)
			if msg:
				m.reply(msg, group_data['bot_id'])

	def load_messages(self, groupme_group_id, message=None):
		if groupme_group_id:
			select = "SELECT message, i FROM messages WHERE groupme_group_id = %s;"
			select_values = (str(groupme_group_id),)
			messages = db.fetch_all(select, values=select_values)
			if message:
				messages.append(message)
			return messages
		else:
			logging.warn("Attempted save on null message")
		return []
			
	def save_message(self, message):
		if message:
			query = "INSERT INTO messages(message, groupme_group_id) VALUES (%s, %s);"
			values = (str(json.dumps(message)), str(message['group_id']))
			db.execute_table_action(query, values)
		else:
			logging.warn("Attempted save on null message")

	def delete_messages(self, messages, anchor=100):
		if len(messages) > anchor:
			index_list = []
			for message in messages:
				index_list.append(message[1])
			index_list.sort()
			val = len(index_list) - anchor
			query = "DELETE FROM messages WHERE i IN %s"
			values = tuple(index_list[0:val])
			db.execute_table_action(query, (values,))
			logging.warn("Old messages deleted: %s"% (values,))
    

