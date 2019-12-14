import requests
import json
import logging
import random
from helpers.secrets import secrets
import db
import utilities
import fantasy
import message as m
import GroupMe_Bot
from insults import talking_to_self as talking
from team_map import team_map as t

def get_group_membership(group_id):
    res =requests.get('https://api.groupme.com/v3/groups/'+str(group_id)+'?token='+secrets['access_token'])
    if res.status_code == 200:
        data = json.loads(res.text)
        members = {}
        for member in data["response"]["members"]:
            members[member['user_id']] = member
        return members
    else:
        return {}

def update_and_post_group_membership(group_data):
    string = 'None'
    if group_data['members']:
        groupme_bot = GroupMe_Bot.GroupMe_Bot()
        data = groupme_bot.get_league_data()
        teams = data['teams']['fantasy_content']['league'][1]['teams']
        team_data = fantasy.get_team_data(teams)
        for k, v in group_data['members'].items():
            logging.warn("K, V from client data: %s %s %s" % (k, v, json.dumps(team_data)))
            if team_data.get(v['team_id']):
                if group_data['members'][k]['team_data']['name'] is not team_data[v['team_id']]['name']:
                    string += group_data['members'][k]['name'] + 'changes team name to '+ team_data[v['team_id']]['name'] + "\n"
            group_data['members'][k]['team_data'] = team_data[v['team_id']]
    query = "UPDATE groupme_yahoo SET members="+utilities.dict_to_json(group_data['members'])+"WHERE session=1;"
    db.execute_table_action(query)
    return string

def talking_to_self(messages, lim=4):
	randomizer = random.randint(lim-1,lim+1) - lim
	lim += randomizer
	user = []
	first = ''
	for message in messages[len(messages)-lim:len(messages)]:
		#logging.warn("%s, %s"%(message, first))
		if isinstance(message[0], dict):
			user.append(message[0]['sender_id'])
		if not first:
			first = str(message[0]['sender_id'])
	logging.warn(user)
	if len(user) >= lim:
		for u in user:
			if str(u) != str(first):
				#logging.warn("u %s,f %s"%(u,first))
				return None
		return talking[random.randint(0,len(talking)-1)]
	return None