from yahoo_oauth import OAuth2
import json
import logging
import db
import groupme
import random

#"70e9ad5bc50020fdb3a14dbca1", "test_bot_id": "566e3b05b73cb551006cf34410"

class GroupMe_Bot():
    def __init__(self, league_id):
        self.oauth = OAuth2(None, None, from_file='helpers/oauth2yahoo.json')
        self.league_id = league_id
        self.high = 13
        self.low = 6
        self._login()

    def _login(self):
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()
    
    def create_group(self, group_id):
        #does not set the bot_id for the group - manuually set this in order to post messages
        query = """INSERT INTO groupme_yahoo (group_id, message_num, message_limit,
            num_past_transactions, league_data, status, messaging_status, bot_id, members) 
            VALUES (?,0,2,0,'{}',1,0,'0');"""
        members = groupme.get_group_membership(group_id)
        values = (group_id, members)
        db.execute_table_action(query, values)

    
    def fetch_data(self, group):
        logging.debug("Fetching league data from DB")
        query = "SELECT * FROM groupme_yahoo WHERE group_id = "+group
        cursor = db.execute_table_action(query, cur=True)
        league_id,message_num,message_limit, past_transaction_num, league_data, status, messaging_status, prd_bot_id, test_bot_id, members = cursor.fetchone()
        group_data = {'id': league_id, 'message_num':message_num, 
                    'message_limit': message_limit,
                    'transaction_num': past_transaction_num,
                    'status': int(status), 'messaging_status': int(messaging_status),
                    'bot_id': prd_bot_id, 
                    'members': members}
        logging.warning("Client Data: %i / %i messages, Bot group: %i (1 is PRD), Active status: %i (1 is active)"%
        (message_num,message_limit,messaging_status, status))
        # if not league_data:
        #     league_data = self.get_league_data()
        return group_data

    def get_group_data(self, group_id):
        group_data = self.fetch_data(group_id)
        if not group_data:
            logging.warn("Creating new group: %s /n" %(group_data['id']))
            self.create_group(group_id)
            group_data = self.fetch_data(group_id)
        #league_data = self.get_league_data()
        return group_data

    def build_url(self, req):
        base_url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
        sport = 'nfl'
        league_id = '186306'
        request = "/"+str(req)
        league_key = sport + '.l.'+ league_id 
        return str(base_url + league_key + request)
    
    def display_status(self):
        query = "SELECT * FROM groupme_yahoo"
        cursor = db.execute_table_action(query, cur=True)
        groups = cursor.fetchall()
        n = "/n"
        ID = ""
        status = "" #need to configure a global status toggle
        init = "Global monitoring status: fake on" + status + n
        display = ""
        for group in groups:
            if isinstance(group[6], str):
                ID = group[6][0:4]
            else:
                ID = ""
            message = (
            "ID: ",ID,n,
            "Group Name: ", group[0],n,
            "Bot Monitoring Status: ", group[4],#status
            n,"Bot Messaging Status: ",n,group[5],n) #bot_status
            for m in n:
                display += str(m)
        return display

    def get_league_data(self):
        league = 12
        weeks = 10
        data = {}
        url_list = ['teams','transactions;types=add']
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


    def increment_message_num(self, group):
        query = "UPDATE groupme_yahoo SET message_num = message_num + 1 WHERE group_id = "+int(group)+";"
        db.execute_table_action(query)
    
    def reset_message_data(self, group):
        lim = random.randint(self.low, self.high)
        query = "UPDATE groupme_yahoo SET message_num = 0, message_limit = "+str(lim)+" WHERE group_id = "+int(group)+";"
        db.execute_table_action(query)
    
    
    def update_transaction_store(self, group, num_trans):
        query = "UPDATE groupme_yahoo SET num_past_transactions = "+num_trans+" WHERE group_id = "+int(group)+";"
        db.execute_table_action(query)
    


    def save_league_data(self, group, data):
        data = json.dumps(data)
        data.strip("'")
        query = "UPDATE groupme_yahoo SET league_data = '"+data+"' WHERE group_id = "+int(group)+";"
        db.execute_table_action(query)
    

