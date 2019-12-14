import os
import psycopg2
import logging

def initialize_connection():
    if os.environ.get('DATABASE_URL'):
        DATABASE_URL = os.environ['DATABASE_URL']
    else:
        DATABASE_URL = "postgres://rswaqrlbkxjsfa:0c3ee7e18e714bf25194dc29a01eee1ba01dcfe658f2e670adbdd0ce12119984@ec2-23-21-115-109.compute-1.amazonaws.com:5432/d3dp6ua6pc73gn"

        logging.error("No DB URL set in environment. (Local) Run set DATABASE_URL=postgres://$(whoami)")

    # conn = psycopg2.connect("dbname='template1' user='dbuser' host='localhost' password='dbpass'")
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def execute_table_action(query, values = ()):
    conn = initialize_connection()
    cursor = conn.cursor()
    if not values:
        cursor.execute(query)
    else:
        cursor.execute(query, values)
    conn.commit()
    conn.close()

def fetch_all(query, values = ()):
	conn = initialize_connection()
	cursor = conn.cursor()
	if not values:
		cursor.execute(query)
	else:
		cursor.execute(query, values)
	l = cursor.fetchall()
	conn.commit()
	conn.close()
	return l

def fetch_one(query, values = ()):
	conn = initialize_connection()
	cursor = conn.cursor()
	if not values:
		cursor.execute(query)
	else:
		cursor.execute(query, values)
	l = cursor.fetchone()
	conn.commit()
	conn.close()
	return l

table_model = """
groupme_group_id INTEGER, 
message_num INTEGER, 
message_limit INTEGER,
num_past_transactions INTEGER,
status BOOLEAN,
messaging_status BOOLEAN,
bot_id VARCHAR(200),
members VARCHAR(MAX),
index SERIAL PRIMARY KEY, 
anchor_datetime TIMESTAMP,
trigger BOOLEAN

"""

create_table = """
CREATE TABLE groupme_yahoo(message_num, message_limit, 
num_past_transactions, status, messaging_status, bot_id, members, groupme_group_id, index);
"""
app_status = """CREATE TABLE application_data(monitoring_status BOOLEAN, messaging_status BOOLEAN);"""

drop_table = """
DROP TABLE 
"""
insert_into = """
INSERT INTO groupme_yahoo(group_id, message_num, message_limit, 
num_past_transactions, league_data, status, messaging_status, bot_id) 
VALUES
    ();
"""
serial = """ALTER TABLE groupme_yahoo ADD COLUMN index SERIAL PRIMARY KEY;"""

select = """
SELECT * FROM groupme_yahoo
"""
add = """
ALTER TABLE groupme_yahoo ADD COLUMN status INTEGER, 
bot_status INTEGER, prd_bot VARCHAR(100), test_bot VARCHAR(200);
"""
#works from CLI, not debug

update = """
UPDATE groupme_yahoo SET status, bot_status, WHERE group_id=1;
"""
