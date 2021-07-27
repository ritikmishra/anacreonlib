import collections
import dataclasses
from typing import (
    NamedTuple,
    Sequence,
    cast,
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    SupportsFloat,
    Tuple,
    Type,
    Union,
)
from anacreonlib.types.request_datatypes import *
from anacreonlib.types.type_hints import BattleObjective
from anacreonlib.types.scenario_info_datatypes import (
    Category,
    ScenarioInfo,
    ScenarioInfoElement,
)
from anacreonlib.types.response_datatypes import *
from anacreonlib import utils
from anacreonlib.anacreon_async_client import AnacreonAsyncClient
import logging
import asyncio
import functools
from dataclasses import dataclass

__all__ = ("ProductionInfo", "MilitaryForceInfo", "Anacreon")

# Map from stateful request body to client method name and API request body type
_stateful_request_bodies: Dict[
    Type[SerializableDataclass], Tuple[str, Type[AnacreonApiRequest]]
] = {
    AbortAttack: ("abort_attack", AbortAttackRequest),
    Attack: ("attack", AttackRequest),
    AlterImprovement: ("destroy_improvement", AlterImprovementRequest),
    BuyItem: ("buy_item", BuyItemRequest),
    DeployFleet: ("deploy_fleet", DeployFleetRequest),
    DesignateWorld: ("designate_world", DesignateWorldRequest),
    DisbandFleet: ("disband_fleet", DisbandFleetRequest),
    LaunchJumpMissile: ("launch_lams", LaunchJumpMissileRequest),
    RenameObject: ("rename_object", RenameObjectRequest),
    SellFleet: ("sell_fleet", SellFleetRequest),
    SetFleetDestination: ("set_fleet_destination", SetFleetDestinationRequest),
    SetIndustryAlloc: ("set_industry_alloc", SetIndustryAllocRequest),
    SetProductAlloc: ("set_product_alloc", SetProductAllocRequest),
    SetTradeRoute: ("set_trade_route", SetTradeRouteRequest),
    StopTradeRoute: ("stop_trade_route", StopTradeRouteRequest),
    TransferFleet: ("transfer_fleet", TransferFleetRequest),
}


IdValueMapping = Union[Dict[int, int], List[int]]
"""Either a dict mapping from resource id to resource qty, or a list with resource id and qty interleaved"""


def _ensure_resources_list(resources: IdValueMapping) -> List[int]:
    """Ensure that an IdValueMapping is a list that can be passed directly to the Anacreon API"""
    if isinstance(resources, dict):
        resources_list = list()
        for item_id, item_count in resources.items():
            resources_list.append(item_id)
            resources_list.append(item_count)
    else:
        resources_list = resources
    return resources_list


@dataclasses.dataclass(eq=True)
class ProductionInfo:
    available: float = 0
    consumed: float = 0
    exported: float = 0
    imported: float = 0
    produced: float = 0
    consumed_optimal: float = 0
    exported_optimal: float = 0
    imported_optimal: float = 0
    produced_optimal: float = 0

    def __add__(self: "ProductionInfo", other: "ProductionInfo") -> "ProductionInfo":
        return ProductionInfo(
            available=self.available + other.available,
            consumed=self.consumed + other.consumed,
            imported=self.imported + other.imported,
            exported=self.exported + other.exported,
            produced=self.produced + other.produced,
            consumed_optimal=self.consumed_optimal + other.consumed_optimal,
            exported_optimal=self.exported_optimal + other.exported_optimal,
            imported_optimal=self.imported_optimal + other.imported_optimal,
            produced_optimal=self.produced_optimal + other.produced_optimal,
        )

    def __sub__(self: "ProductionInfo", other: "ProductionInfo") -> "ProductionInfo":
        return ProductionInfo(
            available=self.available - other.available,
            consumed=self.consumed - other.consumed,
            imported=self.imported - other.imported,
            exported=self.exported - other.exported,
            produced=self.produced - other.produced,
            consumed_optimal=self.consumed_optimal - other.consumed_optimal,
            exported_optimal=self.exported_optimal - other.exported_optimal,
            imported_optimal=self.imported_optimal - other.imported_optimal,
            produced_optimal=self.produced_optimal - other.produced_optimal,
        )


@dataclasses.dataclass
class MilitaryForceInfo:
    space_forces: float
    ground_forces: float
    missile_forces: float
    maneuvering_unit_forces: float


