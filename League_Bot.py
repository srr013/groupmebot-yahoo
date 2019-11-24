from yahoo_oauth import OAuth2
import json

class League_Bot():
    def __init__(self):
        self.oauth = OAuth2(None, None, from_file='oauth2yahoo.json')
        self.data = {}
        self.num_transactions_past = 0
        self.message_num = 0
        self.message_limit = 2

    def _login(self):
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()

    def init():
        self._login()
        self.get_data()
        self.set_transaction_total()
        print("transaction total: " +str(league_bot.num_transactions_past))
        logging.debug("transaction total: " +str(league_bot.num_transactions_past))
        return

    def build_url(self, req):
        base_url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
        sport = 'nfl'
        league_id = '186306'
        request = "/"+str(req)
        league_key = sport + '.l.'+ league_id 
        return str(base_url + league_key + request)
    
    def get_data(self):
        league = 12
        weeks = 10
        data = {}
        url_list = ['standings',
        'scoreboard', #;week='+str(week),
        'teams',
        'players',
        'transactions;types=add']
                #'.t.'+str(team)+'/roster;week='+str(week) ]

        for url in url_list:
            response = self.oauth.session.get(self.build_url(url), params={'format': 'json'})
            url = url.split(';')
            data[url[0]] = json.loads(response.text)
            #there's paging involved to get additional pages of data - players
            #data[url]['fantasy_content']['league'][0] - settings for that league
            #data[url]['fantasy_content']['league'][1][url] - url-related data fo


#'https://fantasysports.yahooapis.com/fantasy/v2/league/nfl.l.186306/season?format=json'

        self.data = data

        return

    def get_matchup_score(self, matchup):
        team_0 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][0]
        team_1 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][1]
        t0_id = team_0['team'][0][0].get(['team_key'])
        t0_name = team_0['team'][0][0].get(['team_name'])
        t0_current_score = team_0['team'][1]['team_points']['total']

    def set_transaction_total(self):
        self.num_transactions_past = self.data['transactions']['fantasy_content']['league'][1]['transactions'].__len__()

    def get_transactions(self):
        response = self.oauth.session.get(self.build_url('transactions;types=add'), params={'format': 'json'})
        self.data['transactions'] = json.loads(response.text)
        self.num_transactions = self.data['transactions']['fantasy_content']['league'][1]['transactions'].__len__()
        transaction_diff = self.num_transactions - self.num_transactions_past
        if transaction_diff > 0:
            i = 1
            trans_list = []
            while i <= transaction_diff:
                transaction = self.data['transactions']['fantasy_content']['league'][1]['transactions'][str(self.num_transactions_past+i)]
                player_name = transaction['0']['transaction'][1]['players'][0]['player'][0][2]['name']['full']
                team_name = transaction['0']['transaction'][1]['players'][0]['player'][1]['transaction_data'][0]['destination_team_name']
                trans_type = transaction['0']['transaction'][1]['players'][0]['player'][1]['transaction_data'][0]['type']
                string = team_name + " "+ trans_type +"s "+player_name
                trans_list.append(string)
                i += 1
        return trans_list
