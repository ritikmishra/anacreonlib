from enum import Enum
from typing import Literal, Tuple

TechLevel = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

Location = Tuple[float, float]
"""
A location is a tuple of 2 numbers
    - x pos
    - y pos
"""

Circle = Tuple[float, float, float]
"""
A Circle is a tuple of 3 numbers: 
    - x pos of center
    - y pos of center
    - radius, in lightyears
"""


class BattleObjective(Enum):
    INVASION = "invasion"
    SPACE_SUPREMACY = "spaceSupremacy"
