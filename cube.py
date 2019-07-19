import json, pickle, time, os, getpass
from datetime import datetime
from datetime import timedelta
import arrow
import humanize
import markdown2
import yagmail
import numpy as np
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn.metrics import r2_score
from passlib.hash import pbkdf2_sha512
import gnupg
from fbchat import Client
import requests
from bs4 import BeautifulSoup
import flask
from requests_oauthlib import OAuth2Session
import statistics, forms
# from oauthlib.oauth2 import TokenExpiredError

# Helper library to query the WCA for competitions and other miscellaneous tasks
# TODO: Database: Postgres?
# TODO: switch all times to arrow times

STR_FUNC = {"load": {"json": json.load, "pickle": pickle.load, "text": lambda f: f.read()},
            "dump": {"json": json.dump, "pickle": pickle.dump, "text": lambda f, obj: f.write(obj)}
           }
EXT_MODE = {"json": "", "pickle": "b", "text": ""}

def load_file(fname: str, func: str="json", short: bool=True) -> dict:
    """ Loads a file. """
    with open("files/{}.{}".format(fname, func) if short else fname, "r" + EXT_MODE[func]) as f:
        return STR_FUNC["load"][func](f)

def dump_file(obj, fname: str, func:str="json", short: bool=True) -> None:
    """ Dumps an obj into a file. """
    with open("files/{}.{}".format(fname, func) if short else fname, "w" + EXT_MODE[func]) as f:
        STR_FUNC["dump"][func](obj, f, **({"indent": 4, "sort_keys": True} if func == "json" else {}))

CONFIG = load_file("config")
URL = "https://www.worldcubeassociation.org/competitions"
LECTURES = "static/pdfs/"
FILE = ".html.j2"
PREVIEW = 80
PARSER = "lxml"
SITEMAP = "static/sitemap.xml"
REPO = "https://github.com/stephen-huan/TJCubing"
#alternatively http://cubing.sites.tjhsst.edu
TJ = "https://activities.tjhsst.edu/cubing/"
EVENTS = ['3x3x3 Cube', '2x2x2 Cube', '4x4x4 Cube', '5x5x5 Cube', '6x6x6 Cube', '7x7x7 Cube', '3x3x3 Blindfolded', '3x3x3 Fewest Moves', '3x3x3 One-Handed', '3x3x3 With Feet', 'Clock', 'Megaminx', 'Pyraminx', 'Skewb', 'Square-1', '4x4x4 Blindfolded', '5x5x5 Blindfolded', '3x3x3 Multi-Blind']
RANKS = ["nr", "cr", "wr"]

https = load_file("site")["url"][:5] == "https"
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = str(int(not https))
os.environ['FLASK_ENV'] = "development"

gpg = gnupg.GPG(gnupghome=".gnupg")

# Overwrite markdown2.markdown function to include extras
markdown = markdown2.markdown
temp = lambda s: markdown(s, extras=["cuddled-lists", "strike"])
markdown2.markdown = temp

def add_dict(d1: dict, d2: dict) -> dict:
    """ Adds two dictionaries together, assuming no conflicts. """
    return {**d1, **d2}

def gen_secret(length=16) -> str:
    """ Generates a random secret key. """
    return os.urandom(length).hex()

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

def make_soup(text: str, mode: str="url", parser: str=PARSER) -> BeautifulSoup:
    """ Returns a soup. """
    if mode == "url" or isinstance(mode, dict):
        params = mode if isinstance(mode, dict) else {}
        text = requests.get(text, params=params).text
    elif mode == "file":
        text = open(text)
    return BeautifulSoup(text, parser)

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

def parse_time(s: str) -> float:
    """ Parses a time string into the number of seconds. """
    if s == "":
        return statistics.DNF
    # MBLD
    if "/" in s:
        solved, attempted = s.split("/")
        return 2*int(solved) - int(attempted.split()[0])
    return round(sum(60**(len(s.split(":")) - 1 - i)*float(token) for i, token in enumerate(s.split(":"))), 2)

def add_zero(s: str, i: int) -> str:
    """ Adds "0" as a suffix or prefix if it needs it. """
    if "." in s and len(s.split(".")[1]) == 1:
        return s + "0"
    if i != 0 and len(s) == 4:
        return "0" + s
    return s

def time_formatted(event:str, mode:str, t: float) -> str:
    """ Reverses parse_time """
    if t == statistics.DNF:
        return ""
    if event in ["3x3x3 Fewest Moves", "3x3x3 Multi-Blind"]:
        if event == "3x3x3 Fewest Moves" and mode == "average":
            return str(t)
        return str(int(t))
    s = str(timedelta(seconds=t))
    tokens = list(filter(lambda token: float(token) != 0, s.split(":")))
    return ":".join([add_zero(str(round((float if i == len(tokens) - 1 else int)(token), 2)), i) for i, token in enumerate(tokens)])

