import requests


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