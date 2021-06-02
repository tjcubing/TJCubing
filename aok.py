"""
A fast, binary search tree-based algorithm for computing a series of aoK's
for a given list of times in O(N log K) for a list of length N

binary tree, initially record where cutoff for < or > 5% is.
keep track of sum of left/right bounds.
look at upper bound.
when removing/adding time, lower/lower - no effect
upper/upper - subtract old and add new
lower/upper - subtract old, use nearest strat (find closest higher in tree)
upper/lower - subtract old, use nearest strat (find closest lower in tree)
when removing/adding time, pointer moves to next time
(at most one value changes).
move pointer to left, right, parent.
left: go left then go as right as possible - closest lower.
right: go right then go as left as possible - closest higher.
parent: can only follow parent up (one child is where you came from,
other child is further away) - could be either.
"""
from bst import BST

def avgs(times: list, k: int=5) -> list:
    """ Finds the rolling aok averages for a given list. """
    blocks = stats.block(times, k, roll=True)

if __name__ == "__main__":
    import statistics as stats

    times = [9.58, 10.23, 23.42, 5.63, 42.53, 10.34, 11.58, 12.47]
    stats_avgs = list(map(stats.ao, stats.block(times, roll=True)))
    print(stats_avgs)
    print(avgs(times))

