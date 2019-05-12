import json, pickle, time
import requests
from bs4 import BeautifulSoup

# Helper library to query the WCA for competitions and other miscellaneous tasks
# TODO: mailing list, switch key to key from tjcubingofficers@gmail.com

with open("config.json") as f:
    config = json.load(f)

URL = "https://www.worldcubeassociation.org/competitions"

class Comp:

    def __str__(self):
        return f"{self.name}"

    def __init__(self, url, name, location, venue, date):
        self.url, self.name, self.location, self.venue, self.date = url, name, location, venue, date
        self.gps = self.km = self.timestr = self.time = None

def get_comps() -> list: #TODO: get events, TJ kids competing.
    """ Parses the WCA website and returns a list of competitors.
        Calls Google's distancematrix API to get distances to the competitions
    """
    local_comps = []
    soup = BeautifulSoup(requests.get(URL + "?region=USA&state=present&display=list").text, 'html.parser')
    for comp in soup("li", class_="list-group-item not-past"):
        info = list(filter(lambda x: x != len(x)*" ", comp.get_text().strip().split("\n")))
        if info[2].split(", ")[-1] in config["states"]:
            local_comps.append(Comp(URL + comp.find("a").get('href')[13:], info[1], info[2], info[3], info[0]))
            temp = BeautifulSoup(requests.get(local_comps[-1].url).text, 'html.parser')
            local_comps[-1].gps = temp.find("dt", string="Address").next_sibling.next_sibling.find("a").get('href').split("/")[-1]

    param = {'origins':config["origin"], 'destinations':"|".join([comp.gps for comp in local_comps]), 'key':config["key"], 'units':'imperial'}

    for i, thing in enumerate(requests.get("https://maps.googleapis.com/maps/api/distancematrix/json", params=param).json()['rows'][0]['elements']):
        local_comps[i].km = thing['distance']['text']
        local_comps[i].timestr = thing['duration']['text']
        local_comps[i].time = thing['duration']['value']

    local_comps.sort(key=lambda comp: comp.time) #sort by time to travel

    with open("comps.pickle", "wb") as f:
        pickle.dump((time.time(), local_comps), f)

    return local_comps

def get_cached_comps() -> tuple:
    """ Returns a (time, list of comps) tuple from a disk file. """
    with open("comps.pickle", "rb") as f:
        return pickle.load(f)

# <?php
# // Check for empty fields
# if(empty($_POST['name'])  		||
#    empty($_POST['email'])	||
#    !filter_var($_POST['email'],FILTER_VALIDATE_EMAIL))
#    {
# 	echo "No arguments Provided!";
# 	return false;
#    }
#
# $name = $_POST['name'];
# $email_address = $_POST['email'];
#
# // Create the email and send the message
# $to = 'davidzhao058@gmail.com'; // Add your email address inbetween the '' replacing yourname@yourdomain.com - This is where the form will send a message to.
# $email_subject = "ADD TO EMAIL LIST:  $name";
# $email_body = "Name: $name\nEmail: $email_address";
# $headers = "From: noreply@tjcubing.org\n"; // This is the email address the generated message will be from. We recommend using something like noreply@yourdomain.com.
# $headers .= "Reply-To: $email_address";
# mail($to,$email_subject,$email_body,$headers);
# return true;
# ?>
