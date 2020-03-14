import time
from datetime import datetime
from datetime import timedelta
import arrow
import humanize

def get_year() -> int:
    """ Returns the year as a number """
    return datetime.today().year

def footer_time() -> float:
    """ Returns the current time in the footer format. """
    return time.strftime("%Y-%m-%d %X %z", time.localtime())

def ion_date(date: str) -> datetime:
    """ Converts an ION formatted date to a datetime object. """
    return datetime.strptime(date, "%Y-%m-%d")

def short_date(date: str) -> float:
    """ Converts my arbitrary shorthand date to a UNIX time. """
    return datetime.strptime(date, "%m/%d/%y %I:%M %p").timestamp()

def jchoi_date(date: str) -> float:
    """ Converts Justin Choi's file naming scheme to a UNIX time. """
    return datetime.strptime(date, "%m.%d.%Y").timestamp()

def unix_to_human(time: float) -> str:
    """ Returns a human-readable time from a UNIX timestamp. """
    return datetime.fromtimestamp(time).strftime("%A, %B %d, %Y at %I:%M:%S.%f %p")

def unix_to_date(time: float) -> str:
    """ Returns a date from a UNIX timestamp. """
    return datetime.fromtimestamp(time).strftime("%m/%d/%Y")

def summer(year: int) -> datetime:
    """ Returns a slightly arbitrary date representing the end of school. """
    return datetime(year, 7, 10)