def parse_rank(s: str) -> int:
    """ Parses a rank. """
    if s == "":
        return statistics.DNF
    return int(s)

def wca_profile(link: str) -> dict:
    """ Parses a user's profile. """
    soup = make_soup(link)
    table = soup.select(".personal-records")[0].find("table")

    text = lambda event, cls, i=0: event.select(".{}".format(cls))[i].text.strip()
    results = {text(event, "event"): add_dict(
               {cls: parse_time(text(event, cls)) for cls in ["single", "average"]},
               {name: {abr: parse_rank(text(event, cls, i)) for abr, cls in zip(RANKS, ["country-rank", "continent-rank", "world-rank"])}
                    for i, name in enumerate(["sranks", "aranks"])})
               for event in table.find_all("tr")[1:]
              }
    return results

def get_lectures() -> list:
    """ Returns a list of past lectures. """
    lectures = []
    for lecture in os.listdir(LECTURES):
        if os.path.isdir(LECTURES + lecture):
            lectures.append(load_file("{}{}/desc.json".format(LECTURES, lecture), "json", False))

    lectures.sort(key=lambda l: datetime.strptime(l["date"], "%m/%d/%Y")) #sort by date
    return lectures

def open_admission() -> str:
    """ Parses the admission text and converts it into HTML. """
    return markdown2.markdown(load_file("static/misc/admission.md", "text", False))

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
    # avoids out of bounds
    preview = text[max(i - PREVIEW, 0):min(i + PREVIEW, len(text))]
    # removes fractions of words
    # removed = " ".join(preview.split()[1:-1])
    # return removed if query in removed.lower() else preview
    return preview

def parse_search(query: str) -> list:
    """ Parses a user's search, returns a list of entries. """
    path = "rendered_templates/"
    query = query.strip().lower()
    if query == "":
        return

    for html in os.listdir(path):
        soup = make_soup(path + html, "file")
        body = soup.find("body")
        for element in ["nav", "footer"]:
            body.find(element).decompose()

        lowest = None
        for element in body.find_all():
            if query in element.text.lower():
                lowest = element

        if lowest is not None:
            yield (unix_to_human(os.path.getmtime(path + html)),
                   html[:-5] if html != "index.html" else "",
                   modify(query, get_preview(query, lowest.text)))

def store_candidate(d: dict) -> None:
    """ Stores a candidate to vote.json. """
    vote = load_file("vote")
    d["time"] = time.time()
    d["timestr"] = unix_to_human(time.time())
    #"client side validation big stupid" - Darin Mao
    d["description"] = d["description"][:forms.LENGTH]
    vote["candidates"][d["name"]] = d
    dump_file(vote, "vote")

def get_candidates() -> list:
    """ Returns a list of candidates, sorted by entry time. """
    candidates = list(load_file("vote")["candidates"].values())
    candidates.sort(key=lambda d: d["time"])
    return candidates

def add_vote(name: str, candidate: str) -> None:
    """ Adds a vote from name to candidate. """
    vote = load_file("vote")
    vote["votes"][name] = candidate
    dump_file(vote, "vote")

def get_winner() -> str:
    """ Returns the winner of the election. """
    count = {}
    for vote in load_file("vote")["votes"].values():
        count[vote] = count.get(vote, 0) + 1
    winner = max(count, key=lambda v: count[v])
    votes = count[winner]
    del count[winner]
    #Tie - two instances of the most votes
    if votes in count.values():
        return
    return winner

def make_key(name: str, param: str) -> str:
    """ Formats a key in the API style. """
    return "{}_{}".format(name, param)

def make_save_token(name: str):
    """ Returns a function which will save the token. """
    def save_token(token: dict) -> None:
        flask.session[make_key(name, "token")] = token

    return save_token

def make_oauth(name: str, **kwargs) -> OAuth2Session:
    """ Makes an OAuth2Session session. Should auto-refresh. """
    params = {param: CONFIG[make_key(name, param)] for param in ["id", "secret", "redirect_uri", "scope", "url"]}
    return OAuth2Session(params["id"],
                         token=flask.session.get(make_key(name, "token"), None),
                         redirect_uri=params["redirect_uri"],
                         scope=params["scope"],
                         auto_refresh_url=params["url"] + "oauth/token",
                         auto_refresh_kwargs={"client_id": params["id"], "client_secret": params["secret"]},
                         token_updater=make_save_token(name),
                         **kwargs
                        )

