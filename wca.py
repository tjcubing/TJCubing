import os, sys, json

# Parses the WCA export files
# TODO: autodownload latest WCA export

def wca_open(fname: str):
    """ Opens a file from the WCA export. """
    prefix = "WCA_export"
    folder = [x for x in os.listdir() if x[:len(prefix)] == prefix][0]
    return open("{}/{}_{}.tsv".format(folder, prefix, fname))

def parse(fname: str) -> list:
    """ Parses a file. """
    with wca_open(fname) as f:
        f.readline() #skip header
        return [(line.split("\t")[0], line.split("\t")[2]) for line in f]

def parse_mbld(s: str) -> float:
    """ Turns the WCA multiblind format into a number. """
    diff, time = 99 - int(s[0:2]), int(s[2:7])/60
    return diff + max((60 - time)/60, 0)

def sor(**kwargs: dict) -> int:
    """ Defines a metric. """
    return kwargs["rank"]

def kinch(**kwargs):
    mode, event, sing = kwargs["mode"], kwargs["event"], kwargs["sing"]
    return 100*(wrd[mode][event]/sing if event != "333mbf" else sing/wrd[mode][event])

def find_scores(metric: str) -> dict:
    """ Finds the score dictionary of WCA id : score """
    # remove mbld event from average
    scores = {p: {"Single": {event: 0 for event in events}, "Average": {event: 0 for event in events[:-1]}} for p in persons}

    for mode in modes:
        with wca_open("Ranks" + mode) as f:
            f.readline()
            cevent, crank = "", 0
            for line in f:
                line = line.split("\t")
                person, event, sing, rank = line[:4]
                rank, sing = int(rank), int(sing) if event != "333mbf" else parse_mbld(sing)
                if event != cevent:
                    wrd[mode][event], rankd[mode][cevent], cevent = sing, crank, event
                crank, scores[person][mode][event] = rank, funcs[metric](mode=mode, rank=rank, sing=sing, event=event)
        rankd[mode][event] = rank
        del rankd[mode][""]

    if metric == "sor":
        # fill in empty result with the number of competitors plus one
        for person in scores:
            for mode in modes:
                for event in scores[person][mode]:
                    if scores[person][mode][event] == 0:
                        scores[person][mode][event] = rankd[mode][event] + 1
    else:
        # events which don't have an average, replace with single
        navg = ["333mbf"]
        for event in navg:
            wrd["Average"][event] = wrd["Single"][event]
        for person in scores:
            for event in navg:
                scores[person]["Average"][event] = scores[person]["Single"][event]

        # events which take the better between single and average
        better = ["333bf", "333fm", "444bf", "555bf"]
        for person in scores:
            for event in better:
                scores[person]["Average"][event] = max(scores[person]["Single"][event], scores[person]["Average"][event])

    return scores

def sum_scores(scores: dict, name: str, mode: str="Single", avg: bool=False):
    return sum(scores[name][mode].values())/(len(events) if avg else 1)

def display(metric: str, scores: dict, mode: str="Single", reverse: bool=False, l: int=10):
    header = events[:-1] if metric == "sor" else events

    ranking = sorted(list(persons), key=lambda x: sum_scores(scores, x, mode), reverse=reverse)
    max_len = len(persons[max(ranking[:l], key=lambda x: len(persons[x]))])
    print(" "*(len(str(l)) + 1) + "Name" + " "*max_len + "Score\t" + "\t".join(header))
    for i in range(l):
        name, id = persons[ranking[i]], ranking[i]
        prefix = str(i + 1) + " "*(len(str(l)) - len(str(i + 1)) + 1) + name + " "*(max_len - len(name)) + "\t"
        print(prefix + str(round(sum_scores(scores, id, mode, reverse), 2)) + "\t" + "\t".join([str(round(scores[id][mode][event], 2)) for event in header]))

def sor_rank(rank: int, mode: str="Single") -> int:
    """ Returns the place in the world that rank would be. """
    ranking = sorted(list(persons), key=lambda x: sum_scores(sor_scores, x, mode))
    for i in range(len(ranking)):
        if rank <= sum_scores(sor_scores, ranking[i], mode):
            return i + 1

def kinch_rank(kinch_score: float) -> int:
    ranking = sorted(list(persons), key=lambda x: sum_scores(kinch_scores, x, "Average"), reverse=True)
    for i in range(len(ranking)):
        if kinch_score >= sum_scores(kinch_scores, ranking[i], "Average", True):
            return i + 1

events = [x[0] for x in sorted(parse("Events"), key=lambda x: int(x[1]))[:-3]]
persons = {p[0]: p[1] for p in parse("Persons")}
wrd, rankd = {"Single": {}, "Average": {}}, {"Single": {}, "Average": {}}

modes = ["Single", "Average"]
funcs = {"sor": sor, "kinch": kinch}

sor_scores, kinch_scores = find_scores("sor"), find_scores("kinch")

with open("files/wca/cache.json", "w") as f:
    json.dump({"wrs": wrd, "ranks": rankd}, f, indent=4, sort_keys=True)

if __name__ == "__main__":
    print(sor_rank(int(sys.argv[1]), "Single"),
          sor_rank(int(sys.argv[2]), "Average"),
          kinch_rank(float(sys.argv[3])))

    # display("sor", sor_scores, "Single", False, 30)
    # display("kinch", kinch_scores, "Average", True, 30)

    # print(sor_rank(3805, "Single"))
    # print(sor_rank(1483, "Average"))
    # print(kinch_rank(59.57))

