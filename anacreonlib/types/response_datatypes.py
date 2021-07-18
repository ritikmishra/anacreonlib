from enum import Enum
import functools
from contextlib import suppress
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import uplink

from anacreonlib import utils
from anacreonlib.exceptions import HexArcException
from anacreonlib.types import DeserializableDataclass
from anacreonlib.types.type_hints import (
    Arc,
    BattleObjective,
    Circle,
    Location,
    SiegeStatus,
    TechLevel,
)
from pydantic import Field, ValidationError

from pydantic.class_validators import root_validator


# response datatype parent/abstract classes


class AuthenticationResponse(DeserializableDataclass):
    auth_token: str
    rights: List[str]
    scoped_credentials: List[str]
    username: str


class AnacreonObject(DeserializableDataclass):
    object_class: str

    class Config:
        fields = {"object_class": "class"}


class AnacreonObjectWithId(AnacreonObject):
    """Not all anacreon objects have an ID, most notably, UpdateObject"""

    id: int


# subclasses


class News(DeserializableDataclass):
    subject: int
    text: str


class SovereignActions(DeserializableDataclass):
    attacks_initiated: int
    offensives_initiated: int
    worlds_conquered: int


class SovereignRelationship(DeserializableDataclass):
    first_contact: int
    our_actions: SovereignActions
    their_actions: SovereignActions


class ExplorationGrid(DeserializableDataclass):
    radius: float
    explored_outline: List[List[float]]


class SovereignStats(DeserializableDataclass):
    fleets: int
    population: int
    resources: Optional[List[int]]
    tech_level: TechLevel
    worlds: int


class MesophonTrait(DeserializableDataclass):
    """Trait applied to the Mesophon sovereign (NPE trading empire that players can buy ships from)"""

    buy_prices: List[Union[int, float]]
    sell_prices: List[Union[int, float]]
    trait_id: int


class BattlePlanDetails(DeserializableDataclass):
    enemy_sovereign_ids: Optional[List[int]] = Field(None, alias="enemySovereignIDs")
    objective: BattleObjective
    sovereign_id: int
    status: str

    @root_validator
    def validate_enemy_sovereign_ids(cls, values):
        if (
            values.get("enemy_sovereign_ids") is None
            and values.get("objective") != BattleObjective.REINFORCE_SIEGE
        ):
            raise ValueError(
                "'enemy_sovereign_ids' can only be None when 'objective' is BattleObjective.REINFORCE_SIEGE"
            )
        return values


class RegionShape(DeserializableDataclass):
    holes: Optional[List[List[float]]]
    outline: List[float]


class Trait(DeserializableDataclass):
    allocation: float
    build_data: List[Union[float, None, List[Any]]]
    is_primary: Optional[bool]
    production_data: Optional[List[Union[float, None]]]
    is_fixed: Optional[bool]
    target_allocation: float
    trait_id: int
    build_complete: Optional[int]
    work_units: float


class Rebellion(DeserializableDataclass):
    popular_support: float
    rebel_forces: float
    rebellion_start: int
    trait_id: int


class Siege(AnacreonObjectWithId):
    object_class: Literal["siege"]
    anchor_obj_id: int
    attack_forces: float
    defense_forces: float
    name: str
    news: Optional[List[News]]
    pos: Location
    resources: Optional[List[float]]
    sovereign_id: int
    status: Optional[SiegeStatus]
    timeLeft: Optional[int]


class HistoryElement(DeserializableDataclass):
    id: int
    obj_id: int
    subject: int
    text: str


class History(AnacreonObject):
    object_class: Literal["history"]
    history: List[HistoryElement]


class TradeRoute(DeserializableDataclass):
    """
    :ivar import_tech: tuple of the desired tech level to acheive, and how many levels uplifted the planet actually is
    :ivar reciprocal: if true, the data for this trade route is attached to the partner object.
    """

    imports: Optional[List[Union[float, None]]]
    exports: Optional[List[Union[float, None]]]

    # Third element is usually not present. it indicates why the world cannot be uplifted to the desired tech level.
    import_tech: Union[Tuple[int, int], Tuple[int, int, Any], None]
    export_tech: Union[Tuple[int, int], Tuple[int, int, Any], None]
    partner_obj_id: int
    reciprocal: Optional[bool] = Field(None, alias="return")


# anacreon objects


class RevIndex(str, Enum):
    HAPPY = "happy"
    CONTENT = "content"
    DISSATISFIED = "dissatisfied"
    AGGRIEVED = "aggrieved"
    RIOTING = "rioting"
    REBELLING = "rebelling"
    CIVIL_WAR = "civil war"


class NebulaType(int, Enum):
    # The meaning of the 'region' field and its allowable values are completely a guess
    CLEAR_SPACE = 1
    LIGHT_NEBULA = 2
    DARK_NEBULA = 3
    RIFT_ZONE = 4


