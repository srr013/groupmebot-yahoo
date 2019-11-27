import json
from yahoo_oauth import OAuth2

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
    url_list = ['transactions;types=add']
            #'standings','scoreboard',
            # ;week='+str(week),'teams','players',
            #'.t.'+str(team)+'/roster;week='+str(week) ]

    for url in url_list:
        response = oauth.session.get(build_url(url), params={'format': 'json'})
        url = url.split(';')
        data[url[0]] = json.loads(response.text)
    return data


oauth = OAuth2(None, None, from_file='helpers/oauth2yahoo.json')
data = get_league_data(oauth)
print(data)
