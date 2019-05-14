import time, json
from datetime import datetime
import flask
#from requests_oauthlib import OAuth2Session
import cube

app = flask.Flask(__name__)
app.secret_key = cube.config["flask_secret_key"].encode()
#print([rule.endpoint for rule in app.url_map.iter_rules()])

def competitions() -> dict:
    """ Gets the cached competitions, but will refresh if not updated recently. """
    last, comps = cube.load_file("comps", "pickle")
    if time.time() - last > cube.WAIT:
        comps = cube.get_comps()

    return {"comps": comps, "last": cube.unix_to_human(last)}

def lectures() -> dict:
    """ Returns the lectures. """
    return {"lectures": cube.get_lectures()}

def search() -> dict:
    """ Parses the user's search. Can be POST or GET method. """
    query = None
    if flask.request.method == 'POST':
        query = flask.request.form['query']
    elif flask.request.args.get('query', None) is not None:
        query = flask.request.args['query']
    return {"entries": [(time, NAMES[html[:-len(cube.FILE)]], html, preview) for time, html, preview in cube.parse_search(query)]}

PAGES = {"": lambda: {'year': datetime.today().year},
         "competitions": competitions,
         "algorithms": None,
         "lectures": lectures,
         "tips": None,
         "contact": None,
         "vote":
         {
            "eligibility": None,
            "admission": None,
            "vote": None,
            "run": None,
            "result": None,
         },
         "search": (search, ['POST', 'GET'])
        }

NAMES = cube.load_file("names")
ORDER = ["", "competitions", "algorithms", "lectures", "tips", "contact", ""]

NAV = [(f"/{i}", NAMES[i]) for i in ["", "competitions", "algorithms", "lectures", "tips", "contact"]] #need order as dicts are unordered
NAV.append(("vote", [(f"vote/{i}", NAMES[i]) for i in ["eligibility", "admission", "vote", "run", "result"]]))

def make_page(s: str, f=lambda: {}, methods=['GET']):
    """ Takes in a string which specifies both the url and the file name, as well as a function which provides the kwargs for render_template. """
    func = lambda: flask.render_template((s if s != "" else "index") + cube.FILE, pages=NAV, **f())
    # Need distinct function names for Flask not to error
    func.__name__ = s
    return app.route(f"/{s}", methods=methods)(func)

def make_pages(d: dict, prefix="") -> None:
    """ Makes the entire site's pages. Recurs on nested dicts, taking file structure into account. """
    for key, value in d.items():
        if isinstance(value, dict):
            make_pages(value, prefix + f"{key}/")
        else:
            func, methods = ((value, ["GET"]) if not isinstance(value, tuple) else value)
            make_page(prefix + key, func if func is not None else lambda: {}, methods)

make_pages(PAGES)

# for page in PAGES:
#     #don't need to store created function as it's already bound to the URL
#     make_page(page, PAGES[page] if PAGES[page] is not None else lambda: {})

@app.route("/login")
def login():
    oauth = cube.make_oauth()
    authorization_url, state = oauth.authorization_url(cube.AUTHORIZATION_URL)

    # State is used to prevent CSRF, keep this for later.
    flask.session["oauth_state"] = state
    return flask.redirect(authorization_url)

@app.route("/callback")
def callback():
    assert flask.request.args.get('state', None) == flask.session['oauth_state']
    oauth = cube.make_oauth(state=flask.session['oauth_state'])
    token = oauth.fetch_token(cube.TOKEN_URL, code=flask.request.args.get('code', None), client_secret=cube.config["client_secret"])
    cube.save_token(token)

    cube.save_club_history(oauth)
    #print(cube.make_api_call("activities"))
    print(token)
    return str(cube.make_api_call(oauth, "profile"))
