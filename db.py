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

create_table = """
CREATE TABLE groupme_yahoo(
session INTEGER,
message_num INTEGER,
message_limit INTEGER
);
"""
drop_table = """
DROP TABLE 
"""
insert_into = """
INSERT INTO groupme_yahoo (session, message_num, message_limit, num_past_transactions)
VALUES (1,0,30);
"""
select = """
SELECT * FROM groupme_yahoo
"""
add = """
ALTER TABLE groupme_yahoo ADD COLUMN num_past_transactions INTEGER;
"""
#works from CLI, not debug

update = """
UPDATE groupme_yahoo SET num_past_transactions=393 WHERE session=1;
"""

def execute_table_action(conn, sql_string):
    cursor = conn.cursor()
    cursor.execute(sql_string)
    return cursor
