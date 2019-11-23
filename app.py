# RESOURCE: http://www.apnorton.com/blog/2017/02/28/How-I-wrote-a-Groupme-Chatbot-in-24-hours/


# IMPORTS
import os
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, request
import logging
import random
import League_Bot
import message as m

app = Flask(__name__)
bot_id = "70e9ad5bc50020fdb3a14dbca1"#"566e3b05b73cb551006cf34410"#
league_bot = None

def refresh():
	transaction_list = league_bot.get_transactions()
	# if transaction_list:
	# 	reply(format_transaction_list(transaction_list))

# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['POST'])
def webhook():
	# 'message' is an object that represents a single GroupMe message.
	message = request.get_json()
	global league_bot
	if not league_bot:
		league_bot = League_Bot.League_Bot()
		league_bot.init()
	league_bot.message_num  += 1
	print(league_bot.message_num, league_bot.message_limit)
	logging.debug("message: "+ message['text']+", "+str(league_bot.message_num)+" / "+str(league_bot.message_limit))
	if league_bot.message_num >= league_bot.message_limit and not sender_is_bot(message):
		league_bot.message_num = 0
		league_bot.message_limit = random.randint(15,30)
		reply(m.get_message(message['name']))

	if "initialize bot" in message['text'].lower():
		logging.debug("initializing")
		league_bot.init()

	return "ok", 200



@app.route('/')
def home():
	return 'Hello'

################################################################################

# Send a message in the groupchat
def reply(msg):
	url = 'https://api.groupme.com/v3/bots/post'
	data = {
		'bot_id'		: bot_id,
		'text'			: msg
	}
	request = Request(url, urlencode(data).encode())
	json = urlopen(request).read().decode()

# Send a message with an image attached in the groupchat
def reply_with_image(msg, imgURL):
	url = 'https://api.groupme.com/v3/bots/post'
	urlOnGroupMeService = upload_image_to_groupme(imgURL)
	data = {
		'bot_id'		: bot_id,
		'text'			: msg,
		'picture_url'		: urlOnGroupMeService
	}
	request = Request(url, urlencode(data).encode())
	json = urlopen(request).read().decode()
	
# Uploads image to GroupMe's services and returns the new URL
def upload_image_to_groupme(imgURL):
	imgRequest = requests.get(imgURL, stream=True)
	filename = 'temp.png'
	postImage = None
	if imgRequest.status_code == 200:
		# Save Image
		with open(filename, 'wb') as image:
			for chunk in imgRequest:
				image.write(chunk)
		# Send Image
		headers = {'content-type': 'application/json'}
		url = 'https://image.groupme.com/pictures'
		files = {'file': open(filename, 'rb')}
		payload = {'access_token': 'eo7JS8SGD49rKodcvUHPyFRnSWH1IVeZyOqUMrxU'}
		r = requests.post(url, files=files, params=payload)
		imageurl = r.json()['payload']['url']
		os.remove(filename)
		return imageurl

# Checks whether the message sender is a bot
def sender_is_bot(message):
	return message['sender_type'] == "bot"