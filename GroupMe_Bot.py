from yahoo_oauth import OAuth2
import json
import logging
import random
from datetime import datetime
import db
import groupme
import utilities
import fantasy as f
import message as m
import Triggers

#"70e9ad5bc50020fdb3a14dbca1", "test_bot_id": "566e3b05b73cb551006cf34410"

class GroupMe_Bot():
	def __init__(self):
		self.oauth = OAuth2(None, None, from_file='helpers/oauth2yahoo.json')
		self.high = 13
		self.low = 9
		self.monitoring_status = False
		self.messaging_status = True
		self._login()

	def _login(self):
		if not self.oauth.token_is_valid():
			self.oauth.refresh_access_token()
		query = """SELECT * FROM application_data"""
		cursor = db.execute_table_action(query, cur=True)
		self.monitoring_status, self.messaging_status = cursor.fetchone()
    
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

	def post_trans_list(self, group_data):
		league_data = self.get_league_data()
		trans_list = f.get_transaction_list(league_data, group_data['transaction_num'])
		s = 'None'
		if trans_list:
			new_trans_num = f.get_transaction_total(league_data)
			query = "UPDATE groupme_yahoo SET num_past_transactions = "+str(new_trans_num)+" WHERE index = "+str(group_data['index'])+";"
			logging.warn("Setting new transaction figure %s"%str(new_trans_num))
			db.execute_table_action(query)
			s = "Recent transactions: \n"
			for t in trans_list:
				s += t
			if group_data['status']:
				logging.warn("id %s" %str(group_data['bot_id']))
				m.reply(s, group_data['bot_id'])
				with open("transaction_list.txt", "w+") as o:
					for l in trans_list:
						o.write(str(l))
			return str(s)
		return "No transactions found"
    
	def fetch_group_data(self, group_id):
		#groups: TEST:32836424, PRD:55536872
		logging.debug("Fetching league data from DB")
		if group_id:
			query = "SELECT * FROM groupme_yahoo WHERE groupme_group_id = "+str(group_id)
			cursor = db.execute_table_action(query, cur=True)
			results = cursor.fetchone()
			if results:
				message_num,message_limit, past_transaction_num, league_data, status, messaging_status, prd_bot_id, members,groupme_group_id, index, messages, trigger = results
				group_data = {'index': index, 'message_num':message_num, 
                            'message_limit': message_limit,
                            'transaction_num': past_transaction_num,
                            'status': int(status), 'messaging_status': int(messaging_status),
                            'bot_id': prd_bot_id,
                            'groupme_group_id': groupme_group_id, 
							'messages': [] if not messages else json.loads(messages),
							'trigger': [] if not trigger else json.loads(trigger),
                            'members': members}
				logging.warning("Messaging Trigger: %i / %i messages, Messaging Status: %i, Monitoring Status: %i (1 is On)"%
				(message_num,message_limit,messaging_status, status))
                # if not league_data:
                #     league_data = self.get_league_data()
				return group_data
		return False

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
			query = "SELECT * FROM groupme_yahoo"
			cursor = db.execute_table_action(query, cur=True)
			groups = cursor.fetchall()
			status = "" #need to configure a global status toggle
			for group in groups:
				g = self.get_group_data(group[8],'')
				bot_id = g['bot_id'][0:4]
				group_data.append([group[8],bot_id,"On" if g['status'] else "Off","On" if g['messaging_status'] else "Off", g['message_num'], g['message_limit']])
		display = {"headers": headers, "group_data": group_data, "global_data": global_data}
                # for k,v in g.items():
                #     new_display += str(k) + ": "
                #     new_display += str(v)
		return display
	
	def get_league_data(self):
        #TODO: pass in league through here
		league = 12
		weeks = 10
		data = {}
		url_list = ['teams','transactions;types=add']
                #'standings','scoreboard',
                # ;week='+str(week),'teams','players',
                #'.t.'+str(team)+'/roster;week='+str(week) ]

		for url in url_list:
			response = self.oauth.session.get(self.build_url(url), params={'format': 'json'})
			url = url.split(';')
			data[url[0]] = json.loads(response.text)
            #there's paging involved to get additional pages of data - players
            #data[url]['fantasy_content']['league'][0] - settings for that league
            #data[url]['fantasy_content']['league'][1][url] - url-related data fo


        #'https://fantasysports.yahooapis.com/fantasy/v2/league/nfl.l.186306/season?format=json'
        #self.save_league_data(group_data['index'], data)
		return data

    # def get_matchup_score(self, matchup):
    #     team_0 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][0]
    #     team_1 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][1]
    #     t0_id = team_0['team'][0][0].get(['team_key'])
    #     t0_name = team_0['team'][0][0].get(['team_name'])
    #     t0_current_score = team_0['team'][1]['team_points']['total']
	def check_triggers(self, group_data):
		group_data['trigger']
		trigger_types = ["Test"]
		active_triggers = []
		triggers = group_data['trigger']
		for trigger_type in trigger_types:
			for t in triggers:
				if Triggers.check_trigger(t, trigger_type, datetime.now()):
					active_triggers.append(t)
		return active_triggers

	def create_trigger(self, group_data, req_dict):
        # trigger_type = "Test"
        # days = ["mon"]
        # periods = ["evening"]
		periods = []
		days = []
		for k, v in req_dict.items():
			if k.lower() == 'type':
				trigger_type = v
			elif k.lower() == 'days':
				days = v
			elif k.lower() == 'periods':
				periods = v
		triggers = group_data['trigger']
		new_trigger = Triggers.create_trigger(trigger_type, days, periods)
		logging.warn(new_trigger)
		if triggers:
			triggers.append(new_trigger)
			self.update_triggers(group_data['index'],json.dumps(triggers))
		else:
			self.update_triggers(group_data['index'], json.dumps([new_trigger]))


	def increment_message_num(self, group):
		query = "UPDATE groupme_yahoo SET message_num = message_num + 1 WHERE index = "+str(group)+";"
		db.execute_table_action(query)

	def reset_message_data(self, group):
		lim = random.randint(self.low, self.high)
		query = "UPDATE groupme_yahoo SET message_num = 0, message_limit = "+str(lim)+" WHERE index = "+str(group)+";"
		db.execute_table_action(query)

	def save_league_data(self, group, data):
		data = json.dumps(data)
		data.strip("'")
		query = "UPDATE groupme_yahoo SET league_data = %s WHERE index = %s;"
		values = (data, str(group))
		db.execute_table_action(query, values)

	def load_messages(self, groupme_group_id, message=None):
		if groupme_group_id:
			select = "SELECT message FROM messages WHERE groupme_group_id = %s;"
			select_values = (groupme_group_id,)
			cursor = db.execute_table_action(select, values=select_values, cur=True)
			messages = cursor.fetchall()
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

    
	def update_triggers(self, group, triggers):
		data = json.dumps(triggers)
		data.strip("'")
		query = "UPDATE groupme_yahoo SET trigger = %s WHERE index = %s;"
		values = (triggers, str(group))
		db.execute_table_action(query, values)

