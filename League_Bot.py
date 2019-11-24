from yahoo_oauth import OAuth2
import json
import logging
import db
import random

class League_Bot():
    def __init__(self, league_id):
        self.oauth = OAuth2(None, None, from_file='helpers/oauth2yahoo.json')
        self.db = db.initialize_connection()
        self.league_id = league_id

    def _login(self):
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()
    
    def fetch_message_data(self):
        logging.debug("Fetching league data from DB")
        query = "SELECT * FROM groupme_yahoo WHERE session = 1"
        cursor = db.execute_table_action(self.db, query)
        league_id,message_num,message_limit, past_transaction_num = cursor.fetchone()
        message_data = {'id': league_id, 'message_num':message_num, 'message_limit': message_limit,
                    'transaction_num': past_transaction_num}
        logging.warning("Message Data: %i, %i, %i, %s" %  (league_id,message_num,message_limit, past_transaction_num))
        return message_data

    def initialize_bot(self):
        self._login()
        data = self.get_league_data()
        message_data = self.fetch_message_data()
        trans_total = message_data['transaction_num']
        trans_list = self.get_transactions_list(data, trans_total)
        return data, trans_list, message_data

    def build_url(self, req):
        base_url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
        sport = 'nfl'
        league_id = '186306'
        request = "/"+str(req)
        league_key = sport + '.l.'+ league_id 
        return str(base_url + league_key + request)
    
    def get_league_data(self):
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
        return data

    def get_matchup_score(self, matchup):
        team_0 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][0]
        team_1 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][1]
        t0_id = team_0['team'][0][0].get(['team_key'])
        t0_name = team_0['team'][0][0].get(['team_name'])
        t0_current_score = team_0['team'][1]['team_points']['total']

    def get_transaction_total(self, data):
        return data['transactions']['fantasy_content']['league'][1]['transactions'].__len__()

    def get_transactions_list(self, data, trans_total):
        response = self.oauth.session.get(self.build_url('transactions;types=add'), params={'format': 'json'})
        data['transactions'] = json.loads(response.text)
        num_transactions = data['transactions']['fantasy_content']['league'][1]['transactions'].__len__()-1
        transaction_diff = num_transactions - trans_total
        logging.warning("Num transactions found: %i" % num_transactions)
        trans_list = []
        if transaction_diff > 0:
            i = 1
            while i <= transaction_diff:
                transaction = data['transactions']['fantasy_content']['league'][1]['transactions'][str(trans_total+i)]
                player_name = transaction['0']['transaction'][1]['players'][0]['player'][0][2]['name']['full']
                team_name = transaction['0']['transaction'][1]['players'][0]['player'][1]['transaction_data'][0]['destination_team_name']
                trans_type = transaction['0']['transaction'][1]['players'][0]['player'][1]['transaction_data'][0]['type']
                string = team_name + " "+ trans_type +"s "+player_name
                trans_list.append(string)
                i += 1
        return trans_list

    def increment_message_num(self):
        logging.warning("Updating DB")
        query = "UPDATE groupme_yahoo SET message_num = message_num + 1 WHERE session = 1"
        cursor = db.execute_table_action(self.db, query)
    
    def reset_message_data(self):
        logging.warning("Reseting Message Data in DB")
        lim = random.random(15,25)
        query = "UPDATE groupme_yahoo SET message_num = 0, message_limit = "+str(lim)+" WHERE session = 1"        
        cursor = db.execute_table_action(self.db, query)