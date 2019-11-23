# RESOURCE: http://www.apnorton.com/blog/2017/02/28/How-I-wrote-a-Groupme-Chatbot-in-24-hours/


# IMPORTS
import os
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, request
import logging
import random

app = Flask(__name__)
bot_id = "566e3b05b73cb551006cf34410"
message_num = 0
message_limit = 25

# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['POST'])
def webhook():
	# 'message' is an object that represents a single GroupMe message.
	message = request.get_json()
	global message_num
	global message_limit
	message_num  += 1
	print(message_num, message_limit)
	if message_num >= message_limit:
		message_num = 0
		message_limit = random.randint(25,40)
		reply(get_message(message['name']))

	return "ok", 200

def get_message(user):
	lead_in = ["Bleep bloop bleep. "+user+ " is", "Congratulations "+user+" you are ", "My calculations have revealed that "+user]
	messages = {
	0 : ['idiotic', 'dumber than a sack of potatoes', 'as insightful as Jim Jordan',
	 "... well let's just say bless your heart", "as good as 3 day old egg salad", "clearly a joke", 
	 "reminiscient of nothing memorable", "nevermind. Go f yaself", "actually a Republican talking point"],
	1 : ["smarter than expected", "amazing", "insightful and heartwarming",
	 "probably better than I could've done", "not dumb", "better than average", "pretty good!"]
	}
	m = random.randint(0,1)
	message = messages[m][random.randint(0, len(messages[m]))-1]
	lead = lead_in[random.randint(0,len(lead_in))-1]
	msg = lead + message
	return msg

@app.route('/')
def home():
	return 'Hello World!'

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

if __name__ == '__main__':
	app.run()