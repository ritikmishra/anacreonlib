from enum import Enum
from typing import Dict, List, Any, Optional, Union, Type

import uplink
from anacreonlib.exceptions import HexArcException

from anacreonlib.types._deser_utils import DeserializableDataclass
from anacreonlib.types.response_datatypes import Sovereign, ReigningSovereign
from anacreonlib.types.type_hints import Location


class Category(str, Enum):
    BUREAU_OF_TRADE = "bureauOfTrade"
    COMMODITY = "commodity"
    CULTURE = "culture"
    DESIGNATION = "designation"
    DOCTRINE = "doctrine"
    FEATURE = "feature"
    FIXED_UNIT = "fixedUnit"
    GROUND_UNIT = "groundUnit"
    IMPROVEMENT = "improvement"
    INDUSTRY = "industry"
    LAM_UNIT = "LAMUnit"
    MANEUVERING_UNIT = "maneuveringUnit"
    ORBITAL_UNIT = "orbitalUnit"
    REBELLION = "rebellion"
    WORLD_CLASS = "worldClass"


class Role(str, Enum):
    TECH_ADVANCE = "techAdvance"
    SECTOR_CAPITAL = "sectorCapital"
    ORBITAL_DEFENSE_INDUSTRY = "orbitalDefenseIndustry"
    IMPERIAL_CAPITAL = "imperialCapital"
    SHIPYARD_INDUSTRY = "shipyardIndustry"
    SPACEPORT = "spaceport"
    LIFE_SUPPORT = "lifeSupport"
    CITADEL_INDUSTRY = "citadelIndustry"
    ACADEMY = "academy"
    UNIVERSITY = "university"
    ENERGY_INDUSTRY = "energyIndustry"
    CITADEL = "citadel"
    ACADEMY_INDUSTRY = "academyIndustry"
    CONSUMER_GOODS_INDUSTRY = "consumerGoodsIndustry"
    FOUNDATION = "foundation"
    ADMINISTRATION = "administration"
    GROUND_DEFENSE_INDUSTRY = "groundDefenseIndustry"
    RAW_MATERIAL_INDUSTRY = "rawMaterialIndustry"
    SHIPYARD = "shipyard"
    TRADING_HUB = "tradingHub"
    COMPONENT_INDUSTRY = "componentIndustry"


class ScenarioInfoClass(str, Enum):
    CURRENCY_TYPE = "currencyType"
    IMAGE = "image"
    REGION_TYPE = "regionType"
    RESOURCE_TYPE = "resourceType"
    SCENARIO = "scenario"
    SOVEREIGN_TYPE = "sovereignType"
    TRAIT = "trait"


class UserInfo(DeserializableDataclass):
    capital_obj_id: int
    game_id: str
    map_bookmarks: List[Location]
    sovereign_id: int
    ui_options: Any
    username: str


class ScenarioInfoElement(DeserializableDataclass):
    is_cargo: Optional[bool] = None
    player_alloc: Optional[bool] = None
    player_product_alloc: Optional[bool] = None
    image_label: Optional[int] = None
    hidden: Optional[bool] = None
    designation_only: Optional[bool] = None
    npe_only: Optional[bool] = None
    is_jump_beacon: Optional[bool] = None
    can_land: Optional[bool] = None
    category: Optional[Category] = None
    scenario_info_class: Optional[ScenarioInfoClass] = None
    id: Optional[int] = None
    image_large: Optional[List[int]] = None
    image_small: Optional[List[int]] = None
    mass: Optional[float] = None
    name_desc: Optional[str] = None
    unid: Optional[str] = None
    attack_value: Optional[int] = None
    short_name: Optional[str] = None
    stats: Optional[List[Union[int, str]]] = None
    build_time: Optional[int] = None
    description: Optional[str] = None
    image_medium: Optional[List[int]] = None
    min_tech_level: Optional[int] = None
    role: Optional[Role] = None
    build_upgrade: Optional[List[int]] = None
    inherit_from: Optional[List[int]] = None
    exports: Optional[List[int]] = None
    max_tech_level: Optional[int] = None
    primary_industry: Optional[int] = None
    requirements: Optional[List[int]] = None
    build_exclusions: Optional[List[int]] = None
    tech_level_advance: Optional[int] = None
    background_color: Optional[List[int]] = None
    background_image: Optional[List[int]] = None
    background_image_low_detail: Optional[List[int]] = None
    background_image_tactical: Optional[List[int]] = None
    exclusions: Optional[List[int]] = None
    ftl: Optional[int] = None
    capital_industry: Optional[int] = None
    capital_type: Optional[int] = None
    build_requirements: Optional[List[int]] = None
    cargo_space: Optional[int] = None
    map_feature_size: Optional[int] = None
    map_size: Optional[List[int]] = None
    name: Optional[str] = None


class ScenarioInfo(DeserializableDataclass):
    scenario_info: List[ScenarioInfoElement]
    sovereigns: List[Union[ReigningSovereign, Sovereign]]
    user_info: UserInfo

    def find_by_unid(self, unid: str) -> ScenarioInfoElement:
        try:
            return next(item for item in self.scenario_info if item.unid == unid)
        except StopIteration:
            raise LookupError(f"Could not find ScenarioInfoElement with unid {unid}")


@uplink.loads.from_json(ScenarioInfo)
def convert_json_to_scenario_info(
    cls: Type[ScenarioInfo], json: Union[Dict[Any, Any], List[Any]]
) -> ScenarioInfo:
    if (
        isinstance(json, list)
        and len(json) == 4
        and all(isinstance(val, str) for val in json)
    ):
        raise HexArcException(json)

    return ScenarioInfo.parse_obj(json)
