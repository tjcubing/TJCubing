import json, pickle, time, os
from datetime import datetime
import markdown2
import requests
import flask
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from bs4 import BeautifulSoup

# Helper library to query the WCA for competitions and other miscellaneous tasks
# 05/30/19 12:00 PM
# TODO: mailing list, switch key to key from tjcubingofficers@gmail.com
# TODO: Database
# TODO: selenium/requests style parsing to download rendered templates
# switch to python 3.5.3

STR_FUNC = {"load": {"json": json.load, "pickle": pickle.load}, "dump": {"json": json.dump, "pickle": pickle.dump}}
EXT_MODE = {"json": "", "pickle": "b"}

def load_file(fname: str, func: str="json", short: bool=True) -> dict:
    """ Loads a file. """
    with open("files/{}.{}".format(fname, func) if short else fname, "r" + EXT_MODE[func]) as f:
        return STR_FUNC["load"][func](f)

def dump_file(obj, fname: str, func:str ="json", short: bool=True) -> None:
    """ Dumps an obj into a file. """
    with open("files/{}.{}".format(fname, func) if short else fname, "w" + EXT_MODE[func]) as f:
        STR_FUNC["dump"][func](obj, f, **({"indent": 4} if func == "json" else {}))

CONFIG = load_file("config")
VOTE = load_file("vote")
URL = "https://www.worldcubeassociation.org/competitions"
LECTURES = "static/pdfs/"
FILE = ".html.j2"
PREVIEW = 80
WAIT = 2.628e6 #seconds in a month

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #turn off when it's legit, localhost is http
ION = "https://ion.tjhsst.edu/"
AUTHORIZATION_URL, TOKEN_URL = ION + "oauth/authorize/", ION + "oauth/token/"

def add_dict(d1: dict, d2: dict) -> dict:
    """ Adds two dictionaries together, assuming no conflicts. """
    return {**d1, **d2}

def gen_secret_key() -> str:
    """ Generates a random secret key. """
    return os.urandom(16).hex()

def get_year() -> int:
    """ Returns the year as a number """
    return datetime.today().year

def footer_time() -> float:
    """ Returns the current time in the footer format. """
    return time.strftime("%Y-%m-%d %X %z", time.localtime())

def ion_date(date: str) -> datetime:
    """ Converts an ION formatted date to a datetime object. """
    return datetime.strptime(date, "%Y-%m-%d")

def short_date(date: str) -> float:
    """ Converts my arbitrary shorthand date to a UNIX time. """
    return datetime.strptime(date, "%m/%d/%y %I:%M %p").timestamp()

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
        if info[2].split(", ")[-1] in CONFIG["states"]:
            temp = {"url": URL + comp.find("a").get('href')[13:],
                    "name": info[1],
                    "location": info[2],
                    "venue": info[3],
                    "date": info[0],
                   }
            subsoup = make_soup(temp["url"])
            temp["gps"] = subsoup.find("dt", string="Address").next_sibling.next_sibling.find("a").get('href').split("/")[-1]
            comps.append(temp)

    param = {'origins': CONFIG["origin"], 'destinations': "|".join([comp["gps"] for comp in comps]), 'key': CONFIG["key"], 'units': 'imperial'}

    for i, thing in enumerate(requests.get("https://maps.googleapis.com/maps/api/distancematrix/json", params=param).json()['rows'][0]['elements']):
        comps[i]["mi"] = thing['distance']['text']
        comps[i]["timestr"] = thing['duration']['text']
        comps[i]["time"] = thing['duration']['value']

    #TODO: sort by user-determined feature
    comps.sort(key=lambda comp: comp["time"]) #sort by time to travel
    dump_file({"time": time.time(), "comps": comps}, "comps")

    return comps

def get_lectures() -> list:
    """ Returns a list of past lectures. """
    lectures = []
    for lecture in os.listdir(LECTURES):
        if os.path.isdir(LECTURES + lecture):
            lectures.append(load_file("{}{}/desc.json".format(LECTURES, lecture), "json", False))

    lectures.sort(key=lambda l: datetime.strptime(l["date"], "%m/%d/%Y")) #sort by date
    return lectures

def open_admission() -> str:
    """ Parses the admission text and converts it into html """
    file = open("static/misc/admission.md").read()
    return markdown2.markdown(file)

def get_sigs() -> list:
    """ Returns the signatures of the admission. """
    for file in os.listdir("static/misc"):
        if file[-4:] == ".asc":
            yield (file, open("static/misc/{}".format(file)).read().replace("\n", "<br>"))

def add_tag(tag: str, s: str) -> str:
    """ Adds a tag on either side of a string. """
    return "<{}>{}</{}>".format(tag, s, tag)

def modify(word: str, text: str) -> str:
    """ Applies a HTML modifer to a subset of a string. """
    i = text.lower().index(word)
    return text[:i] + add_tag("strong", text[i: i + len(word)]) + text[i + len(word):]

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
            soup = BeautifulSoup(open("templates/{}".format(html)).read(), 'html.parser')
            text = soup.get_text()
            if query in text.lower():
                yield (unix_to_human(os.path.getmtime("templates/{}".format(html))), html if html != "index" + FILE else FILE, modify(query, get_preview(query, text)))

