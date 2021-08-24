from enum import Enum
import functools
from contextlib import suppress
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union

import uplink

from anacreonlib.exceptions import HexArcException
from anacreonlib.types._deser_utils import DeserializableDataclass
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

__all__ = (
    "AuthenticationResponse",
    "AnacreonObject",
    "AnacreonObjectWithId",
    "News",
    "SovereignActions",
    "SovereignRelationship",
    "ExplorationGrid",
    "SovereignStats",
    "MesophonTrait",
    "BattlePlanDetails",
    "RegionShape",
    "Trait",
    "Rebellion",
    "Siege",
    "HistoryElement",
    "History",
    "TradeRoute",
    "RevIndex",
    "NebulaType",
    "World",
    "OwnedWorld",
    "Sovereign",
    "ReigningSovereign",
    "OwnSovereign",
    "BattlePlanObject",
    "Fleet",
    "DestroyedSpaceObject",
    "UpdateObject",
    "RegionObject",
    "Relationship",
    "Selection",
)

# response datatype parent/abstract classes


class AuthenticationResponse(DeserializableDataclass):
    auth_token: str
    rights: List[str]
    scoped_credentials: int
    username: str


class AnacreonObject(DeserializableDataclass):
    object_class: str

    class Config:
        fields = {"object_class": "class"}


class AnacreonObjectWithId(AnacreonObject):
    """Not all anacreon objects have an ID, most notably, UpdateObject"""

    id: int


# region: subclasses


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

    #: A list which alternates between resource ID and the number of aes this
    #: empire is willing to pay per unit (they are the buyer)
    buy_prices: List[Union[int, float]]

    #: A list which alternates between resource ID and the number
    #: of aes this empire is willing to accept per unit (they are the seller)
    sell_prices: List[Union[int, float]]
    trait_id: int


class BattlePlanDetails(DeserializableDataclass):
    enemy_sovereign_ids: Optional[List[int]] = Field(None, alias="enemySovereignIDs")
    objective: BattleObjective
    sovereign_id: int
    status: str

    @root_validator
    def validate_enemy_sovereign_ids(cls, values: Dict[str, Any]) -> Dict[str, Any]:
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
    #: ``True``` if this structure is the primary industry on the world
    #: (i.e it belongs to the designation)
    is_primary: Optional[bool]
    production_data: Optional[List[Union[float, None]]]
    is_fixed: Optional[bool]
    target_allocation: float
    trait_id: int
    build_complete: Optional[int]
    work_units: float


class Rebellion(DeserializableDataclass):
    #: if popular support is greater than ``0```, it indicates rebel support
    #: if it is less than ``0```, it indicates imperial support
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
    #: ID of this history element, which can be passed to the setHistoryRead endpoint to clear this message
    id: int

    #: ID of the object this message applies to
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

    #: Third tuple element is usually not present. If present, it indicates why
    #: the world cannot be uplifted to the desired tech level.
    import_tech: Union[Tuple[int, int], Tuple[int, int, Any], None]
    export_tech: Union[Tuple[int, int], Tuple[int, int, Any], None]
    partner_obj_id: int
    reciprocal: Optional[bool] = Field(None, alias="return")


# endregion
# region: anacreon objects


class RevIndex(str, Enum):
    """Enum of social orders a world can have"""

    HAPPY = "happy"
    CONTENT = "content"
    DISSATISFIED = "dissatisfied"
    AGGRIEVED = "aggrieved"
    RIOTING = "rioting"
    REBELLING = "rebelling"
    CIVIL_WAR = "civil war"


class NebulaType(int, Enum):
    """Enum of types of space regions a world can be in

    (technically, a world cannot be in a `RIFT_ZONE`)
    (these values are a guess)
    """

    CLEAR_SPACE = 1
    LIGHT_NEBULA = 2
    DARK_NEBULA = 3
    RIFT_ZONE = 4


class World(AnacreonObjectWithId):
    object_class: Literal["world"]

    #: This is a trait ID that represents something intrinsic about the world's
    #: population
    culture: int

    #: This trait ID corresponds to which designation the world has
    designation: int
    efficiency: float = Field(..., ge=0, le=100)
    name: str

    #: This is a list of IDs of fleets that are stationed at this world
    near_obj_ids: Optional[List[int]] = Field(None, alias="nearObjIDs")
    orbit: List[float]
    population: int
    pos: Location

    #: This is a list alternating between resource ID and quantity stockpiled
    #: on the world
    resources: Optional[List[int]]
    sovereign_id: int
    tech_level: TechLevel
    traits: List[Union[int, Trait, Rebellion]]
    world_class: int
    trade_routes: Optional[List[TradeRoute]]

    rev_index: Optional[RevIndex]

    battle_plan: Optional[BattlePlanDetails]

    #: If the world is going to change tech levels soon, the value of this
    #: field is the target tech level
    target_tech_level: Optional[TechLevel]

    #: If the population is going to change, the value of this field is
    #: what the planet is heading towards
    #:
    #: Unit is millions of people
    target_population: Optional[int]

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
        trait_dict: Dict[int, Union[int, Trait]] = {}
        for trait in self.traits:
            if isinstance(trait, int):
                trait_dict[trait] = trait
            elif isinstance(trait, Trait):
                trait_dict[trait.trait_id] = trait

        return trait_dict

    @functools.cached_property
    def resource_dict(self) -> Dict[int, float]:
        """A dict mapping from resource ID to resource qty on the world"""
        if self.resources is not None:
            return dict(zip(self.resources[::2], self.resources[1::2]))
        else:
            return dict()


