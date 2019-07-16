import time, os, logging
from datetime import datetime
import flask
from flask_sitemap import Sitemap
import flask_uploads
from werkzeug.utils import secure_filename
from werkzeug.exceptions import InternalServerError
import cube, statistics

# TODO: in house comps page
# TODO: partial highlighting on mobile
# TODO: fix mobile login/profile UI
# TODO: 413 not being rendered in actual site
# TODO: prevent CSRF + general security
# TODO: enable autoescaping
# print([rule.endpoint for rule in app.url_map.iter_rules()])

def select_jinja_autoescape(self, filename: str) -> bool:
    """ Overwrites Flask's default behavior to autoescape on custom file endings. """
    if filename is None:
        return False
    if filename.endswith(cube.FILE):
        return True
    return flask.Flask.select_jinja_autoescape(self, filename)

# flask.Flask.select_jinja_autoescape = select_jinja_autoescape
app = flask.Flask(__name__)

# config: one default (public), the other private
app.config.from_object('settings')
os.environ["FLASK_SETTINGS"] = cube.CONFIG["flask_config"]
app.config.from_envvar("FLASK_SETTINGS")

# generate sitemap
# ext = Sitemap(app=app)

# Create an upload set
TIMES = flask_uploads.UploadSet("times")
PHOTOS = flask_uploads.UploadSet("photos", flask_uploads.IMAGES)
flask_uploads.configure_uploads(app, (TIMES, PHOTOS))
# Strange glitch with TJ servers - if you look at the source code this
# *should* happen already...
app.register_blueprint(flask_uploads.uploads_mod)

def alert(msg: str, category: str="success", loc: str="index"):
    """ Redirects the user with an alert. """
    flask.flash(msg, category)
    dest = {"self": flask.request.path,
            "meta": flask.request.full_path
           }
    return flask.redirect(flask.url_for(loc) if loc not in dest else dest[loc])

def format_exts(exts: list):
    """ Returns a formatted list of extentions. """
    return ", ".join(["." + ext for ext in exts])

@app.before_request
def before_request():
    try:
        vote = cube.load_file("vote")
    except:
        #sometimes fails, not sure why
        app.logger.warning("Error in parsing JSON file")
    else:
        if time.time() > cube.short_date(vote["ends_at"]):
            vote["vote_active"] = False
            cube.dump_file(vote, "vote")

# @app.after_request
# def do_something_whenever_a_request_has_been_handled(response):
#     # we have a response to manipulate, always return one
#     return response

def index() -> dict:
    """ Gives the year to list past TJHSST competitions, handles email signups. """
    if flask.request.method == "POST":
        cube.prompt_email(flask.request.form["email"])
        return alert("Check your email for a verification message.", "success")

    return {"year": cube.get_year()}

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
    return {"result": cube.get_winner(), "vote": cube.load_file("vote")}

# http://flask.pocoo.org/docs/1.0/patterns/fileuploads/
def stats() -> dict:
    """ Parses a user's .csv / .txt file and returns statistics. """
    if flask.request.method == "POST":
        times = None
        if "times" in flask.request.form:
            times = statistics.parse_text(flask.request.form["times"])
        else:
            if "file" not in flask.request.files:
                return alert("No file part.", "warning", "self")
            file = flask.request.files['file']
            if file.filename == "":
                return alert("No selected file.", "warning", "self")
            if file and TIMES.file_allowed(file, secure_filename(file.filename)):
                times = statistics.parse(file)

        if times:
            descr, mean, best = statistics.process(times)
            return {"display": True, "descr": descr, "mean": mean, "best": best}

    return {"display": False}

