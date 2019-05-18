import time, os
from flask_frozen import Freezer
import cube

OUT = "rendered_templates"

#Change URL format to end with a tailing slash
site = cube.load_file("site")
site["tailing_slash"] = True
cube.dump_file(site, "site")

from app import app

app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True
app.config['FREEZER_REDIRECT_POLICY'] = 'ignore'

freezer = Freezer(app)

# if __name__ == '__main__':
#     freezer.freeze()

#Undo changes
site["tailing_slash"] = False
cube.dump_file(site, "site")

try:
    os.mkdir(OUT)
except FileExistsError:
    pass

def search(path="build", pages=[]):
    for file in os.listdir(path):
        new = path + "/" + file
        if os.path.isdir(new):
            search(new, pages)
        else:
            if new.split("/")[-1] == "index.html":
                pages.append(new)
    return pages

pages = search()
for page in pages:
    tokens = page.split("/")
    path = "/" + (tokens[-2] if len(tokens) > 2 else "index") + ".html"
    original = "templates" + ("/" if len(tokens) > 3 else "") + "/".join(tokens[1:-2]) + path + ".j2"
    with open(page) as f:
        text = f.read()
    with open(OUT + path, "w") as f:
        f.write(text)

    os.utime(OUT + path, (time.time(), os.path.getmtime(original))) #set modification time to be equal
