import requests
import json
from helpers.secrets import secrets
import db
import utilities
import fantasy
import League_Bot
from team_map import team_map as t

def get_group_membership():
    res =requests.get('https://api.groupme.com/v3/groups/32836424?token='+secrets['access_token'])
    data = json.loads(res.text)
    members = {}
    for member in data["response"]["members"]:
        members[member['user_id']] = member
    league_bot = League_Bot.League_Bot(1)
    data = league_bot.get_league_data()
    teams = data['teams']['fantasy_content']['league'][1]['teams']
    team_data = fantasy.get_team_data(teams)
    for key, val in t.items():
        for k,v in members.items():
            if val == k:
                members[k]['team_id'] = key
                members[k]['team_data'] = team_data[key]
    members = utilities.dict_to_json(members)
    query = "UPDATE groupme_yahoo SET members='"+json.dumps(members)+"' WHERE session=1;"
    db.execute_table_action(query)
    return members

def update_group_membership(client_data):
    string = 'None'
    if client_data['members']:
        league_bot = League_Bot.League_Bot(1)
        data = league_bot.get_league_data()
        teams = data['teams']['fantasy_content']['league'][1]['teams']
        team_data = fantasy.get_team_data(teams)
        for k, v in client_data['members'].items():
            logging.warn("K, V from client data: %s %s"% k, v)
            if team_data.get(v['team_id']):
                if client_data['members'][k]['team_data']['name'] is not team_data[v['team_id']]['name']:
                    string += client_data['members'][k]['name'] + 'changes team name to '+ team_data[v['team_id']]['name'] + "\n"
    return string