def profile() -> dict:
    """ Allows the user to login as well as register a new account. """
    if flask.request.method == "POST":
        users = cube.load_file("users")
        form = flask.request.form

        if "logout" in form:
            del flask.session["account"]
            return {}

        if "delete" in form:
            del users[flask.session["account"]]
            del flask.session["account"]
            cube.dump_file(users, "users")
            return alert("Account deleted!", "success", "self")

        if "clear" in form:
            flask.session.clear()
            return {}

        if "http" in form:
            flask.abort(int(form["http"]))

        if "email" in form:
            recipients = form["recipients"].split(", ") if form["recipients"] != "" else cube.load_file("emails")["emails"]
            body = cube.markdown2.markdown(form["email"]).replace("\n", "")
            cube.send_email(recipients, form["subject"], body)
            if "log" in form:
                cube.save_email(form["subject"], form["email"])
            return alert("Mail sent.", "success", "meta")

        if "submit" in form:
            username, password = form["username"], form["password"]
            if "checkpassword" in form:
                if username in cube.load_file("users"):
                    return alert("Username is taken.", "info", "meta")
                if password != form["checkpassword"] :
                    return alert("Passwords do not match.", "info", "meta")
                cube.register(username, password)
                return alert("Account registered!", "success", "self")

            if not cube.check(username, password):
                return alert("Username or password is incorrect.", "info", "self")

            # Save login to cookies
            flask.session["account"] = username
            flask.session["scope"] = users[username]["scope"]

    if "account" in flask.session:
        tabs = [["overview", "API"], ["email", "refresh", "develop"], ["edit"]]
        scopes = {"default": 0, "privileged": 1, "admin": 2}
        tab = flask.request.args.get('tab', 'overview')

        i = None
        for j, group in enumerate(tabs):
            if tab in group:
                i = j
        if i is None:
            return alert("Invalid tab!", "info", "self")
        if i > scopes[flask.session["scope"]]:
            return alert("User does not have the valid scope. This incident will be logged.", "danger", "self")

        return {"tabs": tabs,
                "scopes": scopes,
                "clubmailpassword": cube.load_file("secrets")["clubmailpassword"],
                "emails": cube.load_file("emails")["emails"],
               }

    return {}

def delete_photo() -> None:
    """ Deletes a photo from the server. """
    users = cube.load_file("users")
    user = users[flask.session["account"]]
    try:
        del user["pfp"]
    except KeyError:
        pass

    try:
        os.remove(PHOTOS.path(user["pfpfilename"]))
        del user["pfpfilename"]
    except (KeyError, FileNotFoundError):
        pass

    cube.dump_file(users, "users")

def settings() -> dict:
    """ Adjusts a user's profile. """
    if "account" not in flask.session:
        return flask.redirect("profile")

    users = cube.load_file("users")
    user = users[flask.session["account"]]

    if flask.request.method == "POST":
        if "remove" in flask.request.form:
            delete_photo()
            return alert("Profile picture removed.", "success", "profile")

        if "gpgkey" in flask.request.form:
            key = cube.gpg.import_keys(flask.request.form["gpgkey"])
            user["keys"] += cube.gpg.list_keys(keys=[key.fingerprints[0]])
            curr = user["keys"][-1]
            curr["fuids"] = ", ".join([uid.split()[-1][1:-1] for uid in curr["uids"]])
            cube.dump_file(users, "users")
            return alert("GPG key added.", "success", "meta")

        if "delete" in flask.request.form:
            del user["keys"][int(flask.request.form["delete"])]
            cube.dump_file(users, "users")

        if "photo" in flask.request.files:
            try:
                users = cube.load_file("users")
                delete_photo() #old profile picture not necessary anymore
                filename = PHOTOS.save(flask.request.files["photo"])
                users[flask.session["account"]]["pfp"] = PHOTOS.url(filename)
                users[flask.session["account"]]["pfpfilename"] = filename
                cube.dump_file(users, "users")
                return alert("Profile photo changed.", "success", "profile")
            except flask_uploads.UploadNotAllowed:
                return alert("Only files with the extentions {} are allowed.".format(format_exts(flask_uploads.IMAGES)), "warning", "self")
    return {}

def search() -> dict:
    """ Parses the user's search. Can be POST or GET method. """
    query = None
    if flask.request.method == 'POST':
        query = flask.request.form['query']
    elif flask.request.args.get('query', None) is not None:
        query = flask.request.args['query']
    else:
        return {}
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
TSLASH = "/" if params["tailing_slash"] else ""
NAMES = params["names"]
NAV = convert(params["order"])

