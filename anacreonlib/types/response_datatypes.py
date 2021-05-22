import functools
from typing import List, Literal, Optional, Any, Union, Dict, Tuple
from contextlib import suppress
import uplink
from pydantic import Field, ValidationError

from anacreonlib.exceptions import HexArcException
from anacreonlib.types import DeserializableDataclass
from anacreonlib.types.type_hints import SiegeStatus, TechLevel, Circle, Location, BattleObjective


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
    resources: List[int]
    tech_level: TechLevel
    worlds: int


class BattlePlanDetails(DeserializableDataclass):
    enemy_sovereign_ids: List[int] = Field(..., alias="enemySovereignIDs")
    objective: BattleObjective
    sovereign_id: int
    status: str


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
    import_tech: Optional[Tuple[int, int]]
    export_tech: Optional[Tuple[int, int]]
    partner_obj_id: int
    reciprocal: Optional[bool] = Field(None, alias="return")


# anacreon objects


class World(AnacreonObjectWithId):
    object_class: Literal["world"]
    culture: int
    designation: int
    efficiency: float = Field(..., ge=0, le=100)
    name: str
    near_obj_ids: Optional[List[int]]
    orbit: List[float]
    population: int
    pos: Location
    resources: Optional[List[int]]
    sovereign_id: int
    tech_level: TechLevel
    traits: List[Union[int, Trait, Rebellion]]
    world_class: int
    trade_routes: Optional[List[TradeRoute]]

    @functools.cached_property
    def trade_route_partners(self) -> Optional[Dict[int, TradeRoute]]:
        """Returns a set of all of the trade route partners of this world"""
        if self.trade_routes is not None:
            return {trade_route.partner_obj_id: trade_route for trade_route in self.trade_routes}
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


class OwnedWorld(World):
    base_consumption: List[Union[int, None]]
    news: Optional[List[News]]
    rev_index: Literal[
        "happy",
        "content",
        "dissatisfied",
        "aggrieved",
        "rioting",
        "rebellion",
        "civil war",
    ]


class Sovereign(AnacreonObjectWithId):
    object_class: Literal["sovereign"]
    imperial_might: int
    name: str
    relationship: Optional[SovereignRelationship]


class ReigningSovereign(Sovereign):
    """Some Sovereigns are abdicated. This class is only for sovereigns currently playing the game."""

    capital_id: int
    doctrine: int

    # Shown if you find their capital
    founded_on: Optional[int]
    territory: Optional[List[Circle]]

    # Only shown for you, I think
    admin_range: Optional[List[Circle]]
    exploration_grid: Optional[ExplorationGrid]
    funds: Optional[List[Any]]  # todo: determine type
    secession_chance: Optional[float]
    stats: Optional[SovereignStats]


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
    if type(res_json) == list and len(res_json) == 4 and all(isinstance(val, str) for val in res_json):
        raise HexArcException(res_json)
    return response


@uplink.loads.from_json(AnacreonObject)
def convert_json_to_anacreon_obj(cls, json: Union[dict, list]):
    classes_to_try = list()
    if cls is AnacreonObject:
        classes_to_try.extend(_anacreon_obj_subclasses)
    else:
        classes_to_try.append(cls)

    with suppress(ValueError): classes_to_try.remove(AnacreonObject)
    with suppress(ValueError): classes_to_try.remove(AnacreonObjectWithId)

    for subcls in classes_to_try:
        try:
            return subcls.parse_obj(json)
        except ValidationError as e:
            pass

    return json