def fetch_token(name: str, oauth: OAuth2Session, code: str) -> dict:
    """ Returns and saves a token. """
    token = oauth.fetch_token(CONFIG[make_key(name, "url")] + "oauth/token", code=code, client_secret=CONFIG[make_key(name, "secret")])
    make_save_token(name)(token)
    return token

def api_call(name: str, call: str, short=True) -> dict:
    """ Makes an API call and returns a dictionary. """
    oauth = make_oauth(name, state=flask.session[make_key(name, "state")])
    extra = "v0/" if name == "wca" else ""
    return json.loads(oauth.get("{}api/{}{}".format(CONFIG[make_key(name, "url")], extra, call) if short else call).content.decode())

def test_token(name: str) -> bool:
    """ Tests whether or not the user is authenticated. """
    return make_key(name, "token") in flask.session

def get_name() -> str:
    """ Returns the name of the user. """
    if "name" not in flask.session:
        flask.session["name"] = api_call("ion", "profile")["display_name"]
    return flask.session["name"]

def get_club_result() -> list:
    """ Returns the club's page. """
    d = api_call("ion", "activities")
    while "next" in d and d["next"] is not None:
        for result in d["results"]:
            if "cube" in result["name"].lower():
                return result
        d = api_call("ion", d["next"], False)

# TODO: some sort of legit method of updating these beyond func calls
# TODO: Admin page to do that: prob just function_name (description): [button to run function]
# TODO: take into account existing club.json file (i.e cuts down on API calls)
def save_club_history() -> dict:
    """ Returns the ION page describing the club. """
    page = api_call("ion", CONFIG["club"]["url"], False)
    for key, block in page["scheduled_on"].items():
        block["subcall"] = api_call("ion", block["roster"]["url"], False)
    page["time"] = time.time()
    dump_file(page, "club")

def parse_block(block) -> dict:
    """ Parses an individual block. """
    return {"title": block["subcall"]["name"],
            "count": block["subcall"]["signups"]["count"],
            "capacity": block["subcall"]["capacity"],
            "date": block["date"],
            "day": ion_date(block["date"]).strftime("%A"),
            "block_letter": block["block_letter"],
           }

def parse_club() -> dict:
    """ Makes a smaller representation of the club.json file. """
    club = load_file("club")
    parsed = {"name": club["name"], "description": club["description"], "blocks": []}
    parsed["blocks"] = list(map(parse_block, club["scheduled_on"].values()))
    parsed["blocks"].sort(key=lambda b: ion_date(b["date"]))
    return parsed

def graph_blocks(s) -> None:
    """ Graphs frequency of Wednesday/Friday A/B. """
    funcs = {"by_x": lambda x: 10*days.index(x[0].split()[0]) + "AB".index(x[0].split()[1]), "by_y": lambda x: x[-1]}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    counts = {day + " " + block: 0 for day in days for block in "AB"}
    for block in parse_club()["blocks"]:
        key = block["day"] + " " + block["block_letter"]
        counts[key] += 1
    x, y = zip(*sorted(counts.items(), key=funcs.get(s, None)))
    plt.figure(figsize=(15, 5))
    plt.bar(x, y)
    plt.title("Block Frequency")
    plt.xlabel("Day and Block")
    plt.ylabel("Frequency (number)")
    plt.savefig("static/img/blocks{}.png".format(s))

def graph_capacity() -> None:
    """ Graphs actual over capacity over time. """
    x, y = zip(*[(ion_date(block["date"]), 100*block["count"]/block["capacity"]) for block in parse_club()["blocks"] if block["capacity"] != 0])

    xp = np.array(list(map(lambda d: d.timestamp(), x))).reshape(-1, 1)
    regr = linear_model.LinearRegression()
    regr.fit(xp, y)
    yp = regr.predict(xp)

    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.plot(x, yp, label="Line of best fit\n{}\n{}".format(r"$r^2 = {}$".format(round(r2_score(y, yp), 4)), r"$m = {}$".format(round(regr.coef_[0], 4))))
    ax.legend(loc="upper right")
    plt.title("Rubik's Cube Club Attendance Over Time")
    plt.xlabel("Time")
    plt.ylabel("Percentage of People Attending (%)")
    plt.savefig("static/img/capacity.png")

def get_signups() -> list:
    """ Returns all of the user's 8th pd signups at a specific club. """
    signups = api_call("ion", "signups/user")
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
        cutoff = load_file("vote")["min_meetings"]
        flask.session["valid_voter"] = annual >= cutoff or total >= 2*cutoff
    return flask.session["valid_voter"]