PAGES = {"": (index, ["POST", "GET"]),
         "competitions": competitions,
         "algorithms": None,
         "weekly": {
             "lectures": lectures,
             "inhouse": None,
             },
         "contact": lambda: {"fb": cube.load_file("fb")},
         "archive":
             {
                "emails": lambda: {"emails": [{k: v if k != "body" else cube.markdown2.markdown(v) for k, v in email.items()}
                                              for email in cube.load_file("mails.json", "json", False)
                                             ]
                                  },
                "history": lambda: cube.parse_club(),
                "tips": None,
             },
         "vote":
             {
                "eligibility": lambda: cube.load_file("vote"),
                "admission": lambda: {"admission": cube.open_admission(), "sigs": cube.get_sigs()},
                "result": result,
             },
         "misc":
             {
                "stats": (stats, ["POST", "GET"]),
             },
         "profile": (profile, ["POST", "GET"]),
         "settings": (settings, ["POST", "GET"]),
         "search": (search, ["POST", "GET"])
        }

### Jinja ###

@app.template_filter()
def capitalize(s: str) -> str:
    """ Capitalizes the first character while keeping the rest the same case.
        Replaces Jinja's default filter. """
    return s[0].upper() + s[1:]

def URL() -> str:
    """ Dynamically generates a URL based on the request. """
    return params["url"] if cube.https else flask.request.url_root[:-1]

def furl_for(endpoint: str, filename: str=None, **kwargs: dict) -> str:
    """ Replacement for url_for. """
    return URL() + (flask.url_for(endpoint, filename=filename) if filename != None else ("/" if endpoint == "" else flask.url_for(endpoint, **kwargs)))

def furl(filename: str) -> str:
    """ Assumes a static endpoint. """
    return furl_for('static', filename)

def expose(d: dict, l: list) -> None:
    """ Adds functions to a dictionary. """
    for f in l:
        d[f.__name__] = f

# Basically a cache of variables that don't change
GLOBAL = {"pages": NAV,
          "URL": params["url"],
          "repo": cube.REPO,
          "TJ": cube.TJ,
          "updated": cube.github_commit_time(),
          "humanize": cube.humanize,
          "arrow": cube.arrow,
          "clubmail": cube.CONFIG["clubmail"],
         }

expose(GLOBAL, [furl, furl_for])

@app.context_processor
def GLOBALS() -> dict:
    """ Returns all the global variables passed to every template. """
    user = cube.load_file("users").get(flask.session.get("account", None), {})
    vars = {"vote_active": cube.load_file("vote")["vote_active"],
            "user": user
           }
    return cube.add_dict(GLOBAL, vars)

### Pages ###

def make_page(s: str, f=lambda: {}, methods=['GET']):
    """ Takes in a string which specifies both the url and the file name, as well as a function which provides the kwargs for render_template. """
    title = s.split("/")[-1]
    def func():
        val = f()
        if isinstance(val, dict):
            return flask.render_template((s if s != "" else "index") + cube.FILE, title=NAMES[title], **val)
        return val
    # Need distinct function names for Flask not to error
    func.__name__ = title if s != "" else "index"
    return app.route(("/{}" + TSLASH).format(s), methods=methods)(func)

def make_pages(d: dict, prefix="") -> None:
    """ Makes the entire site's pages. Recurs on nested dicts, taking file structure into account. """
    for key, value in d.items():
        if isinstance(value, dict):
            make_pages(value, prefix + "{}/".format(key))
        else:
            func, methods = ((value, ["GET"]) if not isinstance(value, tuple) else value)
            #don't need to store created function as it's already bound to the URL
            make_page(prefix + key, func if func is not None else lambda: {}, methods)

# https://stackoverflow.com/questions/14048779/with-flask-how-can-i-serve-robots-txt-and-sitemap-xml-as-static-files
@app.route("/sitemap.xml")
@app.route("/robots.txt")
def static_from_root():
    """ Serves a file from static, skipping the /static/. """
    return flask.send_from_directory(app.static_folder, flask.request.path[1:])

