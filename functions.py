import heapq

from decimal import Decimal
from argparse import ArgumentParser as Parser, ArgumentTypeError
from typing import Optional
from motions import table
from constants import (
    COST_FLEX,
    COST_TABLE,
    MOVEMENT_OPTIONS,
    BASIC_COSTS,
    COST_CHAINS,
    TARGET_BEFORE,
    allowed_groups,
    Node,
    Edge,
    empty_node,
)


def maybe_add_edge(
    graph: list[Node], edge: Edge, to_angle: Node, avoid_angles: list[tuple[int, int]]
):
    """
    Add an edge to an angle, but only if the edge is the fastest way to get to
    the node for a given motion.

    Returns True if the edge was added, False if it wasn't.
    """

    def min_none(x, y):
        return x if (x is not None and x < y) else y

    to_node = graph[to_angle]
    edges_in = to_node.edges_in

    def add_edge():
        edges_in[edge.motion] = edge
        best = min_none(to_node.best, edge.cost)
        graph[to_angle] = Node(edges_in, best)

    for avoid_range in avoid_angles:
        if avoid_range[0] <= edge.from_angle and avoid_range[1] >= edge.from_angle:
            if TARGET_BEFORE[edge.motion]:
                # not an allowed motion based on the avoid params
                return False

    if to_node.best == None:
        add_edge()  # first edge to the node
        return True

    if edge.cost > to_node.best + COST_FLEX:
        # edge costs too much
        return False

    if (edge.motion not in edges_in) or (edge.cost < edges_in[edge.motion].cost):
        # first edge via this motion, or cheaper than the previous edge via this motion
        add_edge()
        return True

    # have already found this node, via this motion, at least as quickly
    return False


def edges_out(graph: list[Node], angle: Node, last_motion, last_cost):
    """
    Iterator of edges out of an angle, given some particular previous motion and
    cost.  Needs the previous motion to calculate the cost of a chained motion.
    """

    if graph[angle].best < last_cost:
        # skip all edges if this edge isn't the cheapest way out
        # misses some valid edges, but it doesn't seem to matter much
        return

    for motion, cost_increase in COST_TABLE[last_motion].items():
        new_angle = table[motion](angle)

        if new_angle is None:
            continue

        to_angle = new_angle & 0xFFFF
        from_angle = angle
        cost = last_cost + cost_increase

        yield (to_angle, Edge(from_angle, motion, cost))


def explore(starting_angles: list[int], avoid_angles: tuple[int, int]):
    """Produce a graph from the given starting angles."""

    graph = [empty_node() for _ in range(0xFFFF + 1)]
    queue = []  # priority queue of '(edge_cost, from_angle, last_motion)'
    seen = 0

    for angle in starting_angles:
        edges_in = {None: Edge(from_angle=None, motion=None, cost=0)}
        best = 0

        graph[angle] = Node(edges_in, best)
        heapq.heappush(queue, (Decimal(0.0), angle, None))
        seen += 1

    previous_cost = 0  # only print status when cost increases

    while len(queue) > 0:
        if seen == (0xFFFF + 1):
            # have encountered all nodes, exit early
            # misses some valid edges, but it doesn't seem to matter much
            break

        (cost, angle, motion) = heapq.heappop(queue)

        if cost > previous_cost + Decimal(1.0):
            print(f"Exploring ({len(queue)}), current cost at {cost}", end="\r")
            previous_cost = cost

        for to_angle, edge in edges_out(graph, angle, motion, cost):
            if graph[to_angle].best == None:
                seen += 1

            if maybe_add_edge(graph, edge, to_angle, avoid_angles):
                # this is a new or cheaper edge, explore from here
                heapq.heappush(queue, (edge.cost, to_angle, edge.motion))

    print("\nDone.")
    return graph


def cost_of_path(path):
    # A path is a list of motions, e.g. ["ess up", "ess up", "turn left"].
    cost = 0
    last = None
    for next in path:
        cost += COST_TABLE[last][next]
        last = next
    return cost


