# TJ Cubing Website

Currently the official website for Rubik's Cube Club at [Thomas Jefferson High School for Science and Technology](https://tjhsst.fcps.edu/).

## Setup
This project uses [Flask](http://flask.pocoo.org/) as a Python backend.  
Install [Pipenv](https://docs.pipenv.org/en/latest/install/#installing-pipenv) and then run `pipenv install` to install all of the Python depdendancies.

Styling is done through [Sass](https://sass-lang.com/). Compile the custom sass (.SCSS) file into CSS via `sass static/scss/custom.scss static/css/custom.css`.

Website primarily made through [Bootstrap](https://getbootstrap.com).

[TJ Oauth](https://ion.readthedocs.io/en/latest/developing/oauth.html) is used for the voting system.

## File Structure

- /app.py: Main file which actually serves the website. Don't use:

    ```python
    if __name__ == '__main__':
      app.run()
    ```
      
    as there are [glitches with the automatic file reloading](http://flask.pocoo.org/docs/1.0/server/#in-code).
    Instead use: 
    
    ```bash
    export FLASK_APP=app.py
    export FLASK_ENV=development
    pipenv run flask run
    ```

- /cube.py: Miscellaneous helper library.

 
- /config.json: File not git commited (API keys).
  - "states": List of strs specifing which states competitions can be from.
    - recommended: ["Virginia", "Maryland", "West Virginia", "Pennsylvania"]
  - "origin": point from which competition distance is calculated, should be at TJ.
    - recommended: "38.818573,-77.168757" 
  - "key": [Google distancematrix API](https://developers.google.com/maps/documentation/distance-matrix/start) key.
  - "flask_secret_key": necessary for [Flask's session](http://flask.pocoo.org/docs/1.0/quickstart/#sessions) dictionary which stores an encrypted cookie between user sessions.
    - Generate this via `cube.gen_secret_key()`.
  - "client_id", "client_secret", "redirect_uri": parameters related to [OAuth](https://requests-oauthlib.readthedocs.io/en/latest/).
    - Go to the linked Ion page and follow their instructions.


- /comps.pickle: Cache of competitions


- /templates/base.html.j2: Base file (loads headers, loads footers, and defines a content block)
  - templates/header.html.j2: header
  - templates/footer.html.j2: footer 
  - other pages in templates self-explanatory


- /static/bootstrap: Boostrap core files, [don't modify](https://getbootstrap.com/docs/4.3/getting-started/theming/).
  - If you want to update Boostrap, simply download it and install to this location.
  - Be sure to include SCSS source files. 


- /static/scss/custom.css: Global stylesheet.
  - /static/css/custom.css: compiled CSS. Don't modify directly as it's compiled from SCSS.
  
  
- /static/img: Images.
- /static/pdfs: LaTeX Lectures.
- /static/js: Includes jQuery and Popper.js.
