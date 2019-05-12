import time, pickle
from datetime import datetime
import flask
import cube

app = flask.Flask(__name__)

FILE = ".html.j2"
WAIT = 2.628e6 #seconds in a month

@app.route('/')
def index():
    #print(flask.request, flask.session, flask.g)
    return flask.render_template("index" + FILE)

@app.route('/competitions')
def competitions():
    last, comps = cube.get_cached_comps()
    if time.time() - last > 2.628e6:
        comps = cube.get_comps()

    last = datetime.fromtimestamp(last).strftime("%A, %B %d, %Y at %I:%M:%S.%f %p")
    return flask.render_template("competitions" + FILE, last=last, comps=comps)

@app.route('/search', methods=['POST', 'GET'])
def search():
    query = None
    if flask.request.method == 'POST':
        query = flask.request.form['query']
    elif flask.request.args.get('query', None) is not None:
        query = flask.request.args['query']

    return f"User searched for: {query}" if query is not None else "hi? not a POST request but ok."
