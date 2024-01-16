#!/usr/bin/env python3

import sys

from decimal import getcontext
from functions import (
    initialize_cost_table,
    explore,
    collect_paths,
    print_path,
    getArguments,
)
from constants import (
    allowed_groups,
    start_angles,
    find_angles,
    avoid_angles,
)

# ALGORITHM OVERVIEW
#
# There are 65536 angles possible, ranging 0x0000-0xFFFF.  There are several
# motions available that change the angle in different ways.
#
# The state of Link's angle is represented by a directed graph.  The nodes are
# angles; the edges are motions between angles.  We want to navigate the graph
# from one node to another in a way that minimizes the cost.
#
#     0x0000 -----(ess left)---------> 0x0708
#        \
#         --(sidehop sideroll left)--> 0xF070
#      ...
#
# The camera is pretty complicated, so some motions don't just "rotate Link
# X units clockwise".  In other words, they're not linear, or even invertible.
# We treat individual motions as opaque functions from angles to angles.  Those
# functions are located in "motions.py".
#
# The algorithm is:
#    1. Construct an empty graph.
#    2. Mark edges in the graph, exploring the fastest nodes first.
#    3. Walk backwards through the graph, starting from the final angle.
#
# Angles can be reached from many motion sequences.  The scoring we use won't
# be perfect for everyone, so to allow some variation we record multiple
# motions into each angle.  Specifically, at each node, we record the best
# edge into it for a given motion, treating our scoring as perfect.  Then, at
# the end, we return paths that are roughly as fast as the best path.  This
# seems to work well.


def main():
    getcontext().prec = 4  # Decimal to 4 places
    sys.setrecursionlimit(5000)  # basic searches can get a lil' wild

    initialize_cost_table()

    # Create a graph starting at the given angles.
    graph = explore(start_angles, avoid_angles)
    paths = []

    # Collect the 5 fastest sequences of the first 50 visited.  The fastest
    # sequence collected is at least tied as the fastest sequence overall.

    for curAngle in find_angles:
        angle = int(curAngle, 16)
        paths.extend(collect_paths(graph, angle, sample_size=35, number=4))

    paths.sort()

    for cost, angle, path in paths:
        print(f"cost: {cost}\n-----")
        print_path(angle, path)
        print("-----\n")

    if len(paths) == 0:
        print("No way to get to the desired angle!")
        print("Add some more motions.")


if __name__ == "__main__":
    args = getArguments()

    for grp in args.allowedGroups:
        if "_" in grp:
            grp = grp.replace("_", " ")
        allowed_groups.append(grp)

    for angle in args.startAngles:
        start_angles.append(int(angle, 16))

    find_angles = args.findAngles
    avoid_angles = args.avoidAngles

    assert len(allowed_groups) > 0
    assert len(start_angles) > 0
    assert len(find_angles) > 0
    if avoid_angles is not None:
        assert len(avoid_angles) > 0
    else:
        avoid_angles = []

    main()
