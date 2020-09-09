import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import random
import logging
import json
import insults

def ad_hoc_message(msg, bot_id):
	if isinstance(msg,str):
		d ={"text" : msg, "bot_id" : bot_id}
		res = requests.post("https://api.groupme.com/v3/bots/post", data=d)
	return res

def get_message_loci(msg, user, user_id):
	start = msg.index(user)
	if start:
		end = start + len(user)
	#logging.warning("Loci are: " + start +" " +end])
	return [start, end]

# Send a message in the groupchat
def reply(msg, bot_id):
	url = 'https://api.groupme.com/v3/bots/post'
	data = {
		'bot_id'		: bot_id,
		'text'			: msg
	}
	request = Request(url, urlencode(data).encode())
	json = urlopen(request).read().decode()

def reply_with_mention(msg, user, user_id, bot_id):
	if "@" in msg:
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
	else:
		reply(msg, bot_id)

def get_message(user):
	user = "@"+user
	l = random.randint(0,100)
	if l > 90:
		insult = insults.self_aware[random.randint(0, len(insults.self_aware)-1)]
	elif l > 75:
		insult = insults.responses[random.randint(0, len(insults.responses)-1)]
	elif l > 65:
		insult = insults.responses[random.randint(0, len(insults.encouragement)-1)]
	else:
		m = insults.insults[random.randint(0,len(insults.insults)-1)]
		a = 'a'
		if m[0].lower() in ['a','e','i','o','u']:
			a = 'an'
		if " " not in m:
			m+= " " + insults.insults[random.randint(0,len(insults.insults)-1)]
		insult = user + " is "+a+" "+ m
	return insult

def talking_to_self(messages, lim=4):
	randomizer = random.randint(lim-1,lim+1) - lim
	lim += randomizer
	user = []
	first = messages[0][0]['sender_id']
	name = messages[0][0]['name']
	msg = ''
	for message in messages[len(messages)-lim:len(messages)]:
		#logging.warn("%s, %s"%(message, first))
		if isinstance(message[0], dict):
			user.append(message[0]['sender_id'])
	# logging.warn(user)
	if len(user) >= lim:
		for u in user:
			if str(u) != str(first):
				#logging.warn("u %s,f %s"%(u,first))
				return None
		msg = insults.talking_to_self[random.randint(0,len(insults.talking_to_self)-1)]
		if random.randint(0, 10) == 7:
			mention = insults.talking_to_self_with_mention[random.randint(0,len(insults.talking_to_self_with_mention)-1)]
			if isinstance(mention, tuple):
				msg = mention[0]+ str(name) + mention[1]
			else:
				msg=mention
	return msg

def talking_to_bot():
	return insults.mentions[random.randint(0,len(insults.mentions)-1)]

# Send a message with an image attached in the groupchat
# def reply_with_image(msg, imgURL):
# 	url = 'https://api.groupme.com/v3/bots/post'
# 	urlOnGroupMeService = upload_image_to_groupme(imgURL)
# 	data = {
# 		'bot_id'		: bot_id,
# 		'text'			: msg,
# 		'picture_url'		: urlOnGroupMeService
# 	}
# 	request = Request(url, urlencode(data).encode())
# 	json = urlopen(request).read().decode()
	
# Uploads image to GroupMe's services and returns the new URL
# def upload_image_to_groupme(imgURL):
# 	imgRequest = requests.get(imgURL, stream=True)
# 	filename = 'temp.png'
# 	postImage = None
# 	if imgRequest.status_code == 200:
# 		# Save Image
# 		with open(filename, 'wb') as image:
# 			for chunk in imgRequest:
# 				image.write(chunk)
# 		# Send Image
# 		headers = {'content-type': 'application/json'}
# 		url = 'https://image.groupme.com/pictures'
# 		files = {'file': open(filename, 'rb')}
# 		payload = {'access_token': 'eo7JS8SGD49rKodcvUHPyFRnSWH1IVeZyOqUMrxU'}
# 		r = requests.post(url, files=files, params=payload)
# 		imageurl = r.json()['payload']['url']
# 		os.remove(filename)
# 		return imageurl

# Checks whether the message sender is a bot
def sender_is_bot(message):
	val = True if (message['sender_type'] == "bot" or message['system']) else False
	return val