def valid_runner() -> bool:
    """ Returns whether or not the user is allowed to run for office. """
    if not flask.session.get("valid_runner", False):
        #why not?
        flask.session["valid_runner"] = True
    return flask.session["valid_runner"]

def add_xmltag(soup, element, seen, name, default, update=False):
    """ Adds a new tag to an element. """
    tag = soup.new_tag(name)
    seen[name] = seen.get(name, default) if not update else default
    tag.append(str(seen[name]))
    element.append(tag)

def edit_sitemap(use_json=True) -> None:
    """ Changes the URL on the sitemap and modification times. """
    soup = make_soup(SITEMAP, "file", "xml")
    seen = load_file("sitemap") if use_json else {}
    for child in soup.find_all("url"):
        loc = child.find("loc")
        path = "/".join(loc.text.split("/")[3:]).strip()
        if path not in seen or use_json:
            if not use_json:
                seen[path] = {}

            seen[path]["loc"] = seen[path].get("loc", TJ + path)
            loc.string.replace_with(seen[path]["loc"])
            fname = "templates/" + path + FILE
            if not os.path.isfile(fname):
                if path in ["robots.txt", "sitemap.xml"]:
                    fname = "static/" + path
                elif path in [""]:
                    fname = "templates/index" + FILE
                else:
                    fname = None

            mtime = datetime.fromtimestamp(os.path.getmtime(fname)).isoformat() if fname is not None else None
            for args in [("lastmod", mtime, True), ("changefreq", "yearly", False), ("priority", 0.0, False)]:
                add_xmltag(soup, child, seen[path], *args)

        else:
            child.decompose()

    with open(SITEMAP, "w") as f:
        f.write(soup.prettify())

    dump_file(seen, "sitemap")

def github_commit_time() -> str:
    """ Returns the time of the last Github commit. """
    soup = make_soup(REPO + "/commits/master")
    mtime = soup.find("relative-time")
    return arrow.get(mtime["datetime"]).to('US/Eastern').format('YYYY-MM-DD HH:mm:ss ZZ')

def get_pfp(name: str, client: Client=None) -> Client:
    """ Gets the Facebook profile picture of a person, and saves the profile location. """
    client = Client(CONFIG["email"], getpass.getpass()) if client is None else client
    user = client.searchForUsers(name)[0]
    d = load_file("fb")
    d[name] = user.url
    dump_file(d, "fb")
    with open("static/img/pfps/{}.png".format(name.replace(" ", "")), "wb") as f:
        f.write(requests.get(user.photo).content)
    return client

def get_pfps(names: list) -> None:
    """ Gets multiple profile pictures at a time, saving the same client object. """
    client = get_pfp(names[0])
    for name in names[1:]:
        get_pfp(name, client)

def get_errors() -> list:
    """ Returns the defined HTTP status errors. """
    return [int(fname.split(FILE)[0]) for fname in os.listdir("templates/error")]

def register(username: str, password: str) -> None:
    """ Registers a new user account. """
    users = load_file("users")
    user = users[username] = {}
    user["hash"] = pbkdf2_sha512.hash(password)
    user["scope"] = "default"
    user["keys"] = []
    user["encrypt"] = True
    dump_file(users, "users")

def check(username: str, password: str) -> bool:
    """ Determines whether a login is legitimate or not. """
    user = load_file("users").get(username, None)
    return user is not None and pbkdf2_sha512.verify(password, user["hash"])

def prompt_email(email: str) -> None:
    """ Sends a email asking for verification. """
    emails = load_file("emails")
    nonce = gen_secret()
    emails["requests"][nonce] = email
    dump_file(emails, "emails")
    body = """Please click on this link to be added to the mailing list.
<a href="{}">Add</a>

<p><small>If you did not request this email, discard this message.</small><p>""".format(load_file("site")["url"] + "/email?nonce={}".format(nonce))
    send_email(email, "Request to join mailing list", body)

def register_email(email: str) -> None:
    """ Stores an email in the mailing list. """
    emails = load_file("emails")
    if email not in emails["emails"]:
        emails["emails"].append(email)
    dump_file(emails, "emails")

def send_email(recipients: list, subject: str, body: str) -> None:
    """ Sends an email. """
    yag = yagmail.SMTP(CONFIG["clubmail"], oauth2_file=os.getcwd() + "/files/oauth2_creds.json")
    yag.send(to=recipients, subject=subject, contents=body)

def save_email(subject: str, body: str) -> None:
    """ Saves an email to disk. """
    mails = load_file("mails.json", "json", False)
    mails.append({"subject": subject, "body": body, "time": time.time()})
    dump_file(mails, "mails.json", "json", False)
