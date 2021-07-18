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

Arc = Tuple[float, float, float, float, float]
"""
An Arc is a tuple of 5 numbers:
    - x pos of center
    - y pos of center
    - radius, in light years
    - starting angle in radians
    - ending angle in radians
"""


class BattleObjective(str, Enum):
    INVASION = "invasion"
    SPACE_SUPREMACY = "spaceSupremacy"
    REINFORCE_SIEGE = "reinforceSiege"


class SiegeStatus(str, Enum):
    ATTACK_FAILING = "attackFailing"
    ATTACK_WINNING = "attackWinning"
    DEFENSE_FALIING = "defenseFailing"
    DEFENSE_WINNING = "defenseWinning"
