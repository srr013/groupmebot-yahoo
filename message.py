import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def ad_hoc_message(msg):
    if isinstance(msg,str):
        d ={"text" : msg, "bot_id" : "70e9ad5bc50020fdb3a14dbca1"}
    res = requests.post("https://api.groupme.com/v3/bots/post", data=d)

    return res

def get_message(user):
	lead_in = ["Bleep bloop bleep. "+user+ " is ", "Congratulations "+user+" you are ", 
	"My calculations have revealed that "+user+" is ", "I heard that "+user+" is "]
	messages = {
	0 : ['idiotic', 'dumber than a sack of potatoes', 'only valuable in the sack', "a straight up moron",
	 "... well let's just say bless your heart", "as good at Fantasy Football as Owen Reese", "the human form of a bad joke", 
	 "reminiscent of nothing memorable", "...nevermind. Go f yaself", "as factually inaccurate as a Republican talking point",
	 "not worth the time it took to write this. Dumbass.", "fishier than Hillary Clinton's underpants on a hot day"],
	1 : ["smarter than expected", "amazing", "insightful and heartwarming", "attractive",
	 "probably better than I could've done", "not dumb", "better than average", "a pro",
	 "as beautiful and talented as Tom Brady", "the Gordon Ramsey of Fantasy Footballers"]
	}
	m = random.randint(0,1)
	message = messages[m][random.randint(0, len(messages[m]))-1]
	lead = lead_in[random.randint(0,len(lead_in))-1]
	msg = lead + message
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