import requests
import json
import logging
#from helpers.secrets import secrets
import db
import utilities
import fantasy
import message as m
# import GroupMe_Bot
from team_map import team_map as t

def get_group_membership(group_id, groupme_access_token):
    res =requests.get('https://api.groupme.com/v3/groups/'+str(group_id)+'?token='+groupme_access_token)
    if res.status_code == 200:
        data = json.loads(res.text)
        members = {}
        for member in data["response"]["members"]:
            members[member['user_id']] = member
        return members
    else:
        return {}

def update_and_post_group_membership(group_data, league_data):
    string = 'None'
    if group_data['members']:
        # groupme_bot = GroupMe_Bot.GroupMe_Bot()
        # data = GroupMe_Bot.get_league_data()
        teams = league_data['teams']['fantasy_content']['league'][1]['teams']
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

