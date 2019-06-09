import math
import pandas as pd

# Computes various statistics

DNF = float("INF")

def parse_time(s: str) -> float:
    """ Parses a string to a time. """
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

def parse(text: str):
    """ Parses a CStimer CSV file. """
    session = pd.read_csv(text, sep=";")
    times = list(map(parse_time, session["Time"]))
    avgs = list(map(ao, block(times)))
    return "mo{}ao5".format(len(avgs)), mean(avgs), min(avgs)
