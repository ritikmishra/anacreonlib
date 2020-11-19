import asyncio
from typing import Dict, Any

import aiohttp
from uplink import Consumer, json, post, Field, returns, Query, get, Body, clients
from uplink.types import List

from anacreonlib.types.request_datatypes import (
    AnacreonApiRequest,
    DeployFleetRequest,
    pydantic_request_converter,
)
from anacreonlib.types.response_datatypes import (
    convert_json_to_anacreon_obj,
    AnacreonObject,
)


@json
@returns.json
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
            converter=(pydantic_request_converter, convert_json_to_anacreon_obj),
        )

    def __del__(self):
        """Ensures the session was closed"""
        if not self._aio_session.closed:
            asyncio.run(self._aio_session.close())

    @post("login")
    async def authenticate_user(
        self, username: Field, password: Field, actual: Field = True
    ):
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
    ):
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
    def deploy_fleet(
        self, request: Body(type=DeployFleetRequest)
    ) -> List[AnacreonObject]:
        """
        Deploy a fleet
        :return: A refreshed version of the ``get_objects`` response
        """
