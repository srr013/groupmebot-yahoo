import json
from yahoo_oauth import OAuth2
import utilities
import logging
import message as m


def build_url(req):
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
    sport = 'nfl'
    league_id = '186306'
    request = "/"+str(req)
    league_key = sport + '.l.' + league_id
    return str(base_url + league_key + request)

def get_league_data(oauth):
    league = 12
    weeks = 10
    data = {}
    url_list = ['teams', 'transactions;types=add','scoreboard']
    # 'standings','scoreboard',
    # ;week='+str(week),,'players',
    # '.t.'+str(team)+'/roster;week='+str(week) ]

    for url in url_list:
        response = oauth.session.get(build_url(url), params={'format': 'json'})
        url = url.split(';')
        data[url[0]] = json.loads(response.text)
	
    return data

def parse_league_data(group_data, data):
	

def append_league_data(group_data, oauth):
	data = get_league_data(oauth)
	group_data['league'] = parse_league_data(group_data, data)

def get_team_data(teams):
    team_data = {}
    for t, val in teams.items():
        if t == 'count':
            continue
        # logging.warn("Val from get_team_data: %s" %
        #              utilities.dict_to_json(val))
        td = val['team'][0]
        team_id = ''
        name = ''
        num_moves = 0
        num_trades = 0
        for entry in td:
            # try:
            #     logging.warn("Entry: %s"%(utilities.dict_to_json(entry)))
            # except:
            #     pass
            if isinstance(entry, dict):
                for k, v in entry.items():
                    if k == 'count':
                        continue
                    elif k == 'name':
                        name = v
                    elif k == 'number_of_moves':
                        num_moves = v
                    elif k == 'number_of_trades':
                        num_trades = v
                    elif k == 'team_key':
                        team_key = v
                    elif k == 'team_id':
                        team_id = v
        if team_id:
            team_data[team_id] = {
                'name': name, 'num_moves': num_moves,
                'num_trades': num_trades, 'team_key': team_key}
    logging.warn("Team Data output: %s" % utilities.dict_to_json(team_data))
    return team_data


"""
{'team': 
[
    [{'team_key': '390.l.186306.t.12'}, {'team_id': '12'}, {'name': 'FFB Fournography'}, [], 
    {'url': 'https://football.fantasysports.yahoo.com/f1/186306/12'}, 
    {'team_logos': [{'team_logo': {'size': 'large', 'url': 'https://s.yimg.com/cv/apiv2/default/nfl/nfl_12.png'}}]}, 
    [], 
    {'waiver_priority': 6}, [], {'number_of_moves': '36'}, {'number_of_trades': '1'}, 
    {'roster_adds': {'coverage_type': 'week', 'coverage_value': 13,'value': '3'}}, 
    {'clinched_playoffs': 1}, {'league_scoring_type': 'head'}, [], [], 
    {'has_draft_grade': 1, 'draft_grade': 'B+', 'draft_recap_url': 'https://football.fantasysports.yahoo.com/f1/186306/12/draftrecap'}, 
    [], [], {'managers': [{'manager': {'manager_id': '12', 'nickname': 'Steve', 'guid': 'NX5WSOP6KRPWEGJ44JJJ3KLYBI', 
    'image_url': 'https://s.yimg.com/ag/images/default_user_profile_pic_64sq.jpg'}}]}]]}
"""


def get_transaction_total(data):
    return data['transactions']['fantasy_content']['league'][1]['transactions']["0"]['transaction'][0]['transaction_id']


def get_transaction_list(data, past_trans_total):
    num_transactions = get_transaction_total(data)
    transaction_diff = int(num_transactions) - int(past_trans_total)
    trans_list = []
    trans = data['transactions']['fantasy_content']['league'][1]['transactions']
    tl = [t for t in trans.keys()]
    i=0
    for t in tl[0:transaction_diff]:
        i+=1
        if t == 'count':
            continue
            #if trans[t]['transaction'][0]['transaction_id'] == str(past_trans_total+i):
            #logging.warn("Key located")
        players = trans[t]['transaction'][1]['players']
        string = str(i)+'. '
        count = 0
        for player in players.keys():
            #logging.warn("player located")
            if player == 'count':
                continue
            #logging.warning("Player %s" % json.dumps(players[player]))
            count += 1
            player_name = players[player]['player'][0][2]['name']['full']
            if isinstance(players[player]['player'][1]['transaction_data'], list):
                trans_type = players[player]['player'][1]['transaction_data'][0]['type']
                if trans_type == 'drop':
                    team_name = players[player]['player'][1]['transaction_data'][0]['source_team_name']
                else:
                    team_name = players[player]['player'][1]['transaction_data'][0]['destination_team_name']
                string += team_name + " " + trans_type + "s "+player_name+"\n"
            else:
                trans_type = players[player]['player'][1]['transaction_data']['type']
                if trans_type == 'drop':
                    team_name = players[player]['player'][1]['transaction_data']['source_team_name']
                else:
                    team_name = players[player]['player'][1]['transaction_data']['destination_team_name']
                if count == 1:
                    string += team_name + " " + trans_type + "s "+player_name+"\n"
                else:
                    string += "and " + trans_type + "s "+player_name+"\n"
        if string:
                trans_list.append(string)
    return trans_list

    # def get_matchup_score(self, data, matchup):
	# 	matchup = {}
    #     team_0 = data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][0]
    #     team_1 = data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][1]
	# 	#t0_id = team_0['team'][0][0].get(['team_key'])
    #     t0_name = team_0['team'][0][0].get(['team_name'])
    #     t0_current_score = team_0['team'][1]['team_points']['total']