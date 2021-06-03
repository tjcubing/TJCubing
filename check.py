import argparse, json
# checks whether the voters have the required number of meetings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="vote checker")
    parser.add_argument("-n", "--name", required=True,
                        help="file containing names.")
    parser.add_argument("-u", "--username", required=True,
                        help="file containing usernames.")
    parser.add_argument("-s", "--signups", required=True,
                        help="json file containing signup data.")

    args = parser.parse_args()

    with open(args.name) as f:
        names = [line.strip() for line in f]

    with open(args.username) as f:
        usernames = [line.strip() for line in f]

    with open(args.signups) as f:
        signups = json.load(f)

    assert len(names) == len(usernames), "number of names not equal to number of usernames"
    n = len(names)

    valid, invalid, not_registered = [], [], []
    for i in range(n):
        k = usernames[i]
        ((valid if signups[k] >= 4 else invalid) if k in signups else \
         not_registered).append(i)

    print(f"{n} votes: {len(valid)} valid, {len(invalid)} invalid, {len(not_registered)} not registered")

    print("invalid:")
    for i in invalid:
        print(f"{names[i]:>30} ({usernames[i]:<20}): {signups[usernames[i]]}")

    print("not registered:")
    for i in not_registered:
        print(f"{names[i]:>30} ({usernames[i]:<20})")