def store_candidate(d: dict) -> None:
    """ Stores a candidate to vote.json. """
    d["time"] = time.time()
    d["timestr"] = unix_to_human(time.time())
    d["description"] = d["description"][:VOTE["length"]] #"client side validation big stupid" - Darin Mao
    VOTE["candidates"][d["name"]] = d
    dump_file(VOTE, "vote")

def get_candidates() -> list:
    """ Returns a list of candidates, sorted by entry time. """
    candidates = list(VOTE["candidates"].values())
    candidates.sort(key=lambda d: d["time"])
    return candidates

def add_vote(name: str, candidate: str) -> None:
    """ Adds a vote from name to candidate. """
    VOTE["votes"][name] = candidate
    dump_file(VOTE, "vote")

def get_winner() -> str:
    """ Returns the winner of the election. """
    count = {}
    for vote in VOTE["votes"].values():
        count[vote] = count.get(vote, 0) + 1
    winner = max(count, key=lambda v: count[v])
    votes = count[winner]
    del count[winner]
    if votes in count.values(): #Tie - two instances of the most votes
        return
    return winner

def save_token(token: dict) -> None:
    """ Saves a token to Flask. """
    flask.session["token"] = token

def make_oauth(**kwargs) -> OAuth2Session:
    """ Makes an OAuth2Session session. Should auto-refresh. """
    args = {"client_id": CONFIG["client_id"], "client_secret": CONFIG["client_secret"]}
    return OAuth2Session(CONFIG["client_id"], token=flask.session.get("token", None), redirect_uri=CONFIG["redirect_uri"], scope=["read"], auto_refresh_url=TOKEN_URL, auto_refresh_kwargs=args, token_updater=save_token, **kwargs)

def make_api_call(call: str, short=True) -> dict:
    """ Makes an API call and returns a dictionary. """
    oauth = make_oauth(**{"state": flask.session["oauth_state"]})
    return json.loads(oauth.get(ION + "api/{}".format(call) if short else call).content.decode())

def test_token():
    """ Tests whether or not the user is authenticated. """
    return "token" in flask.session

def get_name() -> str:
    """ Returns the name of the user. """
    if "name" not in flask.session:
        flask.session["name"] = make_api_call("profile")["display_name"]
    return flask.session["name"]

def get_club_result() -> list:
    """ Returns the club's page. """
    d = make_api_call("activities")
    while "next" in d and d["next"] is not None:
        for result in d["results"]:
            if "cube" in result["name"].lower():
                return result
        d = make_api_call(d["next"], False)

#TODO: some sort of legit method of updating these beyond func calls
#TODO: Admin page to do that: prob just function_name (description): [button to run function]
#TODO: take into account existing club.json file (i.e cuts down on API calls)
def save_club_history() -> dict:
    """ Returns the ION page describing the club. """
    page = make_api_call(CONFIG["club"]["url"], False)
    for key, block in page["scheduled_on"].items():
        block["subcall"] = make_api_call(block["roster"]["url"], False)
    page["time"] = time.time()
    dump_file(page, "club")

def parse_block(block):
    """ Parses an individual block. """
    return {"title": block["subcall"]["name"],
            "count": block["subcall"]["signups"]["count"],
            "capacity": block["subcall"]["capacity"],
            "date": block["date"],
            "day": ion_date(block["date"]).strftime("%A"),
            "block_letter": block["block_letter"],
           }

#TODO: matplotlib graphs
#4-column bar (Wed A Wed B Fri A Fri B)
#Capacity as a line graph over time

def parse_club():
    """ Makes a smaller representation of the club.json file. """
    club = load_file("club")
    parsed = {"name": club["name"], "description": club["description"], "blocks": []}
    parsed["blocks"] = list(map(parse_block, club["scheduled_on"].values()))
    return parsed

def graph_blocks():
    pass

def graph_capacity():
    pass

def get_signups() -> list:
    """ Returns all of the user's 8th pd signups at a specific club. """
    signups = make_api_call("signups/user")
    return list(filter(lambda signup: signup["activity"]["id"] == CONFIG["club"]["id"], signups))

def count_meetings(signups=None, left: datetime=datetime(get_year() - 1, 7, 10), right: datetime=datetime.today()) -> int:
    """ Retuns the number of meetings the user has been to, between two date ranges. """
    """ Left bound is chosen as an arbitrary date guarenteed to be after any 8th pds from the past year, but before any from the current year. """
    """ Right bound is chosen to be today. """
    signups = list(filter(lambda signup: left < ion_date(signup["block"]["date"]) < right, get_signups() if signups is None else signups))
    return len(signups)

def count_years(signups=None) -> int:
    """ Returns the number of distinct years the user has been to the club """
    return len(set([ion_date(signup["block"]["date"]).year for signup in (get_signups() if signups is None else signups)]))

def valid_voter() -> bool:
    """ Returns whether not not the user is allowed to vote. """
    # Possibly was unable but now able, but never able and then unable.
    if not flask.session.get("valid_voter", False):
        signups = get_signups()
        total, annual = count_meetings(signups, datetime.min, datetime.max), count_meetings(signups)
        flask.session["valid_voter"] = annual >= VOTE["min_meetings"] or total >= 2*VOTE["min_meetings"]
    return flask.session["valid_voter"]

def valid_runner() -> bool:
    """ Returns whether or not the user is allowed to run for office. """
    if not flask.session.get("valid_runner", False):
        flask.session["valid_runner"] = True #why not?
    return flask.session["valid_runner"]
