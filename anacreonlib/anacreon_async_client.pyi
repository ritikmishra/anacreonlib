from anacreonlib.types.response_datatypes import AnacreonObject, AuthenticationResponse
from anacreonlib.types.scenario_info_datatypes import ScenarioInfo
from typing import Any, Dict, List
from anacreonlib.types.request_datatypes import (
    AbortAttackRequest,
    AlterImprovementRequest,
    AnacreonApiRequest,
    AttackRequest,
    AuthenticationRequest,
    BuyItemRequest,
    DeployFleetRequest,
    DesignateWorldRequest,
    DisbandFleetRequest,
    GetTacticalRequest,
    LaunchJumpMissileRequest,
    RenameObjectRequest,
    SellFleetRequest,
    SendMessageRequest,
    SetFleetDestinationRequest,
    SetHistoryReadRequest,
    SetIndustryAllocRequest,
    SetProductAllocRequest,
    SetTradeRouteRequest,
    StopTradeRouteRequest,
    TacticalOrderRequest,
    TransferFleetRequest,
)

class AnacreonAsyncClient:
    """
    A coroutine-based asynchronous API client to interact with anacreon
    """

    def __init__(self, *, base_url: str = ...) -> None: ...
    async def authenticate_user(
        self, username_and_pw: AuthenticationRequest
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
    async def get_game_list(self, auth_token: str) -> List[Dict[Any, Any]]:
        """
        Get the list of games we are in right now (?)
        :return: said list
        """
    async def get_game_info(self, auth_token: str, game_id: str) -> ScenarioInfo:
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
    async def get_objects(self, request: AnacreonApiRequest) -> List[AnacreonObject]:
        """
        :return: A list of all objects that you have explored and data relevant to them, such as object ID's, planet
        designations, resources contained in fleets, and similar information relevant to gameplay
        """
    async def deploy_fleet(self, request: DeployFleetRequest) -> List[AnacreonObject]:
        """
        Deploy a fleet
        :return: A refreshed version of the ``get_objects`` response
        """
    async def transfer_fleet(
        self, request: TransferFleetRequest
    ) -> List[AnacreonObject]:
        """
        Transfer a fleet's resources

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def disband_fleet(self, request: DisbandFleetRequest) -> List[AnacreonObject]:
        """
        Disband a fleet to anyone/anything else

        Disbanding a fleet completely dissolves it. You can disband a fleet to yourself OR another sovereign.

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def rename_object(self, request: RenameObjectRequest) -> List[AnacreonObject]:
        """
        Rename an object that belongs to your sovereign

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def set_fleet_destination(
        self, request: SetFleetDestinationRequest
    ) -> List[AnacreonObject]:
        """
        Send a fleet somewhere

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def attack(self, request: AttackRequest) -> List[AnacreonObject]:
        """
        Initiate an attack on an object

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def abort_attack(self, request: AbortAttackRequest) -> List[AnacreonObject]:
        """
        Abort an attack

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def launch_lams(
        self, request: LaunchJumpMissileRequest
    ) -> List[AnacreonObject]:
        """
        Launch some jumpmissiles at a fleet

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def designate_world(
        self, request: DesignateWorldRequest
    ) -> List[AnacreonObject]:
        """
        Designate a world to something

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def build_improvement(
        self, request: AlterImprovementRequest
    ) -> List[AnacreonObject]:
        """
        Build an improvement on a world

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def destroy_improvement(
        self, request: AlterImprovementRequest
    ) -> List[AnacreonObject]:
        """
        Destroy an improvement

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def set_industry_alloc(
        self, request: SetIndustryAllocRequest
    ) -> List[AnacreonObject]:
        """
        Change the allocation of an industry as a percent of labor on the world

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def set_product_alloc(
        self, request: SetProductAllocRequest
    ) -> List[AnacreonObject]:
        """
        Change the allocation of how a structure produces its products

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def set_trade_route(
        self, request: SetTradeRouteRequest
    ) -> List[AnacreonObject]:
        """
        Add a trade route between two worlds

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def stop_trade_route(
        self, request: StopTradeRouteRequest
    ) -> List[AnacreonObject]:
        """
        Stop a trade route between two planets

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def buy_item(self, request: BuyItemRequest) -> List[AnacreonObject]:
        """
        Buy something

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def sell_fleet(self, request: SellFleetRequest) -> List[AnacreonObject]:
        """
        Sell a fleet to a planet

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
    async def get_tactical(
        self, battlefield_id: GetTacticalRequest
    ) -> List[Dict[str, Any]]:
        """
        Get battlefield information of a planet, such as battle groups and squadron locations

        :return: Battlefield info
        """
    async def tactical_order(self, order: TacticalOrderRequest) -> bool:
        """
        Give a tactical order

        :return: If your order was carried out
        """
    async def set_history_read(self, history_id: SetHistoryReadRequest) -> bool:
        """
        Delete one of those popups that show up over planets

        :return: If the popup was cleared successfully
        """
    async def send_message(self, message: SendMessageRequest) -> None:
        """
        Send a message to another empire

        :return: None
        """