def navigate_all(
    graph: list[Node],
    angle: int,
    path: Optional[list] = None,
    seen: Optional[set[int]] = None,
    flex: Decimal = COST_FLEX,
):
    """
    Iterator of paths to a given angle, whose costs differ from the best
    path by no more than COST_FLEX.

    The first yielded path is guaranteed to be the cheapest (or tied with other
    equally cheapest paths), but the second path is NOT necessarily
    second-cheapest (or tied with the first).  The costs of yielded paths are
    not ordered except for the first.

    Yields values of the form
        (angle, path)
    where 'angle' is an integer 0x0000-0xFFFF, and 'path' is a list of motions.
    """

    # 'flex' starts at the maximum permissible deviation from the optimal path.
    # As the function recurses, 'flex' decreases by the deviation from optimal
    # at each node.

    if path is None:
        # instantiate new objects in case the function is called multiple times
        path = []
        seen = set()

    node = graph[angle]

    if None in node.edges_in:
        # this is a starting node
        yield angle, list(reversed(path))

    elif angle in seen:
        # found a cycle (possible by e.g. 'ess left'->'ess right', where 'flex'
        # lets the running cost increase a little)
        pass

    else:
        seen.add(angle)

        # explore the fastest edges first
        # note that this doesn't guarantee the ordering of paths; some paths
        #   through a slower edge at this step might be faster in the end
        # however, A fastest path will be yielded first
        edges = sorted(node.edges_in.values(), key=lambda e: e.cost)

        for edge in edges:
            new_flex = (node.best - edge.cost) + flex

            if new_flex < 0:
                # ran out of flex!  any paths from here will cost too much
                break

            path.append(edge.motion)
            yield from navigate_all(graph, edge.from_angle, path, seen, new_flex)
            path.pop()

        seen.remove(angle)


def print_path(angle: int, path):
    # keep track of repeated motions to simplify the path reading
    prev_motion = None
    iterations = 1
    motions_output = []

    print(f"start at {angle:04X}")

    for motion in path:
        if prev_motion == motion:
            # keep track of how many times a motion is repeated
            iterations += 1
        elif prev_motion:
            # once it stops repeating, add it to the motion list
            motions_output.append(
                {"motion": f"{iterations} {prev_motion}", "angle": f"0x{angle:04x}"}
            )
            iterations = 1

        # update the angle using the current motion and set prev_motion
        angle = table[motion](angle) & 0xFFFF
        prev_motion = motion

    # finally, run one last time
    motions_output.append(
        {"motion": f"{iterations} {prev_motion}", "angle": f"0x{angle:04x}"}
    )

    # get the padding amount based on the length for the largest motion string
    text_length = len(max([output["motion"] for output in motions_output], key=len))
    for motion in motions_output:
        # print out each motion
        print(f"{motion['motion']:<{text_length}} to {motion['angle']}")


def collect_paths(
    graph: list[Node], angle: int, sample_size: int = 20, number: int = 10
):
    """Sample 'sample_size' paths, returning the 'number' cheapest of those.

    Returns a list of
        (cost, angle, path)
    where 'cost' is the float cost, 'angle' is an integer 0x0000-0xFFFF,
    and 'path' is a list of motions.
    """

    paths = []

    for angle, path in navigate_all(graph, angle):
        paths.append((cost_of_path(path), angle, path))

        if len(paths) == sample_size:
            break

    paths.sort()
    return paths[:number]


def initialize_cost_table():
    COST_TABLE[None] = BASIC_COSTS.copy()

    for motion, cost in BASIC_COSTS.items():
        COST_TABLE[motion] = BASIC_COSTS.copy()
    for (first, then), cost in COST_CHAINS.items():
        COST_TABLE[first][then] = cost

    all_motions = set(BASIC_COSTS.keys())
    assert len(allowed_groups) > 0
    allowed_motions = {m for group in allowed_groups for m in MOVEMENT_OPTIONS[group]}
    disallowed_motions = all_motions - allowed_motions

    for motion in disallowed_motions:
        del COST_TABLE[motion]
    for first in COST_TABLE:
        for motion in disallowed_motions:
            del COST_TABLE[first][motion]


def getArguments():
    """Initialisation of the argument parser"""

    def listOfTuple(input: str):
        try:
            x, y = map(str, input.split(","))
            return int(x, 16), int(y, 16)
        except:
            raise ArgumentTypeError("values must be x,y")

    parser = Parser(
        description="Fix various things related to assets for the OoT Decomp"
    )

    parser.add_argument(
        "-g",
        "--allowed-groups",
        dest="allowedGroups",
        nargs="*",
        type=str,
        default="",
        help="usage: ``-g basic sword target_enabled",
        required=True,
    )

    parser.add_argument(
        "-s",
        "--start-angles",
        dest="startAngles",
        nargs="*",
        type=int,
        default="",
        help="usage: ``-s 0x8000 0x4000 0xC000 0x0000",
        required=True,
    )

    parser.add_argument(
        "-f",
        "--find-angles",
        dest="findAngles",
        nargs="*",
        type=str,
        default="",
        help="usage: ``-f 0x5E19 0x5E07 0x5C58 0xACA0",
        required=True,
    )

    parser.add_argument(
        "-a",
        "--avoid-angles",
        dest="avoidAngles",
        nargs=2,
        type=listOfTuple,
        default="",
        help="usage: ``-a 0xB168,0xB188 0xABAB,0x1234",
        required=True,
    )

    return parser.parse_args()
