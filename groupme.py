import requests
import json
import logging
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
    db.execute_table_action(query)
    return members

def update_group_membership(client_data):
    string = 'None'
    if client_data['members']:
        league_bot = League_Bot.League_Bot(1)
        data = league_bot.get_league_data()
        logging.warn("data: %s" % utilities.dict_to_json(data))
        teams = data['teams']['fantasy_content']['league'][1]['teams']
        logging.warn("teams: %s" % utilities.dict_to_json(teams))
        team_data = fantasy.get_team_data(teams)
        for k, v in client_data['members'].items():
            logging.warn("K, V from client data: %s %s %s" % (k, v, json.dumps(team_data)))
            if team_data.get(v['team_id']):
                if client_data['members'][k]['team_data']['name'] is not team_data[v['team_id']]['name']:
                    string += client_data['members'][k]['name'] + 'changes team name to '+ team_data[v['team_id']]['name'] + "\n"
            client_data['members'][k]['team_data'] = team_data[v['team_id']]
    query = "UPDATE groupme_yahoo SET members="+utilities.dict_to_json(client_data['members'])+"WHERE session=1;"
    db.execute_table_action(query)
    return string