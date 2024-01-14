from decimal import Decimal
from collections import namedtuple


COST_FLEX = Decimal(3.0)
COST_TABLE = {}

MOVEMENT_OPTIONS = {
    "basic": [
        "ess right",
        "ess left",
    ],
    "target enabled": [
        "ess up",
        "turn right",
        "turn left",
        "turn 180",
    ],
    "no carry": [
        "sidehop sideroll left",
        "sidehop sideroll right",
        "ess down sideroll",
        "backflip sideroll",
    ],
    "sword": [
        "sword spin shield cancel",
    ],
    "biggoron": [
        "biggoron slash shield cancel",
        "biggoron quickspin shield cancel",
    ],
    "hammer": [
        "hammer shield cancel",
    ],
    "shield corners": [
        "shield top-right",
        "shield top-left",
        "shield bottom-left",
        "shield bottom-right",
    ],
    "c-up frame turn": [
        "c-up frame turn left",
        "c-up frame turn right",
    ],
}

BASIC_COSTS = {
    "ess up": Decimal(0.75),
    "ess left": Decimal(0.75),
    "ess right": Decimal(0.75),
    "turn left": Decimal(1.0),
    "turn right": Decimal(1.0),
    "turn 180": Decimal(1.0),
    "sidehop sideroll left": Decimal(1.0),
    "sidehop sideroll right": Decimal(1.0),
    "ess down sideroll": Decimal(1.0),
    "backflip sideroll": Decimal(1.0),
    "sword spin shield cancel": Decimal(1.25),
    "biggoron slash shield cancel": Decimal(1),
    "biggoron quickspin shield cancel": Decimal(1.25),
    "hammer shield cancel": Decimal(1.25),
    "shield top-right": Decimal(1.0),
    "shield top-left": Decimal(1.0),
    "shield bottom-left": Decimal(1.0),
    "shield bottom-right": Decimal(1.0),
    "c-up frame turn left": Decimal(1.25),
    "c-up frame turn right": Decimal(1.25),
}

COST_CHAINS = {
    ("ess left", "ess left"): Decimal(0.075),
    ("ess right", "ess right"): Decimal(0.075),
    ("c-up frame turn left", "c-up frame turn left"): Decimal(0.25),
    ("c-up frame turn right", "c-up frame turn right"): Decimal(0.25),
}

TARGET_BEFORE = {
    "ess up": True,
    "ess left": False,
    "ess right": False,
    "turn left": True,
    "turn right": True,
    "turn 180": True,
    "sidehop sideroll left": False,
    "sidehop sideroll right": False,
    "ess down sideroll": False,
    "backflip sideroll": False,
    "sword quickspin shield cancel": False,
    "biggoron slash shield cancel": False,
    "biggoron spin shield cancel": False,
    "hammer shield cancel": False,
    "shield top-right": True,
    "shield top-left": True,
    "shield bottom-left": True,
    "shield bottom-right": True,
    "c-up frame turn left": False,
    "c-up frame turn right": False,
}

allowed_groups: list[str] = []
start_angles: list[int] = []
find_angles: list[str] = []
avoid_angles: list[tuple[int, int]] = []

# Node
#   edges_in   - list of edges into this node
#   best       - float cost of the fastest path to this node; 'None' if the
#                node hasn't been encountered yet
# Edge
#   from_angle - integer angle (not a node object) this edge comes from
#   motion     - string, e.g. "ess up"
#   cost       - float cost of the fastest path to this edge, plus the cost of
#                the motion - could be different from the destination node's
#                'best' if this edge isn't on the fastest path to the node
Node = namedtuple("Node", ["edges_in", "best"])
Edge = namedtuple("Edge", ["from_angle", "motion", "cost"])

empty_node = lambda: Node(edges_in={}, best=None)
