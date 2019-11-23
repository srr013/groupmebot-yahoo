d ={"text" : "Good luck", "bot_id" : "70e9ad5bc50020fdb3a14dbca1"}

import requests

res = requests.post("https://api.groupme.com/v3/bots/post", data=d)