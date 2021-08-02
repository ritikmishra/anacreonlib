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
        """Retrieve an auth token from the Anacreon API using Multiverse login
        credentials

        Args:
            username_and_pw (AuthenticationRequest): An object containing
                Multiverse login credentials

        Returns:
            AuthenticationResponse: Response object containing auth token
        """
    async def get_game_list(self, auth_token: str) -> List[Dict[Any, Any]]:
        """Get the list of games we are in right now

        Args:
            auth_token (str): API auth token

        Returns:
            List[Dict[Any, Any]]: JSON response
        """
    async def get_game_info(self, auth_token: str, game_id: str) -> ScenarioInfo:
        """Get information about the game

        This includes
        - Info about the scenario
            - All the items/designations/etc that could exist and their ID's
        - Info about the game
            - All the sovereigns and their ID's
        - Your user info
            - Your sovereign ID, capital ID, etc

        Args:
            auth_token (str): API auth token
            game_id (str): Which game to return info for

        Returns:
            ScenarioInfo: The game info
        """
    async def get_objects(self, request: AnacreonApiRequest) -> List[AnacreonObject]:
        """Get a list of all of the objects in the game

        Args:
            request (AnacreonApiRequest): Request object containing API auth token

        Returns:
            List[AnacreonObject]: A list of all objects in the game
        """
    async def deploy_fleet(self, request: DeployFleetRequest) -> List[AnacreonObject]:
        """Deploy a fleet

        Args:
            request (DeployFleetRequest): Request object containing API auth
                token, where to deploy the fleet, etc

        Returns:
            List[AnacreonObject]: A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def transfer_fleet(
        self, request: TransferFleetRequest
    ) -> List[AnacreonObject]:
        """Transfer a fleet's resources

        Args:
            request (TransferFleetRequest): Request object containing API auth
                token and details about the transfer

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def disband_fleet(self, request: DisbandFleetRequest) -> List[AnacreonObject]:
        """Disband a fleet, merging it with another object (even if the other
        object belongs to another sovereign)

        Args:
            request (DisbandFleetRequest): Request object containing API auth
                token and the ID of the fleet to disband

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def rename_object(self, request: RenameObjectRequest) -> List[AnacreonObject]:
        """Rename an object that belongs to your sovereign

        Args:
            request (RenameObjectRequest): Request object containing API auth
                token, details about the renaming operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def set_fleet_destination(
        self, request: SetFleetDestinationRequest
    ) -> List[AnacreonObject]:
        """Send a fleet somewhere

        Args:
            request (SetFleetDestinationRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def attack(self, request: AttackRequest) -> List[AnacreonObject]:
        """Initiate an attack on an object

        Args:
            request (AttackRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def abort_attack(self, request: AbortAttackRequest) -> List[AnacreonObject]:
        """Abort an attack

        Args:
            request (AbortAttackRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def launch_lams(
        self, request: LaunchJumpMissileRequest
    ) -> List[AnacreonObject]:
        """Launch some jumpmissiles at a fleet

        Args:
            request (LaunchJumpMissileRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def designate_world(
        self, request: DesignateWorldRequest
    ) -> List[AnacreonObject]:
        """Change a world's designation

        Args:
            request (DesignateWorldRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def build_improvement(
        self, request: AlterImprovementRequest
    ) -> List[AnacreonObject]:
        """Build an improvement on a world

        Args:
            request (AlterImprovementRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def destroy_improvement(
        self, request: AlterImprovementRequest
    ) -> List[AnacreonObject]:
        """Destroy an improvement

        Args:
            request (AlterImprovementRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def set_industry_alloc(
        self, request: SetIndustryAllocRequest
    ) -> List[AnacreonObject]:
        """For a single industry on a single world, change its percent
        allocation of total labor.

        Typically, you can only freely set the labor allocation of defense
        structures.

        Args:
            request (SetIndustryAllocRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def set_product_alloc(
        self, request: SetProductAllocRequest
    ) -> List[AnacreonObject]:
        """For a single product type produced by a single industry on a single
        world, change the percent allocation of labor in the industry allocated
        towards making that product.

        Typically, you can only freely set product labor allocation on shipyard
        industries (i.e you can tell your ship yards to produce 50% transports
        and 50% gunships)

        Args:
            request (SetProductAllocRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def set_trade_route(
        self, request: SetTradeRouteRequest
    ) -> List[AnacreonObject]:
        """Add or update a trade route between two worlds

        Args:
            request (SetTradeRouteRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def stop_trade_route(
        self, request: StopTradeRouteRequest
    ) -> List[AnacreonObject]:
        """Stop all trade between 2 planets

        Args:
            request (StopTradeRouteRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def buy_item(self, request: BuyItemRequest) -> List[AnacreonObject]:
        """Buy some quantity of an item from a Mesophon world

        Args:
            request (BuyItemRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def sell_fleet(self, request: SellFleetRequest) -> List[AnacreonObject]:
        """Sell a fleet to a Mesophon world

        Args:
            request (SellFleetRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[AnacreonObject]:  A partial, refreshed version of the
            :py:meth:`~AnacreonAsyncClient.get_objects` response
        """
    async def get_tactical(
        self, battlefield_id: GetTacticalRequest
    ) -> List[Dict[str, Any]]:
        """Get information about the battlefield on a single planet

        This corresponds to the view you get when you zoom in all the way on a
        planet, and you are able to see individual ship groups.

        Args:
            battlefield_id (GetTacticalRequest): Request object containing
                API auth token + details about the operation

        Returns:
            List[Dict[str, Any]]: JSON response
        """
    async def tactical_order(self, order: TacticalOrderRequest) -> bool:
        """Give an order to a ship group orbiting a world

        Args:
            order (TacticalOrderRequest): Request object containing
                API auth token + details about the operation

        Returns:
            bool: ``True`` if your order was carried out successfully
        """
    async def set_history_read(self, history_id: SetHistoryReadRequest) -> bool:
        """Delete a history popup that shows up over planets or fleets

        Args:
            history_id (SetHistoryReadRequest): Request object containing
                API auth token + details about the operation

        Returns:
            bool: ``True`` if your order was carried out successfully
        """
    async def send_message(self, message: SendMessageRequest) -> None:
        """Send a message to another empire

        Args:
            message (SendMessageRequest): Request object containing
                API auth token + details about the operation
        """
