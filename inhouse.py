import os, glob, csv

DNF = "9999"

# Parses the in house comp results
for file in glob.glob("*.csv"):
    fname = file.split("-")[-1].strip().split(".")[0].replace("_", ".")
    fname = fname[:-2] + "20" + fname[-2:]

    with open(file) as csvfile:
        f = csv.reader(csvfile)
        data = [row[0] + "|" + " ".join(token if token != DNF else "DNF" for token in row[1:-1]) for row in f]

    with open("src/txt/" + fname + "res", "w") as f:
        f.write("\n".join(data) + "\n")

    with open("src/txt/" + fname + "scr", "w") as f:
        f.write("We don't have scrambles!")
