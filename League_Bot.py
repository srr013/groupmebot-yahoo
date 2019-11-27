from yahoo_oauth import OAuth2
import json
import logging
import db
import random

class League_Bot():
    def __init__(self, league_id):
        self.oauth = OAuth2(None, None, from_file='helpers/oauth2yahoo.json')
        self.league_id = league_id
        self.high = 13
        self.low = 11

    def _login(self):
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()
    
    def fetch_data(self):
        logging.debug("Fetching league data from DB")
        query = "SELECT * FROM groupme_yahoo WHERE session = 1"
        conn = db.initialize_connection()
        cursor = db.execute_table_action(conn, query)
        league_id,message_num,message_limit, past_transaction_num, league_data = cursor.fetchone()
        message_data = {'id': league_id, 'message_num':message_num, 
                    'message_limit': message_limit,
                    'transaction_num': past_transaction_num}
        logging.warning("Message Data: %i, %i, %i, %s" %  
        (league_id,message_num,message_limit, past_transaction_num))
        # if not league_data:
        #     league_data = self.get_league_data()
        conn.commit()
        conn.close()
        return message_data

    def initialize_bot(self):
        self._login()
        message_data = self.fetch_data()
        #league_data = self.get_league_data()
        return message_data

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
        url_list = ['transactions;types=add']
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
        #self.save_league_data(data)
        return data

    # def get_matchup_score(self, matchup):
    #     team_0 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][0]
    #     team_1 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][1]
    #     t0_id = team_0['team'][0][0].get(['team_key'])
    #     t0_name = team_0['team'][0][0].get(['team_name'])
    #     t0_current_score = team_0['team'][1]['team_points']['total']

    def get_transaction_total(self, data):
        return data['transactions']['fantasy_content']['league'][1]['transactions']["0"]['transaction'][0]['transaction_id']

    def get_transactions_list(self, data, past_trans_total):
        response = self.oauth.session.get(self.build_url('transactions;types=add'), params={'format': 'json'})
        data['transactions'] = json.loads(response.text)
        # with open('data.json', 'w') as d:
        #     d.write(json.dumps(data['transactions']))
        num_transactions = self.get_transaction_total(data)
        transaction_diff = int(num_transactions) - int(past_trans_total)
        logging.warning("Num transactions found: %s new / %s old" % (num_transactions, past_trans_total))
        trans_list = []
        if transaction_diff > 0:
            i = 1
            while i <= transaction_diff:
                trans = data['transactions']['fantasy_content']['league'][1]['transactions']
                for t in trans.keys():
                    if t == 'count':
                        continue
                    if trans[t]['transaction'][0]['transaction_id'] == str(past_trans_total+i):
                        players = trans[t]['transaction'][1]['players']
                        string = ''
                        for player in players.keys():
                            if player == 'count':
                                continue
                            #logging.warning("Player %s" % json.dumps(players[player]))
                            player_name = players[player]['player'][0][2]['name']['full']
                            if isinstance(players[player]['player'][1]['transaction_data'], list):
                                trans_type = players[player]['player'][1]['transaction_data'][0]['type']
                                if trans_type == 'drop':
                                    team_name = players[player]['player'][1]['transaction_data'][0]['source_team_name']
                                else:
                                    team_name = players[player]['player'][1]['transaction_data'][0]['destination_team_name']
                                string += team_name + " "+ trans_type +"s "+player_name+"\n"
                            else:
                                trans_type = players[player]['player'][1]['transaction_data']['type']
                                if trans_type == 'drop':
                                    team_name = players[player]['player'][1]['transaction_data']['source_team_name']
                                else:
                                    team_name = players[player]['player'][1]['transaction_data']['destination_team_name']                                                    
                                string += team_name + " "+ trans_type +"s "+player_name+"\n"
                        if string:
                            logging.warn(string)
                            trans_list.append(string)
                        i += 1
            logging.warning(trans_list)
            if trans_list:
                self.update_transaction_store(num_transactions)
        return trans_list

    def increment_message_num(self):
        logging.warning("Updating DB")
        query = "UPDATE groupme_yahoo SET message_num = message_num + 1 WHERE session = 1;"
        conn = db.initialize_connection()
        cursor = db.execute_table_action(conn, query)
        conn.commit()
        conn.close()
    
    def reset_message_data(self):
        global high, low
        logging.warning("Reseting Message Data in DB")
        lim = random.randint(self.low, self.high)
        query = "UPDATE groupme_yahoo SET message_num = 0, message_limit = "+str(lim)+" WHERE session = 1;"
        conn = db.initialize_connection()
        cursor = db.execute_table_action(conn, query)
        conn.commit()
        conn.close()
    
    def update_transaction_store(self, num_trans):
        query = "UPDATE groupme_yahoo SET num_past_transactions = "+num_trans+" WHERE session = 1;"
        conn = db.initialize_connection()
        cursor = db.execute_table_action(conn, query)
        conn.commit()
        conn.close()


    def save_league_data(self, data):
        data = json.dumps(data)
        data.strip("'")
        query = "UPDATE groupme_yahoo SET league_data = '"+data+"' WHERE session = 1;"
        conn = db.initialize_connection()
        cursor = db.execute_table_action(conn, query)
        conn.commit()
        conn.close()
