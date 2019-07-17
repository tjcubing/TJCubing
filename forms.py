from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, DecimalField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Email
import flask_uploads

# Library that contains all the forms and upload patterns

LENGTH = 200

# Create an upload set
times = flask_uploads.UploadSet("times", flask_uploads.DATA)
photos = flask_uploads.UploadSet("photos", flask_uploads.IMAGES)

def format_exts(exts: list):
    """ Returns a formatted list of extentions. """
    return ", ".join(["." + ext for ext in exts])

class UploadForm(FlaskForm):
    file = FileField("Choose file", [FileRequired(), FileAllowed(times, "Data files only.")])

class PhotoForm(FlaskForm):
    photo = FileField("", [FileRequired(), FileAllowed(photos, "Only files with the extentions {} are allowed.".format(format_exts(flask_uploads.IMAGES)))],
                     render_kw={"style": "display: none;", "onchange": "form.submit()"})

class StatsForm(FlaskForm):
    times = TextAreaField("", [DataRequired()], render_kw={"class": "form-control", "rows": 5, "placeholder": "Paste in your times"})

class RunForm(FlaskForm):
    description = TextAreaField("", render_kw={"class": "form-control", "rows": 5, "placeholder": "Type in your message", "maxlength": LENGTH})

class GPGForm(FlaskForm):
    gpgkey = TextAreaField("Key", [DataRequired()], render_kw={"class": "form-control", "rows": 10, "placeholder": "Begins with '-----BEGIN PGP PUBLIC KEY BLOCK-----'"})

class EmailForm(FlaskForm):
    email = StringField("", [DataRequired(), Email()], render_kw={"class": "form-control", "type": "email", "placeholder": "Enter email"})

class LoginForm(FlaskForm):
    username = StringField("Username", render_kw={"class": "form-control", "placeholder": "Enter username"})
    password = PasswordField("Password", render_kw={"class": "form-control", "placeholder": "Password"})

class SignupForm(LoginForm):
    confirm = PasswordField("Confirm Password", render_kw={"class": "form-control", "placeholder": "Retype the password"})

class MailForm(FlaskForm):
    recipients = TextAreaField("", render_kw={"class": "form-control", "rows": 1})
    subject = StringField("Markdown", [DataRequired()], render_kw={"class": "form-control", "placeholder": "Subject"})
    email = TextAreaField("", [DataRequired()], render_kw={"class": "form-control", "rows": 10, "placeholder": "Write the email here"})
    log = BooleanField("Log to archive?", default="checked")

class HTTPForm(FlaskForm):
    http = DecimalField("", [DataRequired()], render_kw={"class": "form-control", "placeholder": "Type in a HTTP response status code..."})
