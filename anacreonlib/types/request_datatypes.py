import json
from enum import Enum
from typing import List, Union, Optional

from pydantic import BaseModel, Field, SecretStr
from uplink import dumps

from anacreonlib.types import _snake_case_to_lower_camel
from anacreonlib.types.type_hints import BattleObjective


class SerializableDataclass(BaseModel):
    """Base class for a serializable Anacreon request object. Contains common Pydantic config settings."""

    class Config:
        allow_population_by_field_name = True
        alias_generator = _snake_case_to_lower_camel

class AuthenticationRequest(SerializableDataclass):
    username: str
    password: str
    actual: bool = True

class AnacreonApiRequest(SerializableDataclass):
    """Base class for request bodies to most of the endpoints for the Anacreon API"""

    auth_token: str
    game_id: str
    sovereign_id: Union[str, int]
    sequence: Optional[List[str]]


class DeployFleetRequest(AnacreonApiRequest):
    source_obj_id: int
    resources: List[int]


class TransferFleetRequest(AnacreonApiRequest):
    fleet_obj_id: int
    dest_obj_id: int
    resources: List[int]
    # source_obj_id: None = Field(None)


class DisbandFleetRequest(AnacreonApiRequest):
    fleet_obj_id: int
    dest_obj_id: int


class RenameObjectRequest(AnacreonApiRequest):
    obj_id: int
    name: str


class SetFleetDestinationRequest(AnacreonApiRequest):
    obj_id: int
    dest: int


class BattlePlan(SerializableDataclass):
    battlefield_id: int = Field(..., alias="battleFieldID")
    objective: BattleObjective
    enemy_sovereign_ids: List[int] = Field(alias="enemySovereignIDs")


class AttackRequest(AnacreonApiRequest):
    attacker_obj_id: int
    battle_plan: BattlePlan


class AbortAttackRequest(AnacreonApiRequest):
    battlefield_id: int = Field(..., alias="battleFieldID")


class LaunchJumpMissileRequest(AnacreonApiRequest):
    source_obj_id: int = Field(..., alias="objID")
    target_obj_id: int


class DesignateWorldRequest(AnacreonApiRequest):
    source_obj_id: int
    new_designation: int


class AlterImprovementRequest(AnacreonApiRequest):
    """Used to both build and destroy improvements"""

    source_obj_id: int
    improvement_id: int


class SetIndustryAllocRequest(AnacreonApiRequest):
    world_id: int = Field(..., alias="objID")
    industry_id: int
    alloc_value: Union[int, float] = Field(..., ge=0, le=100)


class SetProductAllocRequest(AnacreonApiRequest):
    world_id: int = Field(..., alias="objID")
    industry_id: int
    alloc: List[Union[int, float]]


class TradeRouteTypes(Enum):
    TECH = "tech"
    CONSUMPTION = "consumption"
    DEFAULT = "addDefaultRoute"


class SetTradeRouteRequest(AnacreonApiRequest):
    importer_id: int = Field(..., alias="objID")
    exporter_id: int = Field(..., alias="sourceObjID")
    alloc_type: Union[TradeRouteTypes, str]
    alloc_value: Optional[float]
    res_type_id: Optional[int] = Field(None, alias="resType")


class StopTradeRouteRequest(AnacreonApiRequest):
    planet_id_a: int = Field(..., alias="objID")
    planet_id_b: int = Field(..., alias="sourceObjID")


class BuyItemRequest(AnacreonApiRequest):
    source_obj_id: int
    item_id: int
    item_count: int


class SellFleetRequest(AnacreonApiRequest):
    fleet_id: int = Field(..., alias="objID")
    buyer_obj_id: int
    resources: List[int]


class GetTacticalRequest(AnacreonApiRequest):
    battlefield_id: int = Field(..., alias="objID")


class TacticalOrder(Enum):
    ORBIT = "orbit"
    LAND = "land"
    TARGET = "target"


class TacticalOrderRequest(AnacreonApiRequest):
    battlefield_id: int = Field(..., alias="objID")
    order: Union[TacticalOrder, str]
    squadron_id: int = Field(..., alias="tacticalID")


class SetHistoryReadRequest(AnacreonApiRequest):
    history_id: int


class SendMessageRequest(AnacreonApiRequest):
    recipient_id: int
    messageText: str


@dumps.to_json(AnacreonApiRequest)
def pydantic_request_converter(cls, inst: SerializableDataclass):
    """
    Converts request models to dict, with field aliases as keys

    The default pydantic converter in uplink doesn't use aliases, which we use extensively.
    """
    return json.loads(inst.json(by_alias=True))
