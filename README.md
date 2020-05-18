# TJ Cubing Website

Currently the official [website for Rubik's Cube Club](https://activities.tjhsst.edu/cubing/) at [Thomas Jefferson High School for Science and Technology](https://tjhsst.fcps.edu/).

## Setup
This project uses [Flask](http://flask.pocoo.org/) as a Python backend.  
Install [Pipenv](https://docs.pipenv.org/en/latest/install/#installing-pipenv) and then run `pipenv install` to install all of the Python dependencies.

Styling is done through [Sass](https://sass-lang.com/). Compile the custom sass (.SCSS) file into CSS via `gulp watch`.

Website primarily made through [Bootstrap](https://getbootstrap.com).

[Gulp](https://gulpjs.com/) is used in a hacky way to copy files from `node_modules` to `static/` as well as do some other miscellaneous tasks, including concatenating and minimizing JavaScript, and images. Run `gulp build` to build the website. 

[TJ Oauth](https://ion.readthedocs.io/en/latest/developing/oauth.html) is used for the voting system.

[WCA Oauth](https://github.com/thewca/worldcubeassociation.org/wiki/OAuth-documentation-notes) is used for verifying TJ records.

## File Structure

- /app.py: Main file which actually serves the website. Don't use:

    ```python
    if __name__ == '__main__':
      app.run()
    ```

    as there are [glitches with the automatic file reloading](http://flask.pocoo.org/docs/1.0/server/#in-code).
    Instead use: 
    
    ```bash
    pipenv run flask run 
    ```

    or, make it available to other devices on the same network:
    ```bash
    pipenv run flask run --host='0.0.0.0'
    ```

    or, to use https (this is necessary for testing [Fido U2F](https://www.yubico.com/authentication-standards/fido-u2f/)):
    ```bash
    pipenv run flask run --cert=adhoc
    ```
    Also, be sure to go to https://localhost:5000/ instead of https://127.0.0.1:5000/.

    Using https will make Chrome say "Your connection is not private".
    Recently, Google removed the ability to click "Advanced" -> proceed anyways. 
    To get around this, type "thisisunsafe" and hit enter.

    You might be tempted to background the process. 
    On my computer, this makes the website run _incredibly_ slowly.
    Instead, open a terminal window and just let it vibe there.

- /cube.py: Miscellaneous helper library.

- /files/: Folder for *.json and *.py configuration and disk files.
  - config.json: File not git committed (API keys).
    - "states": List of strings specifying which states competitions can be from.
      - recommended: ["Virginia", "Maryland", "West Virginia", "Pennsylvania"]
    - "origin": point from which competition distance is calculated, should be at TJ.
      - recommended: "38.818573,-77.168757" 
    - "key": [Google distancematrix API](https://developers.google.com/maps/documentation/distance-matrix/start) key.
    - "flask_config": [Config file for Flask](http://flask.pocoo.org/docs/1.0/config/).
      - SECRET_KEY: Necessary for [Flask's session](http://flask.pocoo.org/docs/1.0/quickstart/#sessions) dictionary which stores an encrypted cookie between user sessions.
        - Generate this via `cube.gen_secret_key()`.
      - SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS: Used for [generating sitemap.xml](https://flask-sitemap.readthedocs.io/en/latest/). 
        - Set to `True`.
    - "client_id", "client_secret", "redirect_uri": parameters related to [OAuth](https://requests-oauthlib.readthedocs.io/en/latest/).
      - Go to the linked Ion page and follow their instructions.
    - "club": Dict describing the club.
      - "id": 252, 
      - "url": "https://ion.tjhsst.edu/api/activities/152", 
      - "name": "Rubiks Cube Club"
  - site.json: 
  - vote.json: File storing information relating to the voting system.
    - "vote_active": Boolean which indicates whether users can vote or not.
    - "length": Integer which sets the maximum length of a candidate's post.
    - "min_meetings": Minimum number of meetings a member needs to attend to vote.
    - "ends_at": Time when voting stops in %m/%d/%y %I:%M %p.
    - "position": Position the candidates are running for.
    - "votes": Contains person, person who they voted for pairs (dict).
    - "candidates": List of candidates, represented by a dict.
  - club.json: Generated by `cube.save_club_history`.
  - comps.json: Generated by `cube.get_comps`.

- /templates/: Folder that Flask uses to display *.html files/
  - base.html.j2: Base file (loads headers, loads footers, and defines a content block).
  - header.html.j2: Header.
  - footer.html.j2: Footer. 
  - funcs.html.j2: Collection of Jinja macros and other globals


- /static/bootstrap: Boostrap core files, [don't modify](https://getbootstrap.com/docs/4.3/getting-started/theming/).
  - If you want to update Boostrap, simply download it and install to this location.
  - Be sure to include SCSS source files. 


- /static/scss/custom.css: Global stylesheet.
  - /static/css/custom.css: compiled CSS. Don't modify directly as it's compiled from SCSS.

- /static/img: Images.
- /static/pdfs: LaTeX Lectures.
- /static/js: Includes jQuery and Popper.js.

## Future Plans
- Recreate Twisttheweb (used to be an online timer for racing your friends, now is a mosaic site)
- Switch from JSON to SQLAlchemy database
- Add optional breadcrumbs
- Python tests
- New pages
  - Hardware page (links to Cubicle, SCS, my hardware table)
  - Hardware, Boron treatment, magnetization (in misc/guides)
  - Make nav bar recursive
- Admin Page
  - Ability to edit files through a file editor 
  - Refresh buttons
    - meetings in history
    - sitemap
    - rendered templates for search
      - suffix trees for search feature
  - Simulate jumps forward in time
  - Request increase in power, requests go to logfile, logfile parsed and delivered as notifications page to admin
- Yubikey U2F 2FA
- Ability to delete emails from the archive
- Congratulate when a new TJ record is set
- Calculate sum of ranks (SOR) and Kinch score relative to TJ rankings
- Ability to click on an event and see the TJ ranking, similar to the WCA site
- Hall of Fame (each person with name + year + WCA profile + picture)
- Stronger profiles
  - Click on a name and it shows their history in all the weekly comps, graph of ao5 over time, TJ records held, etc.
- GPG sign emails
