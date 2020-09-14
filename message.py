import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import random
import logging
import json
import insults
import os

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
def send_message(msg, bot_id):
	url = 'https://api.groupme.com/v3/bots/post'
	data = {
		'bot_id'		: bot_id,
		'text'			: msg
	}
	request = Request(url, urlencode(data).encode())
	json = urlopen(request).read().decode()

def send_with_mention(msg, user, user_id, bot_id):
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

#Send a message with an image attached in the groupchat
def send_with_image(bot_id, img):
	url = 'https://api.groupme.com/v3/bots/post'
	urlOnGroupMeService = upload_image_to_groupme(img)
	data = {
		'bot_id'		: bot_id,
		'text'			: '',
		'picture_url'		: urlOnGroupMeService['payload']['url']
	}
	res = requests.post(url, data=data)
	return res

	
#Uploads image to GroupMe's services and returns the new URL
def upload_image_to_groupme(filename):
	headers = {'Content-Type': 'image/jpeg',
				'X-Access-Token': os.environ.get("GM_ACCESS_TOKEN")}
	url = 'https://image.groupme.com/pictures'
	data = open(filename, 'rb').read()
	r = requests.post(url, headers=headers, data=data)
	imageurl = json.loads(r.text)
	return imageurl

def get_message(user, insult_type):
	logging.warn("insult type: %s"%(insult_type))
	user = "@"+user
	l = 0
	if not insult_type:
		l = random.randint(0,100)
	msg_type = 'reply'
	msg = ''
	if l > 90 or insult_type=='self-aware':
		msg = insults.self_aware[random.randint(0, len(insults.self_aware)-1)]
	elif l > 75 or insult_type=='response':
		msg = insults.responses[random.randint(0, len(insults.responses)-1)]
	elif l > 60 or insult_type=='encouragement':
		msg = insults.encouragement[random.randint(0, len(insults.encouragement)-1)]
	elif l > 40 or insult_type=='image':
		msg = "static\\memes\\" + insults.meme_files[random.randint(0, len(insults.meme_files)-1)]
		msg_type = 'image'
	else:
		msg_type = 'mention'
		m = insults.insults[random.randint(0,len(insults.insults)-1)]
		a = 'a'
		if m[0].lower() in ['a','e','i','o','u']:
			a = 'an'
		if random.randint(0, 99) > 50:
			if " " not in m:
				m+= " " + insults.insults[random.randint(0,len(insults.insults)-1)]
			msg = user + " is "+a+" "+ m
		else:
			msg = user + " is "+a+" "+ m
	return msg, msg_type

def talking_to_self(messages, lim=4):
	messages.sort(key=lambda t: t['index'])
	randomizer = random.randint(lim-1,lim+1) - lim
	lim += randomizer
	user = []
	first = messages[0]['message_object']['sender_id']
	name = messages[0]['message_object']['name']
	msg = ''
	msg_type = 'reply'
	proceed = True
	#store the sender of the last <lim> messages to a list
	for message in messages[len(messages)-lim:len(messages)]:
		#logging.warn("%s, %s"%(message, first))
		if isinstance(message['message_object'], dict):
			user.append(message['message_object']['sender_id'])
	# logging.warn(user)
	#if there are enough messages in <user> check if the sender ID is the same on all
	if len(user) >= lim:
		for u in user:
			if str(u) != str(first):
				proceed = False
		#send a response if the user is the same
		if proceed:
			#use a mention-based message sometimes
			if random.randint(0, 10) == 7:
				msg_type = 'mention'
				mention = insults.talking_to_self_with_mention[random.randint(0,len(insults.talking_to_self_with_mention)-1)]
				if isinstance(mention, tuple):
					msg = mention[0]+' @'+ str(name) + ' '+ mention[1]
				else:
					msg = mention+' @'+ str(name)
			else:
				msg = insults.talking_to_self[random.randint(0,len(insults.talking_to_self)-1)]
	return msg, msg_type

def talking_to_bot():
	return insults.mentions[random.randint(0,len(insults.mentions)-1)]

# Checks whether the message sender is a bot
def sender_is_bot(message):
	val = True if (message['sender_type'] == "bot" or message['system']) else False
	return val
