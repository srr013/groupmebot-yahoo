import json
from yahoo_oauth import OAuth2
import utilities

def build_url(req):
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
    sport = 'nfl'
    league_id = '186306'
    request = "/"+str(req)
    league_key = sport + '.l.'+ league_id 
    return str(base_url + league_key + request)

def get_league_data(oauth):
    league = 12
    weeks = 10
    data = {}
    url_list = ['teams','transactions;types=add']
            #'standings','scoreboard',
            # ;week='+str(week),,'players',
            #'.t.'+str(team)+'/roster;week='+str(week) ]

    for url in url_list:
        response = oauth.session.get(build_url(url), params={'format': 'json'})
        url = url.split(';')
        data[url[0]] = json.loads(response.text)
    return data


# oauth = OAuth2(None, None, from_file='helpers/oauth2yahoo.json')
# data = get_league_data(oauth)
# print(data)

def get_team_data(teams):
    team_data = {}
    for t, val in teams.items():
        if t == 'count':
            continue
        logging.warn("Val from get_team_data: %s"% utilities.dict_to_json(val))
        for k, v in val.items():
            logging.warn("k,v from get_team_data: %s, %s"% (k,v))
            if k == 'count':
                continue
            team_id = ''
            name = ''
            num_moves = 0
            num_trades = 0
            if k == 'name':
                name = v
            elif k == 'number_of_moves':
                num_moves = v
            elif k == 'number_of_trades':
                num_trades = v
            elif k == 'team_key':
                team_id = v
        if team_id:
            team_data[team_id] = {'name': name, 'num_moves': num_moves, 'num_trades': num_trades}
    return team_data