class World(AnacreonObjectWithId):
    object_class: Literal["world"]
    culture: int
    designation: int
    efficiency: float = Field(..., ge=0, le=100)
    name: str
    near_obj_ids: Optional[List[int]] = Field(None, alias="nearObjIDs")
    orbit: List[float]
    population: int
    pos: Location
    resources: Optional[List[int]]
    sovereign_id: int
    tech_level: TechLevel
    traits: List[Union[int, Trait, Rebellion]]
    world_class: int
    trade_routes: Optional[List[TradeRoute]]

    rev_index: Optional[RevIndex]

    region: NebulaType = NebulaType.CLEAR_SPACE

    @functools.cached_property
    def trade_route_partners(self) -> Optional[Dict[int, TradeRoute]]:
        """Returns a set of all of the trade route partners of this world"""
        if self.trade_routes is not None:
            return {
                trade_route.partner_obj_id: trade_route
                for trade_route in self.trade_routes
            }
        return None

    @functools.cached_property
    def squashed_trait_dict(self) -> Dict[int, Union[int, Trait]]:
        """Return a dict mapping from trait ID to either trait ID or trait object"""
        trait_dict = {}
        for trait in self.traits:
            if isinstance(trait, int):
                trait_dict[trait] = trait
            elif isinstance(trait, Trait):
                trait_dict[trait.trait_id] = trait

        return trait_dict

    @functools.cached_property
    def resource_dict(self) -> Dict[int, float]:
        """A dict mapping from resource ID to resource qty on the world"""
        return dict(utils.flat_list_to_n_tuples(2, self.resources))


class OwnedWorld(World):
    base_consumption: List[Union[int, None]]
    news: Optional[List[News]]

    trade_route_max: int

    rev_index: RevIndex


class Sovereign(AnacreonObjectWithId):
    """Any sovereign that has ever played in the current game"""

    object_class: Literal["sovereign"]
    imperial_might: int
    name: str
    relationship: SovereignRelationship

    # for some reason, dead sovereigns can have a doctrine
    # , and alive sovereigns might not have a doctrine id
    doctrine: Optional[int]

    traits: Optional[List[MesophonTrait]]


class ReigningSovereign(Sovereign):
    """Some Sovereigns are abdicated. This class is only for sovereigns currently playing the game."""

    capital_id: int

    stats: SovereignStats

    # Shown if you find their capital
    founded_on: Optional[int]
    territory: Optional[List[Union[Circle, Arc]]]


class OwnSovereign(ReigningSovereign):
    """Represents the sovereign belonging to the user who is currently logged in"""

    admin_range: List[Union[Circle, Arc]]
    exploration_grid: ExplorationGrid
    funds: List[Any]  # todo: determine type
    secession_chance: float
    stats: SovereignStats

    relationship: None = None


class BattlePlanObject(AnacreonObjectWithId):
    object_class: Literal["battlePlan"]
    battle_plan: BattlePlanDetails


class Fleet(AnacreonObjectWithId):
    object_class: Literal["fleet"]

    ftl_type: str
    name: str
    sovereign_id: int
    resources: List[int]
    news: Optional[List[News]]

    anchor_obj_id: Optional[int]
    battle_plan: Optional[BattlePlanDetails]
    position: Location = Field(..., alias="pos")
    destination: Optional[Location] = Field(None, alias="dest")
    dest_id: Optional[int]
    eta: Optional[int]

    region: NebulaType = NebulaType.CLEAR_SPACE


class DestroyedSpaceObject(AnacreonObjectWithId):
    object_class: Literal["destroyedSpaceObject"]


class UpdateObject(AnacreonObject):
    object_class: Literal["update"]
    next_update_time: int
    sequence: int
    update: float
    year0: int


class RegionObject(AnacreonObjectWithId):
    """Typically used to encode the location of nebulas, rift zones, and clear space"""

    object_class: Literal["region"]
    shape: List[RegionShape]
    type: int


class Relationship(AnacreonObjectWithId):
    """Partial update for sovereigns"""

    object_class: Literal["relationship"]
    corresponding_sovereign_id: int = Field(..., alias="id")
    relationship: SovereignRelationship


# utility functions


def _init_obj_subclasses():
    subclasses = AnacreonObject.__subclasses__()
    for subcls in subclasses:
        subclasses.extend(subcls.__subclasses__())
    return subclasses[::-1]


_anacreon_obj_subclasses = _init_obj_subclasses()


@uplink.response_handler
def handle_hexarc_error_response(response):
    res_json = response.json()
    if (
        type(res_json) == list
        and len(res_json) == 4
        and all(isinstance(val, str) for val in res_json)
    ):
        raise HexArcException(res_json)
    return response


def _convert_json_to_anacreon_obj(cls, json):
    classes_to_try = list()
    if cls is AnacreonObject:
        classes_to_try.extend(_anacreon_obj_subclasses)
    else:
        classes_to_try.append(cls)

    with suppress(ValueError):
        classes_to_try.remove(AnacreonObject)
    with suppress(ValueError):
        classes_to_try.remove(AnacreonObjectWithId)

    for subcls in classes_to_try:
        try:
            return subcls.parse_obj(json)
        except ValidationError as e:
            pass

    return json


convert_json_to_anacreon_obj = uplink.loads.from_json(AnacreonObject)(
    _convert_json_to_anacreon_obj
)
