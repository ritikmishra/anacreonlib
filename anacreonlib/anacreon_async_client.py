# type: ignore
# uplink does not play well with type checking
import asyncio
from typing import List, Dict, Any

import aiohttp
import uplink
from uplink import Consumer, post, returns, Query, get, Body, clients
from uplink.retry import retry
from uplink.retry.when import raises

from anacreonlib.types.request_datatypes import *
from anacreonlib.types.response_datatypes import (
    AuthenticationResponse,
    convert_json_to_anacreon_obj,
    AnacreonObject,
    handle_hexarc_error_response,
)
from anacreonlib.types.scenario_info_datatypes import (
    ScenarioInfo,
    convert_json_to_scenario_info,
)


@uplink.timeout(10)
@uplink.retry(when=raises(retry.CONNECTION_TIMEOUT))
@uplink.json
@returns.json
@handle_hexarc_error_response
class AnacreonAsyncClient(Consumer):
    """
    A coroutine-based asynchronous API client to interact with anacreon
    """

    def __init__(
        self, *, base_url: str = "https://anacreon.kronosaur.com/api/"
    ) -> None:
        self._aio_session = aiohttp.ClientSession()
        super().__init__(
            base_url=base_url,
            client=clients.AiohttpClient(session=self._aio_session),
            converter=(
                pydantic_request_converter,
                convert_json_to_anacreon_obj,
                convert_json_to_scenario_info,
            ),
        )

    def __del__(self):
        """Ensures the session was closed"""
        if not self._aio_session.closed:
            asyncio.run(self._aio_session.close())

    @post("login")
    async def authenticate_user(
        self, username_and_pw: Body(type=AuthenticationRequest)
    ) -> AuthenticationResponse:
        """
        Logs you into Anacreon. Does not on its own throw an error if you get your password
        wrong!

        :type username: str
        :param username: Username of account to log in as

        :type password: str
        :param password: Password of account to log in as

        :param actual: If false, forces the request to fail
        :type actual: bool

        :return: JSON response.
        """

    @get("gameList")
    async def get_game_list(self, auth_token: Query("authToken")):
        """
        Get the list of games we are in right now (?)
        :return: said list
        """

    @get("getGameInfo")
    async def get_game_info(
        self, auth_token: Query("authToken"), game_id: Query("gameID")
    ) -> ScenarioInfo:
        """
        Get information about the game such as

        - Info about the scenario
            - All the items/designations/etc that could exist and their ID's
        - Info about the game
            - All the sovereigns and their ID's
        - Your user info
            - Your sovereign ID, capital ID, etc

        :return: Said information
        """

    @post("getObjects/")
    async def get_objects(
        self, request: Body(type=AnacreonApiRequest)
    ) -> List[AnacreonObject]:
        """
        :return: A list of all objects that you have explored and data relevant to them, such as object ID's, planet
        designations, resources contained in fleets, and similar information relevant to gameplay
        """

    @post("deployFleet")
    async def deploy_fleet(
        self, request: Body(type=DeployFleetRequest)
    ) -> List[AnacreonObject]:
        """
        Deploy a fleet
        :return: A refreshed version of the ``get_objects`` response
        """

    @post("transferFleet")
    async def transfer_fleet(
        self, request: Body(type=TransferFleetRequest)
    ) -> List[AnacreonObject]:
        """
        Transfer a fleet's resources

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("disbandFleet")
    async def disband_fleet(
        self, request: Body(type=DisbandFleetRequest)
    ) -> List[AnacreonObject]:
        """
        Disband a fleet to anyone/anything else

        Disbanding a fleet completely dissolves it. You can disband a fleet to yourself OR another sovereign.

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("renameObject")
    async def rename_object(
        self, request: Body(type=RenameObjectRequest)
    ) -> List[AnacreonObject]:
        """
        Rename an object that belongs to your sovereign

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("setDestination")
    async def set_fleet_destination(
        self, request: Body(type=SetFleetDestinationRequest)
    ) -> List[AnacreonObject]:
        """
        Send a fleet somewhere

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("attack")
    async def attack(self, request: Body(type=AttackRequest)) -> List[AnacreonObject]:
        """
        Initiate an attack on an object

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("abortAttack")
    async def abort_attack(
        self, request: Body(type=AbortAttackRequest)
    ) -> List[AnacreonObject]:
        """
        Abort an attack

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("launchLAMs")
    async def launch_lams(
        self, request: Body(type=LaunchJumpMissileRequest)
    ) -> List[AnacreonObject]:
        """
        Launch some jumpmissiles at a fleet

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("designateWorld")
    async def designate_world(
        self, request: Body(type=DesignateWorldRequest)
    ) -> List[AnacreonObject]:
        """
        Designate a world to something

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("buildImprovement")
    async def build_improvement(
        self, request: Body(type=AlterImprovementRequest)
    ) -> List[AnacreonObject]:
        """
        Build an improvement on a world

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("destroyImprovement")
    async def destroy_improvement(
        self, request: Body(type=AlterImprovementRequest)
    ) -> List[AnacreonObject]:
        """
        Destroy an improvement

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("setIndustryAlloc")
    async def set_industry_alloc(
        self, request: Body(type=SetIndustryAllocRequest)
    ) -> List[AnacreonObject]:
        """
        Change the allocation of an industry as a percent of labor on the world

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("setProductAlloc")
    async def set_product_alloc(
        self, request: Body(type=SetProductAllocRequest)
    ) -> List[AnacreonObject]:
        """
        Change the allocation of how a structure produces its products

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("setTradeRoute")
    async def set_trade_route(
        self, request: Body(type=SetTradeRouteRequest)
    ) -> List[AnacreonObject]:
        """
        Add a trade route between two worlds

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("stopTradeRoute")
    async def stop_trade_route(
        self, request: Body(type=StopTradeRouteRequest)
    ) -> List[AnacreonObject]:
        """
        Stop a trade route between two planets

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("buyItem")
    async def buy_item(
        self, request: Body(type=BuyItemRequest)
    ) -> List[AnacreonObject]:
        """
        Buy something

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("sellFleet")
    async def sell_fleet(
        self, request: Body(type=SellFleetRequest)
    ) -> List[AnacreonObject]:
        """
        Sell a fleet to a planet

        :return: A refreshed version of ``Anacreon.get_objects()``
        """

    @post("getTactical")
    async def get_tactical(
        self, battlefield_id: Body(type=GetTacticalRequest)
    ) -> List[Dict[str, Any]]:
        """
        Get battlefield information of a planet, such as battle groups and squadron locations

        :return: Battlefield info
        """

    @post("tacticalOrder")
    async def tactical_order(self, order: Body(type=TacticalOrderRequest)) -> bool:
        """
        Give a tactical order

        :return: If your order was carried out
        """

    @post("setHistoryRead")
    async def set_history_read(
        self, history_id: Body(type=SetHistoryReadRequest)
    ) -> bool:
        """
        Delete one of those popups that show up over planets

        :return: If the popup was cleared successfully
        """

    @post("sendMessage")
    async def send_message(self, message: Body(type=SendMessageRequest)) -> None:
        """
        Send a message to another empire

        :return: None
        """
