import math
import pandas as pd

# Computes various statistics

DNF = float("INF")

def parse_time(s: str) -> float:
    """ Parses a string to a time. """
    if s[0] == "(":
        s = s[1:-1]

    if s[-1] == "+":
        return parse_time(s[:-1])
    elif "DNF" in s:
        return DNF
    return float(s)

def mean(l: list) -> float:
    """ Returns the mean of a list, rounded to two decimal places. """
    return round(sum(l)/len(l), 2)

def ao(l: list, k: float=0.05) -> list:
    """ Drops k% of the solves in an average. """
    drop = math.ceil(k*len(l))
    return mean(sorted(l)[drop:-drop])

def block(l: list, k: int=5, roll=False) -> list:
    """ Combines a list into k size buckets. """
    if not roll:
        return [l[i: i + k] for i in range(0, len(l) - 4, k)]
    bucket = l[:k]
    times = []
    for i in range(k, len(l)):
        times.append(bucket)
        bucket = bucket[1:]
        bucket.append(l[i])
    return times

def process(times: list) -> tuple:
    """ Returns the statistics given a time list. """
    avgs = list(map(ao, block(times)))
    return "mo{}ao5".format(len(avgs)), mean(avgs), min(avgs)

def parse(text: str) -> list:
    """ Parses a CStimer CSV file. """
    session = pd.read_csv(text, sep=";")
    return list(map(parse_time, session["Time"].apply(str)))

def parse_cstimer_text(text: str) -> list:
    """ Parses csTimer text. """
    return [parse_time(line.split()[1]) for line in text.split("\n")[4:]]

def parse_dctimer_text(text: str) -> list:
    """ Parses DCTimer text. """
    i = None
    for j, line in enumerate(text.split("\n")):
        if "," in line:
            i = j
            break
    if i is None:
        return []
    return list(map(parse_time, text.split("\n")[i].split(":")[-1].split(", ")))

def parse_text(text: str) -> list:
    """ Parses a text file. """
    try:
        mode = text.split()[2]
        parsers = {"csTimer": parse_cstimer_text,
                   "DCTimer": parse_dctimer_text,
                  }
        return parsers[mode](text.strip())
    except:
        return []