class Anacreon:
    """A wrapper around AnacreonAsyncClient that keeps track of state and handles partial updates"""

    @classmethod
    async def log_in(cls, game_id: str, username: str, password: str) -> "Anacreon":
        auth_req = AuthenticationRequest(username=username, password=password)
        client = AnacreonAsyncClient()
        auth_token = (await client.authenticate_user(auth_req)).auth_token
        return await cls.from_auth_token(game_id, auth_token, client=client)

    @classmethod
    async def from_auth_token(
        cls,
        game_id: str,
        auth_token: str,
        *,
        client: Optional[AnacreonAsyncClient] = None,
    ) -> "Anacreon":
        client = client or AnacreonAsyncClient()
        game_info = await client.get_game_info(auth_token, game_id)

        auth_info: AnacreonApiRequest = AnacreonApiRequest(
            auth_token=auth_token,
            game_id=game_id,
            sovereign_id=game_info.user_info.sovereign_id,
        )

        return cls(auth_info, game_info, client=client)

    def __init__(
        self,
        auth_info: AnacreonApiRequest,
        game_info: ScenarioInfo,
        client: Optional[AnacreonAsyncClient] = None,
    ) -> None:
        self._auth_info: AnacreonApiRequest = auth_info
        self.client: AnacreonAsyncClient = client or AnacreonAsyncClient()
        self.logger = logging.getLogger(str(self.__class__.__name__))

        self._get_objects_event = asyncio.Event()
        self._state_updated_event = asyncio.Event()

        self.game_info = game_info
        self.scenario_info_objects = {
            item_id: item
            for item in game_info.scenario_info
            if (item_id := item.id) is not None
        }
        self._force_calculator = _MilitaryForceCalculator.from_game_info(game_info)

        self.space_objects: Dict[int, Union[World, Fleet]] = dict()
        self.sieges: Dict[int, Siege] = dict()
        self.sovereigns: Dict[int, Sovereign] = {
            sov.id: sov for sov in game_info.sovereigns
        }
        self.history: Dict[int, HistoryElement] = dict()
        self.update_obj: Optional[UpdateObject] = None

    async def get_objects(self) -> "Anacreon":
        """
        :return: A list of all objects that you have explored and data relevant to them, such as object ID's, planet
        designations, resources contained in fleets, and similar information relevant to gameplay
        """
        partial_state = await self.client.get_objects(self._auth_info)
        self._process_update(partial_state)

        # This is fine because the python event loop is single threaded
        # and there is no `await` in between the set/clear
        # so we know that nobody will call `wait_for_get_objects` in between
        # the .set() and the .clear() calls
        self._get_objects_event.set()
        self._get_objects_event.clear()

        return self

    async def wait_for_get_objects(self) -> None:
        await self._get_objects_event.wait()

    async def wait_for_any_update(self) -> None:
        await self._state_updated_event.wait()

    def call_get_objects_periodically(self) -> "asyncio.Task[None]":
        async def _update() -> None:
            while True:
                await self.get_objects()
                if self.update_obj:
                    await asyncio.sleep(self.update_obj.next_update_time // 1000)
                else:
                    await asyncio.sleep(60)

        return asyncio.create_task(_update())

    def _process_update(
        self, partial_state: List[AnacreonObject]
    ) -> Optional[Selection]:
        """
        Update game state based on partial state update

        :param partial_state: The partial state update obtained by calling an API endpoint
        :return: The entire game state
        """

        selection = None

        for obj in partial_state:
            if isinstance(obj, (World, Fleet)):
                self.space_objects[obj.id] = obj

            elif isinstance(obj, BattlePlanObject):
                self.space_objects[obj.id].battle_plan = obj.battle_plan

            elif isinstance(obj, DestroyedSpaceObject):
                del self.space_objects[obj.id]

            elif isinstance(obj, Sovereign):
                self.sovereigns[obj.id] = obj

            elif isinstance(obj, Relationship):
                self.sovereigns[obj.id].relationship = obj.relationship

            elif isinstance(obj, Siege):
                self.sieges[obj.id] = obj

            elif isinstance(obj, UpdateObject):
                self._auth_info.sequence = obj.sequence
                self.update_obj = obj

            elif isinstance(obj, History):
                self.history = {h.id: h for h in obj.history}

            elif isinstance(obj, RegionObject):
                pass

            elif isinstance(obj, Selection):
                selection = obj

            elif isinstance(obj, dict):
                None

        self._state_updated_event.set()
        self._state_updated_event.clear()
        return selection

    async def _do_action(self, request: SerializableDataclass) -> Optional[Selection]:
        client_method_name, api_type = _stateful_request_bodies[type(request)]
        api_request = api_type(**request.dict(), **self._auth_info.dict())
        client_method = getattr(self.client, client_method_name)
        updated_objects: List[AnacreonObject] = await client_method(api_request)
        return self._process_update(updated_objects)

    # region: methods that call the api and update self.space_objects/related state

    async def abort_attack(self, battlefield_id: int) -> None:
        await self._do_action(AbortAttack(battlefield_id=battlefield_id))

    async def attack(
        self,
        battlefield_id: int,
        objective: BattleObjective,
        enemy_sovereign_ids: List[int],
    ) -> None:
        await self._do_action(
            Attack(
                attacker_obj_id=battlefield_id,
                battle_plan=BattlePlan(
                    battlefield_id=battlefield_id,
                    objective=objective,
                    enemy_sovereign_ids=enemy_sovereign_ids,
                ),
            )
        )

    async def build_improvement(self, world_obj_id: int, improvement_id: int) -> None:
        partial_update = await self.client.build_improvement(
            AlterImprovementRequest(
                source_obj_id=world_obj_id,
                improvement_id=improvement_id,
                **self._auth_info.dict(),
            )
        )
        self._process_update(partial_update)

    async def buy_item(self, source_obj_id: int, item_id: int, item_count: int) -> None:
        await self._do_action(
            BuyItem(source_obj_id=source_obj_id, item_id=item_id, item_count=item_count)
        )

    async def deploy_fleet(
        self, source_obj_id: int, resources: IdValueMapping
    ) -> Optional[Fleet]:
        selection = await self._do_action(
            DeployFleet(
                source_obj_id=source_obj_id, resources=_ensure_resources_list(resources)
            )
        )
        if selection is not None:
            ret = self.space_objects[selection.id]
            if isinstance(ret, Fleet):
                return ret
        return None

    async def designate_world(self, world_obj_id: int, designation_id: int) -> None:
        await self._do_action(
            DesignateWorld(source_obj_id=world_obj_id, new_designation=designation_id)
        )

    async def destroy_improvement(self, world_obj_id: int, improvement_id: int) -> None:
        partial_update = await self.client.destroy_improvement(
            AlterImprovementRequest(
                source_obj_id=world_obj_id,
                improvement_id=improvement_id,
                **self._auth_info.dict(),
            )
        )
        self._process_update(partial_update)

    async def disband_fleet(self, fleet_obj_id: int, dest_obj_id: int) -> None:
        await self._do_action(
            DisbandFleet(fleet_obj_id=fleet_obj_id, dest_obj_id=dest_obj_id)
        )

    async def launch_lams(self, source_obj_id: int, target_obj_id: int) -> None:
        await self._do_action(
            LaunchJumpMissile(source_obj_id=source_obj_id, target_obj_id=target_obj_id)
        )

    async def rename_object(self, obj_id: int, new_name: str) -> None:
        await self._do_action(RenameObject(obj_id=obj_id, name=new_name))

    async def sell_fleet(
        self, fleet_id: int, buyer_obj_id: int, resources: IdValueMapping
    ) -> None:
        await self._do_action(
            SellFleet(
                fleet_id=fleet_id,
                buyer_obj_id=buyer_obj_id,
                resources=_ensure_resources_list(resources),
            )
        )

    async def set_fleet_destination(self, fleet_obj_id: int, dest_obj_id: int) -> None:
        await self._do_action(
            SetFleetDestination(obj_id=fleet_obj_id, dest=dest_obj_id)
        )

    async def set_industry_alloc(
        self, world_id: int, industry_id: int, pct_labor_allocated: SupportsFloat
    ) -> None:
        await self._do_action(
            SetIndustryAlloc(
                world_id=world_id,
                industry_id=industry_id,
                alloc_value=float(pct_labor_allocated),
            )
        )

    async def set_product_alloc(
        self,
        world_id: int,
        industry_id: int,
        pct_labor_allocated_by_resource: IdValueMapping,
    ) -> None:
        await self._do_action(
            SetProductAlloc(
                world_id=world_id,
                industry_id=industry_id,
                alloc=_ensure_resources_list(pct_labor_allocated_by_resource),
            )
        )

    async def set_trade_route(
        self,
        importer_id: int,
        exporter_id: int,
        alloc_type: str = TradeRouteTypes.DEFAULT,
        alloc_value: Optional[Union[str, float]] = None,
        res_type_id: Optional[int] = None,
    ) -> None:
        await self._do_action(
            SetTradeRoute(
                importer_id=importer_id,
                exporter_id=exporter_id,
                alloc_type=alloc_type,
                alloc_value=alloc_value,
                res_type_id=res_type_id,
            )
        )

    async def stop_trade_route(self, planet_id_a: int, planet_id_b: int) -> None:
        await self._do_action(
            StopTradeRoute(planet_id_a=planet_id_a, planet_id_b=planet_id_b)
        )

    async def transfer_fleet(
        self, fleet_obj_id: int, dest_obj_id: int, resources: IdValueMapping
    ) -> None:
        await self._do_action(
            TransferFleet(
                fleet_obj_id=fleet_obj_id,
                dest_obj_id=dest_obj_id,
                resources=_ensure_resources_list(resources),
            )
        )

    # endregion
    # region: methods that call the api but don't alter self.space_objects/related state

    async def get_tactical(self, battlefield_id: str) -> List[Dict[str, Any]]:
        """
        Get battlefield information of a planet, such as battle groups and squadron locations

        :return: Battlefield info
        """
        return await self.client.get_tactical(
            GetTacticalRequest(battlefield_id=battlefield_id, **self._auth_info.dict())
        )

    async def tactical_order(
        self,
        battlefield_id: int,
        order: Union[TacticalOrderType, str],
        squadron_id: int,
    ) -> bool:
        """
        Give a tactical order

        :return: If your order was carried out
        """
        return await self.client.tactical_order(
            TacticalOrderRequest(
                battlefield_id=battlefield_id,
                order=order,
                squadron_id=squadron_id,
                **self._auth_info.dict(),
            )
        )

    async def set_history_read(self, history_id: int) -> bool:
        """
        Delete one of those popups that show up over planets

        :return: If the popup was cleared successfully
        """
        successfully_cleared = await self.client.set_history_read(
            SetHistoryReadRequest(history_id=history_id, **self._auth_info.dict())
        )
        if successfully_cleared:
            del self.history[history_id]

        return successfully_cleared

    async def send_message(self, recipient_sov_id: int, message_text: str) -> None:
        """
        Send a message to another empire

        :return: None
        """
        await self.client.send_message(
            SendMessageRequest(
                recipient_id=recipient_sov_id,
                message_text=message_text,
                **self._auth_info.dict(),
            )
        )

    # endregion
    # region: util methods

    def generate_production_info(
        self, world: Union[World, int]
    ) -> Dict[int, ProductionInfo]:
        """
        Generate info that can be found in the production tab of a planet
        :param world: The planet ID or the planet object
        :param refresh: Whether or not to refresh the internal game objects cache
        :return: A list of all the things that the planet has produced, imported, exported, etc
        """

        # This is more or less exactly how the game client calculates production as well
        # I ported this from JavaScript
        if isinstance(world, int):
            maybe_world_obj = self.space_objects[world]
            if maybe_world_obj is None or not isinstance(maybe_world_obj, World):
                raise LookupError(f"Could not find world with id {world}")
            worldobj: World = maybe_world_obj
        else:
            worldobj = world
        assert isinstance(worldobj, World)

        result: DefaultDict[int, ProductionInfo] = collections.defaultdict(
            ProductionInfo
        )

        flat_list_to_4tuples = cast(
            Callable[
                [Sequence[Union[int, float, None]]],
                List[Tuple[int, float, float, Optional[float]]],
            ],
            functools.partial(utils.flat_list_to_n_tuples, 4),
        )
        flat_list_to_3tuples = cast(
            Callable[
                [Sequence[Union[int, float, None]]],
                List[Tuple[int, float, Optional[float]]],
            ],
            functools.partial(utils.flat_list_to_n_tuples, 3),
        )

        resource_id: int
        optimal: float
        actual: Optional[float]

        if isinstance(worldobj, OwnedWorld):
            # First we take into account the base consumption of the planet (i.e the food the population eats)
            for resource_id, optimal, actual in flat_list_to_3tuples(
                worldobj.base_consumption
            ):
                entry = result[resource_id]

                entry.consumed_optimal += optimal

                if actual is None:
                    entry.consumed += optimal
                else:
                    entry.consumed += actual

        for trait in worldobj.traits:
            # Next, we take into account what our structures are consuming (i.e tril spent on growing food)
            if isinstance(trait, Trait):
                if trait.production_data:
                    for resource_id, optimal, actual in flat_list_to_3tuples(
                        trait.production_data
                    ):
                        entry = result[resource_id]

                        if optimal > 0.0:
                            entry.produced_optimal += optimal
                            if actual is None:
                                entry.produced += optimal
                            else:
                                entry.produced += actual
                        else:
                            entry.consumed_optimal += -optimal
                            if actual is None:
                                entry.consumed += -optimal
                            else:
                                entry.consumed += -actual

        if worldobj.trade_routes:
            # Finally, we account for trade routes
            for trade_route in worldobj.trade_routes:
                exports: Optional[List[Optional[float]]] = None
                imports: Optional[List[Optional[float]]] = None
                if trade_route.reciprocal:
                    # The data for this trade route belongs to another planet
                    partner_obj = self.space_objects.get(
                        trade_route.partner_obj_id, None
                    )
                    # would be sorta dumb if our trade route partner didn't actually exist
                    assert isinstance(
                        partner_obj, World
                    ), f"(world {worldobj.id}) partner id {repr(trade_route.partner_obj_id)} was a {type(partner_obj)} instead of World!"

                    # would also be dumb if our trade route partner didn't have any trade routes
                    assert (
                        partner_trade_routes := partner_obj.trade_route_partners
                    ) is not None

                    partner_trade_route = partner_trade_routes[worldobj.id]
                    imports = partner_trade_route.exports
                    exports = partner_trade_route.imports
                else:
                    exports = trade_route.exports
                    imports = trade_route.imports

                if exports is not None:
                    for resource_id, _pct, optimal, actual in flat_list_to_4tuples(
                        exports
                    ):
                        entry = result[resource_id]

                        if actual is None:
                            entry.exported += optimal
                        else:
                            entry.exported += actual

                        entry.exported_optimal += optimal

                if imports is not None:
                    for resource_id, _pct, optimal, actual in flat_list_to_4tuples(
                        imports
                    ):
                        entry = result[resource_id]

                        if actual is None:
                            entry.imported += optimal
                        else:
                            entry.imported += actual

                        entry.imported_optimal += optimal

                if worldobj.resources:
                    for resource_id, resource_qty in cast(
                        List[Tuple[int, float]],
                        utils.flat_list_to_n_tuples(2, worldobj.resources),
                    ):
                        if resource_qty > 0:
                            result[resource_id].available = resource_qty

        return {int(k): v for k, v in result.items()}

    def calculate_forces(
        self, object_or_resources: Union[World, Fleet, IdValueMapping]
    ) -> MilitaryForceInfo:
        return self._force_calculator.calculate_forces(object_or_resources)

    def calculate_remaining_cargo_space(self, fleet: Union[Fleet, int]) -> float:
        if isinstance(fleet, int):
            maybe_fleet = self.space_objects[fleet]
            if isinstance(maybe_fleet, Fleet):
                fleet = maybe_fleet
            else:
                raise LookupError(f"Could not find fleet with id {fleet}")

        fleet_resources = cast(
            List[Tuple[int, float]], utils.flat_list_to_tuples(fleet.resources)
        )

        remaining_cargo_space: float = 0
        for res_id, qty in fleet_resources:
            res_info = self.scenario_info_objects[res_id]
            if res_info.cargo_space:
                remaining_cargo_space += res_info.cargo_space * qty
            elif res_info.is_cargo and res_info.mass:
                remaining_cargo_space -= res_info.mass * qty

        return remaining_cargo_space

    def get_valid_improvement_list(self, world: World) -> List[ScenarioInfoElement]:
        """Returns a list of improvements that can be built"""
        valid_improvement_ids: List[ScenarioInfoElement] = []
        trait_dict = world.squashed_trait_dict

        # func returns true if this world has trait
        this_world_has_trait: Callable[[int], bool] = functools.partial(
            utils.world_has_trait, self.game_info.scenario_info, world
        )

        for improvement in self.game_info.scenario_info:
            if (
                improvement.category == Category.IMPROVEMENT  # should be an improvement
                and improvement.id is not None
                and improvement.id
                not in trait_dict.keys()  #  that is not already built
                and improvement.build_time is not None  #       that could be built
                and not improvement.npe_only  #                 by players
                and not improvement.designation_only  #         without redesignating
                and (
                    improvement.min_tech_level is None  #
                    or world.tech_level >= improvement.min_tech_level
                )
            ):
                if improvement.build_upgrade:
                    # Check if we have the predecessor structure.
                    has_predecessor_structure = any(
                        this_world_has_trait(predecessor)
                        and not utils.trait_under_construction(trait_dict, predecessor)
                        for predecessor in improvement.build_upgrade
                    )
                    if not has_predecessor_structure:
                        continue
                if improvement.build_requirements:
                    # Check we have requirements. Requirements can be any trait.
                    requirement_missing = any(
                        not this_world_has_trait(requirement_id)
                        or utils.trait_under_construction(trait_dict, requirement_id)
                        for requirement_id in improvement.build_requirements
                    )
                    if requirement_missing:
                        continue

                if improvement.build_exclusions:
                    # Check if we are banned from doing so
                    if any(
                        this_world_has_trait(exclusion_id)
                        for exclusion_id in improvement.build_exclusions
                    ):
                        continue

                # Check if this trait would be a downgrade from an existing trait
                if any(
                    utils.does_trait_depend_on_trait(
                        self.game_info.scenario_info, existing_trait_id, improvement.id
                    )
                    for existing_trait_id in trait_dict.keys()
                ):
                    continue

                # if this is a tech advancement structure, check if we can build it
                if improvement.role == "techAdvance":
                    if (improvement.tech_level_advance or 0) <= world.tech_level:
                        continue

                # we have not continue'd so it is ok to  build
                valid_improvement_ids.append(improvement)

        return valid_improvement_ids

    # endregion


_missile_unit_unids = {
    "core.GDM",
    "core.hypersonicMissile",
    "core.armoredSatellite",
    "core.battlestationTitan",
    "core.jumpcruiserAdamant",
    "core.jumpcruiserUndine",
    "core.starcruiserBehemoth",
    "core.starcruiserMegathere",
    "core.starcruiserTyphon",
    "core.starcruiserVictory",
}


@dataclass
class _MilitaryForceCalculator:
    sf_calc: Dict[int, float]
    gf_calc: Dict[int, float]
    maneuvering_unit_calc: Dict[int, float]
    missile_calc: Dict[int, float]

    @classmethod
    def from_game_info(cls, game_info: ScenarioInfo) -> "_MilitaryForceCalculator":
        """
        Generate the dictionaries required to calculate space and ground force of an object

        :return: None
        """

        sf_calc: Dict[int, float] = dict()
        gf_calc: Dict[int, float] = dict()
        maneuvering_unit_calc: Dict[int, float] = dict()
        missile_calc: Dict[int, float] = dict()

        for item in game_info.scenario_info:
            if item.attack_value is not None:
                assert item.id is not None
                attack_value = float(item.attack_value)

                if (
                    item.category
                    in (
                        Category.FIXED_UNIT,
                        Category.ORBITAL_UNIT,
                        Category.MANEUVERING_UNIT,
                    )
                    and item.cargo_space is None
                ):
                    sf_calc[item.id] = attack_value
                    if item.category == Category.MANEUVERING_UNIT:
                        maneuvering_unit_calc[item.id] = attack_value
                    if item.unid in _missile_unit_unids:
                        missile_calc[item.id] = attack_value

                elif item.category == Category.GROUND_UNIT:
                    gf_calc[item.id] = attack_value

        return cls(sf_calc, gf_calc, maneuvering_unit_calc, missile_calc)

    def calculate_forces(
        self, object_or_resources: Union[World, Fleet, IdValueMapping]
    ) -> MilitaryForceInfo:
        if isinstance(object_or_resources, (World, Fleet)):
            if object_or_resources.resources is None:
                return MilitaryForceInfo(0, 0, 0, 0)

            resource_list = object_or_resources.resources
        else:
            resource_list = _ensure_resources_list(object_or_resources)

        space_forces = 0.0
        ground_forces = 0.0
        maneuveringunit_force = 0.0
        missile_force = 0.0

        for item_id, item_qty in cast(
            List[Tuple[int, float]], utils.flat_list_to_tuples(resource_list)
        ):
            space_forces += float(item_qty) * self.sf_calc.get(item_id, 0)
            ground_forces += float(item_qty) * self.gf_calc.get(item_id, 0)
            maneuveringunit_force += float(item_qty) * self.maneuvering_unit_calc.get(
                item_id, 0
            )
            missile_force += float(item_qty) * self.missile_calc.get(item_id, 0)

        return MilitaryForceInfo(
            space_forces / 100,
            ground_forces / 100,
            maneuveringunit_force / 100,
            missile_force / 100,
        )
