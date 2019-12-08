from yahoo_oauth import OAuth2
import json
import logging
import random
import db
import groupme
import utilities

#"70e9ad5bc50020fdb3a14dbca1", "test_bot_id": "566e3b05b73cb551006cf34410"

class GroupMe_Bot():
    def __init__(self):
        self.oauth = OAuth2(None, None, from_file='helpers/oauth2yahoo.json')
        self.high = 13
        self.low = 6
        self._login()

    def _login(self):
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()
    
    def create_group(self, group_id, bot_id):
        #does not set the bot_id for the group - manuually set this in order to post messages
        query = """INSERT INTO groupme_yahoo 
        (groupme_group_id, message_num, message_limit,
            num_past_transactions, league_data, 
            status, messaging_status, bot_id, members) 
            VALUES (%s,%i,%i,%i,%s,%i,%i,%s,%s);"""
        members = groupme.get_group_membership(group_id)
        values = (str(group_id),0,1,0,"{}",1,1,str(bot_id),utilities.dict_to_json(members))
        db.execute_table_action(query, values)

    
    def fetch_group_data(self, group_id):
        #groups: 32836424, 55536872
        logging.debug("Fetching league data from DB")
        if not group_id:
            group_id=1
        query = "SELECT * FROM groupme_yahoo WHERE groupme_group_id = "+str(group_id)
        cursor = db.execute_table_action(query, cur=True)
        results = cursor.fetchone()
        if results:
            message_num,message_limit, past_transaction_num, league_data, status, messaging_status, prd_bot_id, members,groupme_group_id, index = results
            group_data = {'index': index, 'message_num':message_num, 
                        'message_limit': message_limit,
                        'transaction_num': past_transaction_num,
                        'status': int(status), 'messaging_status': int(messaging_status),
                        'bot_id': prd_bot_id,
                        'groupme_group_id': groupme_group_id, 
                        'members': members}
            logging.warning("Messaging Trigger: %i / %i messages, Messaging Status: %i, Monitoring Status: %i (1 is On)"%
            (message_num,message_limit,messaging_status, status))
            # if not league_data:
            #     league_data = self.get_league_data()
            return group_data
        return False

    def get_group_data(self, group_id, bot_id):
        logging.warn("Getting Group Data for group %s"%(group_id))
        group_data = self.fetch_group_data(group_id)
        if not group_data and bot_id:
            logging.warn("Creating new group: %s /n" %(bot_id))
            self.create_group(group_id, bot_id)
            group_data = self.fetch_group_data(group_id)
        #league_data = self.get_league_data()
        return group_data

    def build_url(self, req):
        base_url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
        sport = 'nfl'
        league_id = '186306' #TODO: Manage multiple leagues 
        request = "/"+str(req)
        league_key = sport + '.l.'+ league_id 
        return str(base_url + league_key + request)
    
    def display_status(self):
        query = "SELECT * FROM groupme_yahoo"
        cursor = db.execute_table_action(query, cur=True)
        groups = cursor.fetchall()
        n = "___________"
        ID = "0"
        status = "" #need to configure a global status toggle
        init = "Global monitoring status: fake on" + status + n
        display = init
        new_display = ""
        for group in groups:
            g = self.get_group_data(group[8],'')
            ID = ""
            if isinstance(g['bot_id'], str):
                if len(g['bot_id'])>4:
                    ID = g['bot_id'][0:4]
            message = (
            "ID: ",ID,n,
            #"Group Name: ", g[''],n,
            "Bot Monitoring Status: ", "On" if g['status'] else "Off",#status
            n,"Bot Messaging Status: ","On" if g['messaging_status'] else "Off") #messaging_status
            for m in message:
                display += str(m)
            for k,v in g.items():
                new_display += str(k) + ": "
                new_display += str(v)
        return new_display

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
        #self.save_league_data(group_data['index'], data)
        return data

    # def get_matchup_score(self, matchup):
    #     team_0 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][0]
    #     team_1 = self.data['scoreboard']['fantasy_content']['league'][1]['scoreboard'][0]['matchups'][matchup][0]['teams'][1]
    #     t0_id = team_0['team'][0][0].get(['team_key'])
    #     t0_name = team_0['team'][0][0].get(['team_name'])
    #     t0_current_score = team_0['team'][1]['team_points']['total']


    def increment_message_num(self, group):
        query = "UPDATE groupme_yahoo SET message_num = message_num + 1 WHERE index = "+str(group)+";"
        db.execute_table_action(query)
    
    def reset_message_data(self, group):
        lim = random.randint(self.low, self.high)
        query = "UPDATE groupme_yahoo SET message_num = 0, message_limit = "+str(lim)+" WHERE index = "+str(group)+";"
        db.execute_table_action(query)
    
    
    def update_transaction_store(self, group, num_trans):
        query = "UPDATE groupme_yahoo SET num_past_transactions = "+num_trans+" WHERE index = "+str(group)+";"
        db.execute_table_action(query)
    


    def save_league_data(self, group, data):
        data = json.dumps(data)
        data.strip("'")
        query = "UPDATE groupme_yahoo SET league_data = '"+data+"' WHERE index = "+str(group)+";"
        db.execute_table_action(query)
    

