# syncs json files of club history
import json

with open("files/archive/4-28-2020/club.json") as f:
    old = json.load(f)

with open("files/archive/4-29-2020/club.json") as f:
    new = json.load(f)

def present_in(d: dict, date: str) -> str:
    """ Returns the key if the date is in the dictionary, otherwise None. """
    for k in d["scheduled_on"]:
        if d["scheduled_on"][k]["date"] == date:
            return k

def sync(old: dict, new: dict) -> dict:
    """ Syncs two dictionaries. """
    for k, v in new["scheduled_on"].items():
        if present_in(old, v["date"]) is None:
            old["scheduled_on"][k] = v
    return old

d = sync(old, new)
with open("files/club.json", "w") as f:
    json.dump(d, f, indent=4, sort_keys=True)
