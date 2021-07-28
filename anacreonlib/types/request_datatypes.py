import json
from enum import Enum
from typing import Any, Dict, List, Type, TypeVar, Union, Optional, cast

from pydantic import BaseModel, Field
from uplink import dumps

from anacreonlib.types._deser_utils import _snake_case_to_lower_camel
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
    sovereign_id: int
    sequence: Optional[int]


class TacticalOrderType(str, Enum):
    ORBIT = "orbit"
    LAND = "land"
    TARGET = "target"


class BattlePlan(SerializableDataclass):
    battlefield_id: int = Field(..., alias="battleFieldID")
    objective: BattleObjective
    enemy_sovereign_ids: List[int] = Field(alias="enemySovereignIDs")


# region ACTION TYPES
class DeployFleet(SerializableDataclass):
    source_obj_id: int
    resources: List[int]


class TransferFleet(SerializableDataclass):
    fleet_obj_id: int
    dest_obj_id: int
    resources: List[int]
    # source_obj_id: None = Field(None)


class DisbandFleet(SerializableDataclass):
    fleet_obj_id: int
    dest_obj_id: int


class RenameObject(SerializableDataclass):
    obj_id: int
    name: str


class SetFleetDestination(SerializableDataclass):
    obj_id: int
    dest: int


class Attack(SerializableDataclass):
    attacker_obj_id: int
    battle_plan: BattlePlan


class AbortAttack(SerializableDataclass):
    battlefield_id: int = Field(..., alias="battleFieldID")


class LaunchJumpMissile(SerializableDataclass):
    source_obj_id: int = Field(..., alias="objID")
    target_obj_id: int


class DesignateWorld(SerializableDataclass):
    source_obj_id: int
    new_designation: int


class AlterImprovement(SerializableDataclass):
    """Used to both build and destroy improvements"""

    source_obj_id: int
    improvement_id: int


class SetIndustryAlloc(SerializableDataclass):
    world_id: int = Field(..., alias="objID")
    industry_id: int
    alloc_value: Union[int, float] = Field(..., ge=0, le=100)


class SetProductAlloc(SerializableDataclass):
    world_id: int = Field(..., alias="objID")
    industry_id: int
    alloc: List[Union[int, float]]


class TradeRouteTypes(str, Enum):
    TECH = "tech"
    CONSUMPTION = "consumption"
    DEFAULT = "addDefaultRoute"
    ADD_EXPORT_ROUTE = "addExportRoute"
    SET_EXPORT_QUOTA = "setExportQuota"


class SetTradeRoute(SerializableDataclass):
    importer_id: int = Field(..., alias="objID")
    exporter_id: int = Field(..., alias="sourceObjID")
    alloc_type: Union[TradeRouteTypes, str]
    alloc_value: Optional[Union[str, float]]
    res_type_id: Optional[int] = Field(None, alias="resType")


class StopTradeRoute(SerializableDataclass):
    planet_id_a: int = Field(..., alias="objID")
    planet_id_b: int = Field(..., alias="sourceObjID")


class BuyItem(SerializableDataclass):
    source_obj_id: int
    item_id: int
    item_count: int


class TacticalOrder(SerializableDataclass):
    battlefield_id: int = Field(..., alias="objID")
    order: Union[TacticalOrderType, str]
    squadron_id: int = Field(..., alias="tacticalID")
    orbit: Optional[float] = None
    tactical_id: Optional[int] = None


class SetHistoryRead(SerializableDataclass):
    history_id: int


# endregion

# region API TYPES
class SellFleet(SerializableDataclass):
    fleet_id: int = Field(..., alias="objID")
    buyer_obj_id: int
    resources: List[int]


class SendMessage(SerializableDataclass):
    recipient_id: int
    message_text: str


class GetTactical(SerializableDataclass):
    battlefield_id: int = Field(..., alias="objID")


class DeployFleetRequest(DeployFleet, AnacreonApiRequest):
    pass


class TransferFleetRequest(TransferFleet, AnacreonApiRequest):
    pass


class DisbandFleetRequest(DisbandFleet, AnacreonApiRequest):
    pass


class RenameObjectRequest(RenameObject, AnacreonApiRequest):
    pass


class SetFleetDestinationRequest(SetFleetDestination, AnacreonApiRequest):
    pass


class AttackRequest(Attack, AnacreonApiRequest):
    pass


class AbortAttackRequest(AbortAttack, AnacreonApiRequest):
    pass


class LaunchJumpMissileRequest(LaunchJumpMissile, AnacreonApiRequest):
    pass


class DesignateWorldRequest(DesignateWorld, AnacreonApiRequest):
    pass


class AlterImprovementRequest(AlterImprovement, AnacreonApiRequest):
    pass


class SetIndustryAllocRequest(SetIndustryAlloc, AnacreonApiRequest):
    pass


class SetProductAllocRequest(SetProductAlloc, AnacreonApiRequest):
    pass


class SetTradeRouteRequest(SetTradeRoute, AnacreonApiRequest):
    pass


class StopTradeRouteRequest(StopTradeRoute, AnacreonApiRequest):
    pass


class BuyItemRequest(BuyItem, AnacreonApiRequest):
    pass


class SellFleetRequest(SellFleet, AnacreonApiRequest):
    pass


class GetTacticalRequest(GetTactical, AnacreonApiRequest):
    pass


class TacticalOrderRequest(TacticalOrder, AnacreonApiRequest):
    pass


class SetHistoryReadRequest(SetHistoryRead, AnacreonApiRequest):
    pass


class SendMessageRequest(SendMessage, AnacreonApiRequest):
    pass


# endregion


@dumps.to_json(AnacreonApiRequest)
def pydantic_request_converter(
    cls: type, inst: SerializableDataclass
) -> Dict[Any, Any]:
    """
    Converts request models to dict, with field aliases as keys

    The default pydantic converter in uplink doesn't use aliases, which we use extensively.
    """
    return cast(Dict[Any, Any], json.loads(inst.json(by_alias=True)))
