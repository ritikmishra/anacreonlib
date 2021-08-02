"""The :py:class:`Anacreon` class is a wrapper around 
:py:class:`~anacreonlib.anacreon_async_client.AnacreonAsyncClient` that handles 
basic functionality (such as state management and merging partial updates).
"""
import collections
import dataclasses
from typing import (
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
    """This is a :py:func:`dataclasses.dataclass`"""

    #: Amount of resource that is stockpiled on the world
    available: float = 0

    #: Amount of resource that was consumed last watch
    consumed: float = 0

    #: Amount of resource that was exported last watch
    exported: float = 0

    #: Amount of resource that was imported last watch
    imported: float = 0

    #: Amount of resource that was produced last watch
    produced: float = 0

    #: Amount of resource that would have been consumed last watch if there were
    #: no resource shortages
    consumed_optimal: float = 0

    #: Amount of resource that would have been exported last watch if there were
    #: no resource shortages
    exported_optimal: float = 0

    #: Amount of resource that would have been imported last watch if there were
    #: no resource shortages
    imported_optimal: float = 0

    #: Amount of resource that would have been produced last watch if there were
    #: no resource shortages
    produced_optimal: float = 0

    def __add__(self: "ProductionInfo", other: "ProductionInfo") -> "ProductionInfo":
        """Add two :class:`ProductionInfo` instances together elementwise

        Returns:
            ProductionInfo: the elementwise sum
        """
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
        """Subtract two :class:`ProductionInfo` instances together elementwise

        Returns:
            ProductionInfo: the elementwise difference
        """
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
    """This is a :py:func:`dataclasses.dataclass`"""

    #: The amount of space forces on a world/in a fleet, as would be shown
    #: in the game UI
    space_forces: float

    #: The amount of ground forces on a world/in a fleet, as would be shown
    #: in the game UI
    ground_forces: float

    #: The amount of space forces that come from units that shoot missiles
    #: (as opposed to beam weapons)
    missile_forces: float

    #: The amount of space forces that come from units that are ships
    #: (as opposed to fixed point units or satellite units)
    maneuvering_unit_forces: float


class Anacreon:
    @classmethod
    async def log_in(cls, game_id: str, username: str, password: str) -> "Anacreon":
        """Authenticate with the Anacreon API using a Multiverse username and password

        Example:

            >>> import asyncio
            >>> async def main():
            ...     client = await Anacreon.log_in("8JNJ7FNZ", "username", "password")
            ...     # do stuff with client
            ...
            >>> asyncio.run(main())


        Args:
            game_id (str): The game ID of the game you intend to manipulate.
                You can find the game ID by looking at the URL when you are
                playing Anacreon in your browser. e.g if the URL was
                ``anacreon.kronosaur.com/trantor.hexm?gameID=8JNJ7FNZ``,
                the game ID would be ``8JNJ7FNZ``.

            username (str): The username to your Multiverse account
            password (str): The password to your Multiverse account

        Returns:
            Anacreon: An instance of the API client wrapper, which can be used
            to programmatically perform actions within the game
        """
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
        """Authenticate with the Anacreon API using an auth token

        You can get an auth token by looking at your cookies for
        `anacreon.kronosaur.com` in your browser's dev console.

        Args:
            game_id (str): The game ID of the game you intend to manipulate
            auth_token (str): A valid Multiverse auth token

        Returns:
            Anacreon: An instance of the API client wrapper, which can be used
            to programmatically perform actions within the game
        """
        client = client or AnacreonAsyncClient()
        game_info = await client.get_game_info(auth_token, game_id)

        auth_info: AnacreonApiRequest = AnacreonApiRequest(
            auth_token=auth_token,
            game_id=game_id,
            sovereign_id=game_info.user_info.sovereign_id,
        )

        ret = cls(auth_info, game_info, client=client)
        await ret.get_objects()
        return ret

    def __init__(
        self,
        auth_info: AnacreonApiRequest,
        game_info: ScenarioInfo,
        client: Optional[AnacreonAsyncClient] = None,
    ) -> None:
        """Construct an Anacreon instance directly

        Consider using one of the helper class methods like :func:`~anacreonlib.Anacreon.log_in` instead

        Args:
            auth_info (AnacreonApiRequest): A stub API request containing a valid auth token
            game_info (ScenarioInfo): Info about the game, such as all the traits that
            client (Optional[AnacreonAsyncClient], optional): The low-level API client to use in order to make HTTP
                requests. Defaults to None.
        """
        self._auth_info: AnacreonApiRequest = auth_info
        self._get_objects_event = asyncio.Event()
        self._state_updated_event = asyncio.Event()
        self._force_calculator = _MilitaryForceCalculator.from_game_info(game_info)

        self.logger = logging.getLogger(str(self.__class__.__name__))

        #: the low level API client that is used to make HTTP requests to the Anacreon API
        self.client: AnacreonAsyncClient = client or AnacreonAsyncClient()

        #: The scenario info for the game
        self.game_info: ScenarioInfo = game_info

        #: A mapping from trait/resource ID to :class:`ScenarioInfoElement`
        self.scenario_info_objects: Dict[int, ScenarioInfoElement] = {
            item_id: item
            for item in game_info.scenario_info
            if (item_id := item.id) is not None
        }

        #: A mapping from world/fleet ID to :class:`World` or :class:`Fleet` instance
        self.space_objects: Dict[int, Union[World, Fleet]] = dict()

        #: A mapping from siege ID to :class:`Siege` instances
        self.sieges: Dict[int, Siege] = dict()

        #: A mapping from sovereign ID to :class:`Sovereign` instance
        self.sovereigns: Dict[int, Sovereign] = {
            sov.id: sov for sov in game_info.sovereigns
        }

        #: A list of all history popups that would appear over your worlds in the game UI
        self.history: Dict[int, HistoryElement] = dict()

        self.update_obj: Optional[UpdateObject] = None

    @property
    def sov_id(self) -> int:
        """The sovereign ID of the currently logged in player"""
        return self._auth_info.sovereign_id

    async def get_objects(self) -> "Anacreon":
        """Refreshes game state from the Anacreon API to update world state,
        fleet state, and so on.

        Returns:
            Anacreon: this object
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
        """This coroutine waits until :meth:`Anacreon.get_objects` is called by
        someone else.

        One use case for this function is when you have 2 long-lived async
        :py:class:`~asyncio.Task` s running. One is caling
        :meth:`Anacreon.get_objects` every minute, while the other is
        managing a fleet. The task managing the fleet could to use this
        method to wait for updates to the state
        """
        await self._get_objects_event.wait()

    async def wait_for_any_update(self) -> None:
        """This coroutine waits until any method that updates game state, such as
        :func:`Anacreon.designate_world` or :func:`Anacreon.attack`, is called.

        One use case for this function is when you are just starting a script,
        and you spawn an :py:class:`~asyncio.Task` to periodically fetch updates.
        Your main coroutine would have to block until the task fetches the first
        update.
        """
        await self._state_updated_event.wait()

    def call_get_objects_periodically(self) -> "asyncio.Task[None]":
        """Spawns an :py:class:`~asyncio.Task` that calls
        :meth:`Anacreon.get_objects` every watch.

        Returns:
            asyncio.Task[None]: The task that was spawned.
        """

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
        """Abort an attack in progress

        Args:
            battlefield_id (int): The world ID of the planet that you are attacking
        """
        await self._do_action(AbortAttack(battlefield_id=battlefield_id))

    async def attack(
        self,
        battlefield_id: int,
        objective: BattleObjective,
        enemy_sovereign_ids: List[int],
    ) -> None:
        """Attack a world

        Args:
            battlefield_id (int): The ID of the world that you intend to attack
            objective (BattleObjective): Whether you want to invade, reinforce a
                siege, or destroy all space defenses
            enemy_sovereign_ids (List[int]): A list of the sovereign ids that
                you wish to engage in battle with
        """
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
        """Build an improvement

        Args:
            world_obj_id (int): The ID of the world to build the improvement on
            improvement_id (int): The trait ID of the improvement to build
        """
        partial_update = await self.client.build_improvement(
            AlterImprovementRequest(
                source_obj_id=world_obj_id,
                improvement_id=improvement_id,
                **self._auth_info.dict(),
            )
        )
        self._process_update(partial_update)

    async def buy_item(self, source_obj_id: int, item_id: int, item_count: int) -> None:
        """Buy an item from the Mesophons.

        As a prerequisite to calling this method, you must have a fleet
        stationed at the world where you wish to buy ships from.

        Args:
            source_obj_id (int): The ID of the world to buy ships from
            item_id (int): The resource ID of the ship that you wish to buy
            item_count (int): The number of ships that you wish to buy. Unlike
                the UI, which only lets you buy ships in groups of 1000, you may
                specify any number here.
        """
        await self._do_action(
            BuyItem(source_obj_id=source_obj_id, item_id=item_id, item_count=item_count)
        )

    async def deploy_fleet(
        self, source_obj_id: int, resources: IdValueMapping
    ) -> Optional[Fleet]:
        """Deploy a fleet

        Args:
            source_obj_id (int): The world or fleet from which you wish to
                create the fleet
            resources (IdValueMapping): A mapping from resource IDs to quantities.
                Can either be a dict, or a flat list alternating between ID and
                qty.

        Returns:
            Optional[Fleet]: The newly created fleet.
        """
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
        """Designate a world

        Args:
            world_obj_id (int): The ID of the world you wish to designate
            designation_id (int): The trait ID of the designation you wish to
                give the world
        """
        await self._do_action(
            DesignateWorld(source_obj_id=world_obj_id, new_designation=designation_id)
        )

    async def destroy_improvement(self, world_obj_id: int, improvement_id: int) -> None:
        """Destroy a structure/improvement on a world

        Args:
            world_obj_id (int): The ID of the world on which you want to destroy
                the structure
            improvement_id (int): The trait ID of the structure you wish to
                destroy
        """
        partial_update = await self.client.destroy_improvement(
            AlterImprovementRequest(
                source_obj_id=world_obj_id,
                improvement_id=improvement_id,
                **self._auth_info.dict(),
            )
        )
        self._process_update(partial_update)

    async def disband_fleet(self, fleet_obj_id: int, dest_obj_id: int) -> None:
        """Delete a fleet by forcing it to become a part of another object that
        it is stationed next to.

        You can use this method to gift fleets to enemy sovereigns.

        Args:
            fleet_obj_id (int): The ID of the fleet to disband
            dest_obj_id (int): The ID of the world/fleet that it should become a
                part of
        """
        await self._do_action(
            DisbandFleet(fleet_obj_id=fleet_obj_id, dest_obj_id=dest_obj_id)
        )

    async def launch_lams(self, source_obj_id: int, target_obj_id: int) -> None:
        """Launch jumpmissiles from a citadel

        Args:
            source_obj_id (int): The world ID of the citadel you wish to launch
                jumpmissiles from
            target_obj_id (int): The world/fleet ID you wish to shoot
                jumpmissiles at
        """
        await self._do_action(
            LaunchJumpMissile(source_obj_id=source_obj_id, target_obj_id=target_obj_id)
        )

    async def rename_object(self, obj_id: int, new_name: str) -> None:
        """Change the name of a world/fleet

        Args:
            obj_id (int): The ID of the object you wish to rename
            new_name (str): The object's new name
        """
        await self._do_action(RenameObject(obj_id=obj_id, name=new_name))

    async def sell_fleet(
        self, fleet_id: int, buyer_obj_id: int, resources: IdValueMapping
    ) -> None:
        """Sell a fleet (or fleet cargo) to the Mesophons

        As a prerequisite to calling this method, the fleet in question must
        already be stationed at a mesophon world.

        Args:
            fleet_id (int): The ID of the fleet to sell from
            buyer_obj_id (int): The ID of the Mesophon world you are selling to
            resources (IdValueMapping): The resources from the fleet which you
                are selling to the mesophons. You may choose to sell a portion
                of your resources, as opposed to all of the fleet's cargo or all
                of the ships.
        """
        await self._do_action(
            SellFleet(
                fleet_id=fleet_id,
                buyer_obj_id=buyer_obj_id,
                resources=_ensure_resources_list(resources),
            )
        )

    async def set_fleet_destination(self, fleet_obj_id: int, dest_obj_id: int) -> None:
        """Send a fleet somewhere

        Args:
            fleet_obj_id (int): The ID of the fleet
            dest_obj_id (int): The world ID of the fleet's desired destination
        """
        await self._do_action(
            SetFleetDestination(obj_id=fleet_obj_id, dest=dest_obj_id)
        )

    async def set_industry_alloc(
        self, world_id: int, industry_id: int, pct_labor_allocated: SupportsFloat
    ) -> None:
        """On a world, set the percent labor allocation to a structure

        For example, this method can be used to set the labor allocation to
        defense structures to 0%.

        Args:
            world_id (int): The ID of the world that the industry is on
            industry_id (int): The trait ID of the industry in question
            pct_labor_allocated (SupportsFloat): The percent of total labor on
                the world to allocate to this structure. This value should be
                between 0 and 100.
        """
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
        """Within a single industry, set the percent labor allocation to a
        single product of the industry.

        For example, this method can be used to set the labor allocation on a
        jumpship yards planet to spend 100% of the labor available to the yards
        structure on building Reliant-class jumptransports.

        Args:
            world_id (int): The ID of the world in question
            industry_id (int): The trait ID of the industry in question
            pct_labor_allocated_by_resource (IdValueMapping): A mapping from
                resource ID to percent labor allocation (from 0 to 100). This
                can either be a dict, or an alternating list.
        """
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
        """Create/update a trade route between 2 planets

        Args:
            importer_id (int): The ID of the world that is importing resources
            exporter_id (int): The ID of the world that is exporting resources
            alloc_type (TradeRouteTypes, optional): How to decide how the trade
                route should be set. Defaults to
                :py:attr:`TradeRouteTypes.DEFAULT`, which emulates the behavior
                of setting up a 1 way trade route between 2 unconnected planets
                in the game UI.
            alloc_value (Optional[Union[str, float]], optional): The percent of
                demand on the importing world to import from (between 0 and 999).
                Defaults to None.
            res_type_id (Optional[int], optional): The ID of the resource to
                import.
        """
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
        """Stop all trade between 2 planets

        If you need to stop trade on only one resource, you may do the set the
        percent of demand to import to 0 using :meth:`Anacreon.set_trade_route`
        with ``alloc_type`` as :py:attr:`TradeRouteTypes.CONSUMPTION`.

        Args:
            planet_id_a (int): The ID of one of the worlds on the trade route
            planet_id_b (int): The ID of another world on the trade route
        """
        await self._do_action(
            StopTradeRoute(planet_id_a=planet_id_a, planet_id_b=planet_id_b)
        )

    async def transfer_fleet(
        self, fleet_obj_id: int, dest_obj_id: int, resources: IdValueMapping
    ) -> None:
        """Transfer ships in a fleet to another fleet/world

        Args:
            fleet_obj_id (int): The ID of the fleet to transfer from
            dest_obj_id (int): The ID of the fleet/world to transfer to
            resources (IdValueMapping): The resources from the fleet to transfer
        """
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
        """Get battlefield information of a planet, such as battle groups and squadron locations

        Args:
            battlefield_id (str): The ID of the world to check

        Returns:
            List[Dict[str, Any]]: A list of dicts that is essentially the raw JSON
            returned by the API.

        Todo:
            Add models for this method to make it more type safe
        """
        return await self.client.get_tactical(
            GetTacticalRequest(battlefield_id=battlefield_id, **self._auth_info.dict())
        )

    async def tactical_order(
        self,
        battlefield_id: int,
        order: Union[TacticalOrderType, str],
        squadron_id: int,
        orbit: Optional[float] = None,
        target_id: Optional[int] = None,
    ) -> bool:
        """Send an order to a tactial squadron on a world

        Args:
            battlefield_id (int): The ID of the world
            order (Union[TacticalOrderType, str]): The order you are giving
            squadron_id (int): The ID of the squadron to give the order to
            orbit (Optional[float]): If ``order`` is
                :attr:`TacticalOrderType.ORBIT`, this should be the new orbit
                altitude
            target_id (Optional[int]): If ``order`` is
                :attr:`TacticalOrderType.TARGET`, this should be the id of the
                tactical squadron to target

        Returns:
            bool: ``True`` if the order was successfully processed
        """
        return await self.client.tactical_order(
            TacticalOrderRequest(
                battlefield_id=battlefield_id,
                order=order,
                squadron_id=squadron_id,
                orbit=orbit,
                target_id=target_id,
                **self._auth_info.dict(),
            )
        )

    async def set_history_read(self, history_id: int) -> bool:
        """Delet a history popup that show up over a planet

        You can see a list of all the history popups by looking at
        :py:attr:`Anacreon.history`.

        Args:
            history_id (int): The history ID of the popup as per
                :py:attr:`HistoryElement.id`.

        Returns:
            bool: ``True`` if the popup was successfully closed.
        """
        successfully_cleared = await self.client.set_history_read(
            SetHistoryReadRequest(history_id=history_id, **self._auth_info.dict())
        )
        if successfully_cleared:
            del self.history[history_id]

        return successfully_cleared

    async def send_message(self, recipient_sov_id: int, message_text: str) -> None:
        """Send a message to another empire

        Args:
            recipient_sov_id (int): The sovereign ID of the recipient empire
            message_text (str): The text of the message
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
        """Calculate production info for a world

        Args:
            world (Union[World, int]): Either the :class:`World` object, or the
                world ID.

        Raises:
            LookupError: Raised if `world` is a world ID that cannot be found

        Returns:
            Dict[int, ProductionInfo]: A mapping from resource ID to
            :class:`ProductionInfo` objects describing how much of that
            resource was imported/exported
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
        """Calculate the ground forces + space forces of a particular world/fleet

        Args:
            object_or_resources (Union[World, Fleet, IdValueMapping]): Either
                the :class:`World` object, the :class:`Fleet` object, or a
                list/dict of resources.

        Returns:
            MilitaryForceInfo: A dataclass containing the force information as
            it would be displayed in the Anacreon UI
        """
        return self._force_calculator.calculate_forces(object_or_resources)

    def calculate_remaining_cargo_space(self, fleet: Union[Fleet, int]) -> float:
        """Calculate the remaining cargo space on a fleet

        Args:
            fleet (Union[Fleet, int]): Either the :class:`Fleet` object, or the
                fleet ID

        Raises:
            LookupError: Raised if the fleet could not be found

        Returns:
            float: The remaining cargo space left in the fleet. Can be negative
            if uneven attrition has left more cargo in the fleet than it has
            space for.
        """
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
        """Returns a list of scenario elements which represent improvements that
        can be built on a given world.

        Args:
            world (World): The world in question

        Returns:
            List[ScenarioInfoElement]: A list of improvements that can be built.
        """
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