class OwnedWorld(World):
    """This is a world we know belongs to the current user because you are
    guaranteed to see certain fields
    """

    base_consumption: List[Union[int, None]]
    news: Optional[List[News]]

    trade_route_max: Optional[int]

    rev_index: RevIndex


class Sovereign(AnacreonObjectWithId):
    """Any sovereign that has ever played in the current game"""

    object_class: Literal["sovereign"]

    #: A measure of the empire's strength relative to you
    imperial_might: int
    name: str
    relationship: Optional[SovereignRelationship]

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

    #: Alternating list between resource ID and resource quantity
    #: As long as is only one currency (aes), this list will only have 2
    #: elements max
    funds: List[Union[int, float]]  # todo: determine type
    secession_chance: float
    stats: SovereignStats


class BattlePlanObject(AnacreonObjectWithId):
    object_class: Literal["battlePlan"]
    battle_plan: BattlePlanDetails


class Fleet(AnacreonObjectWithId):
    object_class: Literal["fleet"]

    #: Whether this is a jumpship fleet, starship/ramship fleet, or explorer
    #: fleet
    ftl_type: str
    name: str
    sovereign_id: int
    resources: List[int]

    #: For fleets, you might get news if they were attacked by jumpmissiles
    news: Optional[List[News]]

    #: ``None`` if this fleet is not currently stationed at a world. Otherwise,
    #: this is the ID of the world where this fleet is stationed.
    anchor_obj_id: Optional[int]
    battle_plan: Optional[BattlePlanDetails]
    pos: Location
    destination: Optional[Location] = Field(None, alias="dest")
    dest_id: Optional[int]

    #: If not ``None``, corresponds to the :py:attr:`UpdateObject.update`
    #: on which this fleet will arrive at its destination.
    eta: Optional[int]

    region: NebulaType = NebulaType.CLEAR_SPACE


class DestroyedSpaceObject(AnacreonObjectWithId):
    object_class: Literal["destroyedSpaceObject"]


class UpdateObject(AnacreonObject):
    object_class: Literal["update"]

    #: Number of milliseconds until the next watch update happens on the server
    next_update_time: int

    #: This is a unique ID associated with each state update. Using this number,
    #: the Anacreon server can know exactly what data it needs to send us in
    #: order to catch us up to speed with what changed since we last talked.
    sequence: int

    #: Number of watches that have occured since the game started
    update: float

    #: The in-game calendar year in which the game started (e.g ``4021``)
    year0: int


class RegionObject(AnacreonObjectWithId):
    """Typically used to encode the location of nebulas, rift zones, and clear space"""

    object_class: Literal["region"]
    shape: List[RegionShape]

    #: Corresponds to the :py:class:`ScenarioInfoElement` for this region type
    type: int


class Relationship(AnacreonObjectWithId):
    """Partial update for sovereigns"""

    object_class: Literal["relationship"]
    relationship: SovereignRelationship


class Selection(AnacreonObjectWithId):
    """
    The API returns this object if it wants the UI to
    select something as a result of the API request

    For example, when you deploy a fleet, the API returns
    one of these objects in order to signal that the new
    fleet should be selected.
    """

    object_class: Literal["selection"]


# endregion
# region: utility functions


def _init_obj_subclasses() -> List[Type[AnacreonObject]]:
    subclasses = AnacreonObject.__subclasses__()
    for subcls in subclasses:
        subclasses.extend(subcls.__subclasses__())
    return subclasses[::-1]


_anacreon_obj_subclasses = _init_obj_subclasses()


@uplink.response_handler
def handle_hexarc_error_response(response: Any) -> Any:
    res_json = response.json()
    if (
        type(res_json) == list
        and len(res_json) == 4
        and all(isinstance(val, str) for val in res_json)
    ):
        raise HexArcException(res_json)
    return response


def _convert_json_to_anacreon_obj(
    cls: Type[DeserializableDataclass], json: Dict[Any, Any]
) -> Any:
    classes_to_try: List[Type[DeserializableDataclass]] = list()
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

# endregion
