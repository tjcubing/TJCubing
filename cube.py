import json, pickle, time, os, secrets
from datetime import datetime
import requests
import flask
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from bs4 import BeautifulSoup

# Helper library to query the WCA for competitions and other miscellaneous tasks
# TODO: mailing list, switch key to key from tjcubingofficers@gmail.com
# TODO: Voting system

STR_FUNC = {"load": {"json": json.load, "pickle": pickle.load}, "dump": {"json": json.dump, "pickle": pickle.dump}}
FUNC_EXT = {json.load: ".json", json.dump: ".json", pickle.load: ".pickle", pickle.dump: ".pickle"}
EXT_MODE = {".json": "", ".pickle": "b"}

def load_file(fname: str, func="json") -> dict:
    """ Loads a file. """
    func = STR_FUNC["load"][func]
    ext = FUNC_EXT[func]
    with open(fname + ext, "r" + EXT_MODE[ext]) as f:
        return func(f)

def dump_file(obj, fname: str, func="json") -> None:
    """ Dumps an obj into a file. """
    func = STR_FUNC["dump"][func]
    ext = FUNC_EXT[func]
    with open(fname + ext, "w" + EXT_MODE[ext]) as f:
        func(obj, f, **({"index": 4} if func == json.dump else {}))

config = load_file("config")
URL = "https://www.worldcubeassociation.org/competitions"
LECTURES = "static/pdfs/"
FILE = ".html.j2"
PREVIEW = 80
WAIT = 2.628e6 #seconds in a month

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #turn off when it's legit, localhost is http
ION = "https://ion.tjhsst.edu/"
AUTHORIZATION_URL, TOKEN_URL = ION + "oauth/authorize/", ION + "oauth/token/"

def gen_secret_key() -> str:
    """ Generates a random secret key. """
    return secrets.token_hex(16)

def unix_to_human(time: float) -> str:
    """ Returns a human-readable time from a UNIX timestamp. """
    return datetime.fromtimestamp(time).strftime("%A, %B %d, %Y at %I:%M:%S.%f %p")

def make_soup(url: str, params={}) -> BeautifulSoup:
    """ Returns a soup from a url. """
    return BeautifulSoup(requests.get(url, params=params).text, 'html.parser')

#TODO: get events, TJ kids competing.
def get_comps() -> list:
    """ Parses the WCA website and returns a list of competitors.
        Calls Google's distancematrix API to get distances to the competitions
    """
    comps = []
    soup = make_soup(URL, {"region": "USA", "state": "present", "display": "list"})
    for comp in soup("li", class_="list-group-item not-past"):
        info = list(filter(lambda x: x != len(x)*" ", comp.get_text().strip().split("\n")))
        if info[2].split(", ")[-1] in config["states"]:
            temp = {"url": URL + comp.find("a").get('href')[13:],
                    "name": info[1],
                    "location": info[2],
                    "venue": info[3],
                    "date": info[0],
                   }
            subsoup = make_soup(temp["url"])
            temp["gps"] = subsoup.find("dt", string="Address").next_sibling.next_sibling.find("a").get('href').split("/")[-1]
            comps.append(temp)

    param = {'origins': config["origin"], 'destinations': "|".join([comp["gps"] for comp in comps]), 'key': config["key"], 'units': 'imperial'}

    for i, thing in enumerate(requests.get("https://maps.googleapis.com/maps/api/distancematrix/json", params=param).json()['rows'][0]['elements']):
        comps[i]["mi"] = thing['distance']['text']
        comps[i]["timestr"] = thing['duration']['text']
        comps[i]["time"] = thing['duration']['value']

    #TODO: sort by user-determined feature
    comps.sort(key=lambda comp: comp["time"]) #sort by time to travel
    dump_file((time.time(), comps), "comps", "pickle")

    return comps

def get_lectures() -> list:
    """ Returns a list of past lectures. """
    lectures = []
    for lecture in os.listdir(LECTURES):
        if os.path.isdir(LECTURES + lecture):
            with open(LECTURES + lecture + "/desc.txt") as f:
                lines = f.readlines()
            lectures.append({line.split(":")[0]: ":".join(line.split(":")[1:]).strip() for line in lines})

    lectures.sort(key=lambda l: datetime.strptime(l["date"], "%m/%d/%Y")) #sort by date
    return lectures

def get_preview(query: str, text: str) -> str:
    """ Returns a preview of a larger string from a smaller string. """
    i = text.lower().index(query)
    preview = text[max(i - PREVIEW, 0):min(i + PREVIEW, len(text) - 1)] #avoid out of bounds
    return " ".join(preview.split()[1:-1]) #removes fractions of words

def parse_search(query: str) -> list:
    """ Parses a user's search, returns a list of entries. """
    query = query.strip().lower()
    for html in os.listdir("templates/"):
        if html[-len(FILE):] == FILE:
            soup = BeautifulSoup(open(f"templates/{html}").read(), 'html.parser')
            text = soup.get_text()
            if query in text.lower():
                yield (unix_to_human(os.path.getmtime(f"templates/{html}")), html if html != "index" + FILE else FILE, get_preview(query, text))

def make_oauth(**kwargs) -> OAuth2Session:
    """ Makes an OAuth2Session session. Should auto-refresh. """
    args = {"client_id": config["client_id"], "client_secret": config["client_secret"]}
    return OAuth2Session(config["client_id"], redirect_uri=config["redirect_uri"], scope=["read"], auto_refresh_url=TOKEN_URL, auto_refresh_kwargs=args, **kwargs)

def make_api_call(oauth: OAuth2Session, call: str, short=True) -> dict:
    """ Makes an API call and returns a dictionary. """
    return json.loads(oauth.get(ION + f"api/{call}" if short else call).content.decode())

def save_token(token: dict) -> None:
    """ Saves a token to Flask. """
    flask.session["token"] = token

def get_club_result(oauth: OAuth2Session) -> list:
    """ Returns the club's page. """
    d = make_api_call(oauth, "activities")
    while "next" in d and d["next"] is not None:
        for result in d["results"]:
            if "cube" in result["name"].lower():
                return result
        d = make_api_call(oauth, d["next"], False)

#TODO: some sort of legit method of updating these beyond func calls
#TODO: Admin page to do that

def save_club_history(oauth: OAuth2Session) -> dict:
    """ Returns the ION page describing the club. """
    dump_file(make_api_call(oauth, config["club"]["url"], False), f)

def get_activities(oauth: OAuth2Session) -> list:
    """ Returns all of the user's activities. """
    return

# <?php
# // Check for empty fields
# if(empty($_POST['name'])  		||
#    empty($_POST['email'])	||
#    !filter_var($_POST['email'],FILTER_VALIDATE_EMAIL))
#    {
# 	echo "No arguments Provided!";
# 	return false;
#    }
#
# $name = $_POST['name'];
# $email_address = $_POST['email'];
#
# // Create the email and send the message
# $to = 'davidzhao058@gmail.com'; // Add your email address inbetween the '' replacing yourname@yourdomain.com - This is where the form will send a message to.
# $email_subject = "ADD TO EMAIL LIST:  $name";
# $email_body = "Name: $name\nEmail: $email_address";
# $headers = "From: noreply@tjcubing.org\n"; // This is the email address the generated message will be from. We recommend using something like noreply@yourdomain.com.
# $headers .= "Reply-To: $email_address";
# mail($to,$email_subject,$email_body,$headers);
# return true;
# ?>
