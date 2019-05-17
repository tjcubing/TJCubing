import time, json
from datetime import datetime
import flask
#from requests_oauthlib import OAuth2Session
import cube

#TODO: Gulp

app = flask.Flask(__name__)
app.secret_key = cube.CONFIG["flask_secret_key"].encode()
#print([rule.endpoint for rule in app.url_map.iter_rules()])

# flask.session = {} #holds temp global data, without using globals. kinda a hack on mutability.
#might be glitchy with multiple users not sure.

def send_home(msg, category="success"):
    """ Redirects the user back to home with an alert. """
    flask.flash(msg, category)
    return flask.redirect(flask.url_for("index"))

@app.before_request
def before_request():
    if time.time() > cube.short_date(cube.VOTE["ends_at"]):
        cube.VOTE["vote_active"] = False
        cube.dump_file(cube.VOTE, "vote")

# @app.after_request
# def do_something_whenever_a_request_has_been_handled(response):
#     # we have a response to manipulate, always return one
#     return response

def competitions() -> dict:
    """ Gets the cached competitions, but will refresh if not updated recently. """
    c = cube.load_file("comps")
    last, comps = c["time"], c["comps"]
    if time.time() - last > cube.WAIT:
        comps = cube.get_comps()

    return {"comps": comps, "last": cube.unix_to_human(last)}

def lectures() -> dict:
    """ Returns the lectures. """
    return {"lectures": cube.get_lectures()}

def result() -> dict:
    """ Displays the result of the election. """
    return {"result": cube.get_winner(), "vote": cube.VOTE}

def search() -> dict:
    """ Parses the user's search. Can be POST or GET method. """
    query = None
    if flask.request.method == 'POST':
        query = flask.request.form['query']
    elif flask.request.args.get('query', None) is not None:
        query = flask.request.args['query']
    return {"entries": [(time, NAMES[html], html, preview) for time, html, preview in cube.parse_search(query)]}

def convert(order:list, prefix:str="", new:list=[]) -> list:
    """ Converts an order specification into a parsable (path, name) format by the nav header. """
    for name in order:
        if isinstance(name, list):
            addition, sublist = name
            new.append(("*" + addition, convert(sublist, "{}".format(prefix), [])))
            #new.append(("*" + addition, convert(sublist, "{}{}/".format(prefix, addition), [])))
        else:
            new.append(("{}{}".format(prefix, name if name != "" else "index"), NAMES[name]))
    return new

params = cube.load_file("site")
NAMES = params["names"]
NAV = convert(params["order"])

PAGES = {"": lambda: {"year": cube.get_year()},
         "competitions": competitions,
         "algorithms": None,
         "lectures": lectures,
         "inhouse": None,
         "history": lambda: cube.add_dict(cube.parse_club(), {"url": params["url"]}),
         "contact": None,
         "archive":
             {
                "tips": None,
             },
         "vote":
             {
                "eligibility": lambda: cube.VOTE,
                "admission": lambda: {"admission": cube.open_admission(), "sigs": cube.get_sigs()},
                "result": result,
             },
         "search": (search, ['POST', 'GET'])
        }

GLOBAL = {"pages": NAV, "active": cube.VOTE["vote_active"], "URL": params["url"]}

def make_page(s: str, f=lambda: {}, methods=['GET']):
    """ Takes in a string which specifies both the url and the file name, as well as a function which provides the kwargs for render_template. """
    func = lambda: flask.render_template((s if s != "" else "index") + cube.FILE, **GLOBAL, title=NAMES[s.split("/")[-1]], **f())
    # Need distinct function names for Flask not to error
    func.__name__ = s.split("/")[-1] if s != "" else "index"
    return app.route("/{}".format(s), methods=methods)(func)

def make_pages(d: dict, prefix="") -> None:
    """ Makes the entire site's pages. Recurs on nested dicts, taking file structure into account. """
    for key, value in d.items():
        if isinstance(value, dict):
            make_pages(value, prefix + "{}/".format(key))
        else:
            func, methods = ((value, ["GET"]) if not isinstance(value, tuple) else value)
            #don't need to store created function as it's already bound to the URL
            make_page(prefix + key, func if func is not None else lambda: {}, methods)

#TODO: update sitemap, update robots.txt with correct link
# https://stackoverflow.com/questions/14048779/with-flask-how-can-i-serve-robots-txt-and-sitemap-xml-as-static-files
@app.route("/sitemap.xml")
@app.route("/robots.txt")
def static_from_root():
    """ Serves a file from static, skipping the /static/. """
    return flask.send_from_directory(app.static_folder, flask.request.path[1:])

# https://requests-oauthlib.readthedocs.io/en/latest/
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
    code = flask.request.args.get('code', None)
    if flask.request.args.get('error', None) is not None or code is None:
        return send_home("You must allow Ion OAuth access to vote!", "danger")
    oauth = cube.make_oauth(state=flask.session['oauth_state'])
    token = oauth.fetch_token(cube.TOKEN_URL, code=code, client_secret=cube.CONFIG["client_secret"])
    cube.save_token(token)

    return flask.redirect(flask.session["action"])

@app.route("/vote/vote", methods=["GET", "POST"])
def vote():
    if not cube.test_token():
        flask.session["action"] = flask.request.path
        return flask.redirect(flask.url_for("login"))

    if not cube.valid_voter():
        return send_home("You do not fullfill the requirements to be able to vote.", "warning")

    if not cube.VOTE["vote_active"]:
        return send_home("Stop trying to subvert democracy!!!", "danger")

    if flask.request.method == "POST":
        cube.add_vote(cube.get_name(), flask.request.form["vote"])
        return send_home("<strong>Congrats!</strong> You have voted for {}.".format(flask.request.form['vote']))

    return flask.render_template(flask.request.path + cube.FILE, **GLOBAL, **cube.VOTE, sorted_candidates=cube.get_candidates(), name=cube.get_name(), title="vote")

@app.route("/vote/run", methods=["GET", "POST"])
def run():
    if not cube.test_token():
        flask.session["action"] = flask.request.path
        return flask.redirect(flask.url_for("login"))

    if not cube.valid_runner():
        return send_home("You do not fullfill the requirements to be able to run.", "warning")

    if not cube.VOTE["vote_active"]:
        return send_home("Stop trying to subvert democracy!!!", "danger")

    signups = cube.get_signups()
    params = {"name": cube.get_name(),
              "years": cube.count_years(signups),
              "meetings": cube.count_meetings(signups, datetime.min, datetime.max),
              "annual_meetings": cube.count_meetings(signups),
              "year": cube.get_year(),
             }

    if flask.request.method == "POST":
        cube.store_candidate(cube.add_dict({"description": flask.request.form['description']}, params))
        return send_home("<strong>Congrats!</strong> Your application has been registered.")

    return flask.render_template(flask.request.path + cube.FILE, **GLOBAL, **cube.VOTE, **params, title="run")

#http://flask.pocoo.org/docs/1.0/patterns/errorpages/
@app.errorhandler(404)
def page_not_found(e):
    return flask.render_template('error/404' + cube.FILE, title="404", pages=NAV), 404

make_pages(PAGES)
