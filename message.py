import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import random
import logging
import json
import insults

def ad_hoc_message(msg,id):
	if isinstance(msg,str):
		d ={"text" : msg, "bot_id" : id}
		res = requests.post("https://api.groupme.com/v3/bots/post", data=d)
	return res

def get_message_loci(msg, user, user_id):
	start = msg.index(user)
	if start:
		end = start + len(user)
	#logging.warning("Loci are: " + start +" " +end])
	return [start, end]

def reply_with_mention(msg, user, user_id, bot_id):
	loci = get_message_loci(msg, user, user_id)
	d = {'bot_id': bot_id,
    		'text': msg,
	    	'attachments': [
                {"type": "mentions",
                "loci": [loci],
                "user_ids": [user_id]}
            ]
	    }
	logging.warn(json.dumps(d))
	url = "https://api.groupme.com/v3/bots/post"
	resp = requests.post(url, json=d)

def get_message(user):
	user = "@"+user
	# lead_in = ["Bleep bloop bleep. "+user+ " is ", "Congratulations "+user+" you are ", 
	# "My calculations have revealed that "+user+" is ", "I heard that "+user+" is "]
	# messages = {
	# 0 : ['idiotic', 'dumber than a sack of potatoes', 'only valuable in the sack', "a straight up moron",
	#  "... well let's just say bless your heart", "as good at Fantasy Football as Owen Reese", "the human form of a bad joke", 
	#  "reminiscent of nothing memorable", "...nevermind. Go f yaself", "as factually inaccurate as a Republican talking point",
	#  "not worth the time it took to write this. Dumbass.", "fishier than Hillary Clinton's underpants on a hot day"],
	# 1 : ["smarter than expected", "amazing", "insightful and heartwarming", "attractive",
	#  "probably better than I could've done", "actually not that dumb", "a bit better than average", "a pro",
	#  "as beautiful and talented as Tom Brady", "the Gordon Ramsey of Fantasy Footballers"]
	# }
	insult_list = insults.insults
	m = insult_list[random.randint(0,len(insult_list)-1)]
	a = 'a'
	if m[0].lower() in ['a','e','i','o','u']:
		a = 'an'
	if " " not in m:
		m+= " " + insult_list[random.randint(0,len(insult_list)-1)]
	# message = messages[m][random.randint(0, len(messages[m]))-1]
	# lead = lead_in[random.randint(0,len(lead_in))-1]
	# msg = lead + message
	msg = user + " is "+a+" "+ m
	return msg

# Send a message in the groupchat
def reply(msg, bot_id):
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