@app.route("/cookie")
def cookie() -> dict:
    """ Returns the user's cookies. """
    data = dict(flask.session)
    users = cube.load_file("users")
    if "account" in flask.session:
        user = users[flask.session["account"]]
        if len(user["keys"]) > 0:
            return str(cube.gpg.encrypt(flask.json.dumps(data), [k["fingerprint"] for k in user["keys"]], always_trust=True))
    return data

@app.route("/email")
def email():
    """ After requesting to be added to the email list, see if nonce matches. """
    emails = cube.load_file("emails")
    requests = emails["requests"]
    nonce = flask.request.args.get("nonce", None)
    if nonce in requests:
        email = requests[nonce]
        # Remove previous attempts
        emails["requests"] = {nonce: value for nonce, value in requests.items() if value != email}
        cube.dump_file(emails, "emails")
        cube.register_email(email)
        return alert("You have been added to the email list.", "success")
    return alert("Wrong nonce. Try registering again?", "danger")

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
    if 'oauth_state' not in flask.session:
        return "You shouldn't be here..."
    assert flask.request.args.get('state', None) == flask.session['oauth_state']
    code = flask.request.args.get('code', None)
    if flask.request.args.get('error', None) is not None or code is None:
        return alert("You must allow Ion OAuth access to vote!", "danger")
    oauth = cube.make_oauth(state=flask.session['oauth_state'])
    token = oauth.fetch_token(cube.TOKEN_URL, code=code, client_secret=cube.CONFIG["client_secret"])
    cube.save_token(token)

    return flask.redirect(flask.session.get("action", "profile"))

@app.route("/vote/vote", methods=["GET", "POST"])
def vote():
    if not cube.test_token():
        flask.session["action"] = flask.request.path
        return flask.redirect(flask.url_for("login"))

    vote = cube.load_file("vote")

    if not cube.valid_voter():
        return alert("You do not fullfill the requirements to be able to vote.", "warning")

    if not vote["vote_active"]:
        return alert("Stop trying to subvert democracy!!!", "danger")

    if flask.request.method == "POST":
        cube.add_vote(cube.get_name(), flask.request.form["vote"])
        return alert("<strong>Congrats!</strong> You have voted for {}.".format(flask.request.form['vote']))

    return flask.render_template(flask.request.path + cube.FILE, **vote, sorted_candidates=cube.get_candidates(), name=cube.get_name(), title="vote")

@app.route("/vote/run", methods=["GET", "POST"])
def run():
    if not cube.test_token():
        flask.session["action"] = flask.request.path
        return flask.redirect(flask.url_for("login"))

    vote = cube.load_file("vote")

    if not cube.valid_runner():
        return alert("You do not fullfill the requirements to be able to run.", "warning")

    if not vote["vote_active"]:
        return alert("Stop trying to subvert democracy!!!", "danger")

    signups = cube.get_signups()
    params = {"name": cube.get_name(),
              "years": cube.count_years(signups),
              "meetings": cube.count_meetings(signups, datetime.min, datetime.max),
              "annual_meetings": cube.count_meetings(signups),
              "year": cube.get_year(),
             }

    if flask.request.method == "POST":
        cube.store_candidate(cube.add_dict({"description": flask.request.form['description']}, params))
        return alert("<strong>Congrats!</strong> Your application has been registered.")

    return flask.render_template(flask.request.path + cube.FILE, **vote, **params, title="run")


# http://flask.pocoo.org/docs/1.0/patterns/errorpages/
# Catch-all exception handler
@app.errorhandler(Exception)
def exception_handler(e):
    app.logger.error('{}: {}'.format(type(e).__name__, e))
    return make_error_page(500)(InternalServerError())

def make_error_page(error: int):
    """ Makes an error page. """
    def f(e):
        body = e.get_body().strip().split("\n")
        title, descr = body[1][7:-8], body[-1][3:-4]
        return flask.render_template('error/{}{}'.format(error, cube.FILE), title=title, descr=descr), error
    return f

def make_error_pages(errors: list) -> None:
    """ Makes error pages. """
    for error in errors:
        app.errorhandler(error)(make_error_page(error))

make_error_pages(cube.get_errors())
make_pages(PAGES)

# https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
