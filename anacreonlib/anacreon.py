import sys
from typing import Tuple, Dict, Any, List, TypeVar, Optional

import requests
from anacreonlib.exceptions import AuthenticationException, HexArcException
import urllib.parse

Number = TypeVar("Number", int, float)

OneOrMoreNums = TypeVar("OneOrMoreNums", int, List[int])


class Anacreon:
    """
    Contains all the methods for interacting with the Anacreon API
    """

    def __init__(self, username: str = None, password: str = None, secure: bool = True, *, auth_token: Optional[str]=None) -> None:
        """
        Create a new instance of the API
        :param username: Your username
        :param password: Your password
        :param secure: Whether or not to force use of HTTPS as opposed to HTTP
        """

        self._HTTPS = True
        """Whether or not we are using HTTPS to communicate"""

        if auth_token is None:
            try:
                res = requests.post(
                    self._endpoint("login"),
                    data={"actual": True, "username": username, "password": password},
                ).json()
            except requests.exceptions.SSLError as e:
                if secure:
                    print(
                        "Could not connect using HTTPS. You can try again with secure=False, but that is insecure",
                        file=sys.stderr,
                    )
                    raise e
                else:
                    self._HTTPS = False
                    print("Warning: Using HTTP rather than HTTPS", file=sys.stderr)
                    res = requests.post(
                        self._endpoint("login"),
                        data={"actual": True, "username": username, "password": password},
                    ).json()

            try:
                self.authtoken_get = urllib.parse.quote_plus(res["authToken"])
                self.authtoken = res["authToken"]
            except KeyError:
                raise AuthenticationException(res[3])
        else:
            self.authtoken = auth_token
            self.authtoken_get = urllib.parse.quote_plus(auth_token)

        self.gameID = None
        self.sovID = None
        self.objects_dict = {}
        self.game_info = None
        self.sovereign_dict = {}
        self.history_dict = {}
        self.siege_dict = {}
        self.update_dict = {}
        self.scenario_info = {}
        self.sf_calc = {}
        self.gf_calc = {}

    def get_game_list(self) -> List[Dict[str, Any]]:
        """
        Get the list of games we are in right now (?)
        :return: said list
        """
        return requests.get(
            self._endpoint("gameList", params={"authToken": self.authtoken})
        ).json()

    def get_game_info(self) -> Dict[str, Any]:
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

        if self.gameID is None:
            raise ValueError("self.gameID must not be None")

        res = self._check_for_error(
            requests.get(
                self._endpoint(
                    "getGameInfo",
                    params={"authToken": self.authtoken_get, "gameID": self.gameID},
                )
            ).json()
        )

        self.game_info = res
        self._generate_force_calculation_dict()
        self._build_scenario_info()
        return res

    def get_objects(self) -> Dict[int, Dict[str, Any]]:
        """
        :return: A list of all objects that you have explored and data relevant to them, such as object ID's, planet
        designations, resources contained in fleets, and similar information relevant to gameplay
        """
        return self._make_api_request("getObjects", full=True)

    def deploy_fleet(
        self, resources: List[int], source_obj_id: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Deploy a fleet

        :param resources: A list that alternates between object ID and quantity. For example, suppose that Helions are
        ID number 100. To deploy 10 Helions, resources would have to be ``[100,  10]``

        :param source_obj_id: The ID of the object from which the new fleet will come from



        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "deployFleet", {"sourceObjID": source_obj_id, "resources": resources}
        )

    def transfer_fleet(
        self, dest_obj_id: int, fleet_obj_id: int, resources: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Transfer a fleet's resources

        :param dest_obj_id: The id of the object to which resources are being transferred
        :param resources: A list that alternates between object ID and change in quantity *for the fleet*. For example, suppose that Helions are
                          ID number 100. To transfer 10 Helions down to a planet, resources would have to be ``[100,  -10]``
        :param fleet_obj_id: The id of the fleet.
        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "transferFleet",
            {
                "fleetObjID": fleet_obj_id,
                "destObjID": dest_obj_id,
                "resources": resources,
                "source_obj_id": None,
            },
        )

    def disband_fleet(
        self, fleet_obj_id: int, dest_obj_id: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Disband a fleet to anyone/anything else

        Disbanding a fleet completely dissolves it. You can disband a fleet to yourself OR another sovereign.

        :param fleet_obj_id: The ID of the fleet which you are disbanding
        :param dest_obj_id: What you are disbanding it to (another world, another fleet, etc)
        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "disbandFleet", {"fleetObjID": fleet_obj_id, "destObjID": dest_obj_id}
        )

    def rename_object(self, id: int, new_name: str) -> Dict[int, Dict[str, Any]]:
        """
        Rename an object that belongs to your sovereign

        :param id: ID of the object
        :param new_name: The object's new name

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request("renameObject", {"objID": id, "name": new_name})

    def set_fleet_destination(
        self, fleet_id: int, dest_obj_id: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Send a fleet somewhere

        :param fleet_id: The ID of the fleet
        :param dest_obj_id: The ID of the planet to which you are sending the fleet

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "setDestination", {"objID": fleet_id, "dest": dest_obj_id}
        )

    def attack(
        self,
        victim_id: int,
        objective: str,
        sovereign: int = 1,
        battlefield_id: int = None,
    ) -> Dict[int, Dict[str, Any]]:
        """
        Initiate an attack on an object

        :param victim_id: The ID of the object that you are attacking
        :param objective: Whether you wish to invade (``"invasion"``) or clear space forces (``"spaceSupremacy"``)
        :param sovereign: The sovereign(s) that you are attacking (independent by default)
        :param battlefield_id: The ID of the battlefield

        :type sovereign: An integer (1 sovereign ID) or a list of integers (multiple sovereign ID's).
        :return: A refreshed version of ``Anacreon.get_objects()``
        """

        if objective not in ["invasion", "spaceSupremacy"]:
            raise ValueError("objective must be either 'invasion' or 'spaceSupremacy'")

        if battlefield_id is None:
            battlefield_id = victim_id

        if type(sovereign) is not list or tuple or set:
            sovereign = [int(sovereign)]

        data = {
            "attackerObjID": victim_id,
            "battlePlan": {
                "battleFieldID": battlefield_id,
                "objective": objective,
                "enemySovereignIDs": list(sovereign),
            },
        }

        return self._make_api_request("attack", data=data)

    def abort_attack(self, battlefield_id: int) -> Dict[int, Dict[str, Any]]:
        """
        Abort an attack

        :param battlefield_id: The ID of the planet at which the battle is occurring
        :return: A refreshed version of ``Anacreon.get_objects()``
        """

        return self._make_api_request("abortAttack", {"battleFieldID": battlefield_id})

    def launch_lams(self, world_id: int, target_id: int) -> Dict[int, Dict[str, Any]]:
        """
        Launch some jumpmissiles at a fleet

        :param world_id: The object ID of the world from which you are firing jumpmissiles
        :param target_id: The object ID of the thing at which you are firing jumpmissiles
        :return: A refreshed version of ``Anacreon.get_objects()``
        """

        return self._make_api_request(
            "launchLAMs", {"objID": world_id, "targetObjID": target_id}
        )

    def designate_world(
        self, world_id: int, designation_id: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Designate a world to something

        :param world_id: The ID of the world to designate
        :param designation_id: The scenario ID of the designation

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "designateWorld",
            {"sourceObjID": world_id, "newDesignation": designation_id},
        )

    def build_improvement(
        self, world_id: int, improvement_id: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Build an improvement on a world

        :param world_id: The ID of the world
        :param improvement_id: The scenario ID of the improvement

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "buildImprovement",
            {"sourceObjID": world_id, "improvementID": improvement_id},
        )

    def destroy_improvement(
        self, world_id: int, improvement_id: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Destroy an improvement

        :param world_id: The ID of the world
        :param improvement_id: The scenario ID of the improvement

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "destroyImprovement",
            {"sourceObjID": world_id, "improvementID": improvement_id},
        )

    def set_industry_alloc(
        self, world_id: int, industry_id: int, alloc_value: Number
    ) -> Dict[int, Dict[str, Any]]:
        """
        Change the allocation of an industry as a percent of labor on the world

        :param world_id: The object ID of the world on which the industry resides
        :param industry_id: The scenario ID of the industry
        :param alloc_value: What percent (between 0 and 100) of the world's labor should go to that industry

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "setIndustryAlloc",
            {"objID": world_id, "industryID": industry_id, "allocValue": alloc_value},
        )

    def set_product_alloc(
        self, world_id: int, industry_id: int, alloc: List[Number]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Change the allocation of how a structure produces its products

        :param world_id: The object ID of the world on which the industry resides
        :param industry_id: The scenario ID of the industry

        :param alloc: A list that alternates between the scenario ID of the product and how much labor should be used
                      to produce that product (as a percent of total labor allocated to the industry, between 0 and 100)

                      For example, suppose that Helions have a scenario ID of 100, and that Vanguards have a scenario
                      ID of 99. If I wanted my ship-producing industry to spend 80% of its labor on making Helions and
                      20% on Vanguards, alloc would be ``[100, 80, 99, 20]``


        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request(
            "setProductAlloc",
            {"objID": world_id, "industryID": industry_id, "alloc": alloc},
        )

    def set_trade_route(
        self,
        importer: int,
        exporter: int,
        alloc_type: str,
        alloc_value: float = None,
        res_type_id: int = None,
    ) -> Dict[int, Dict[str, Any]]:
        """
        Add a trade route between two worlds

        :param importer: The ID of the object that is importing stuff
        :param exporter: The ID of the object that is exporting stuff
        :param alloc_type: What allocValue means (``"tech"``, ``"consumption"`` or ``"addDefaultRoute"``. There are probably more)
        :param alloc_value: What percent of total consumption/what tech level/etc the importer should be importing from the exporter
        :param res_type_id: Indicates which resource alloc_value applies to

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        data = {"objID": importer, "sourceObjID": exporter, "allocType": alloc_type}

        if alloc_value is not None:
            data["allocValue"] = alloc_value
        if res_type_id is not None:
            data["resType"] = res_type_id

        return self._make_api_request("setTradeRoute", data)

    def stop_trade_route(
        self, planet_id_a: int, planet_id_b: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Stop a trade route between two planets

        :param planet_id_a: The ID of one of the planets involved in the trade route
        :param planet_id_b: The ID of the other planet involved in the trade route
        :return: A refreshed version of ``Anacreon.get_objects()``
        """

        return self._make_api_request(
            "stopTradeRoute", {"objID": planet_id_a, "sourceObjID": planet_id_b}
        )

    def buy_item(
        self, vendor_planet_id: int, item_id: int, item_count: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Buy something

        :param vendor_planet_id: The ID of the planet from whom you are buying stuff
        :param item_id: The ID of the item that you are buying
        :param item_count: How many things you are buying
        :return: A refreshed version of ``Anacreon.get_objects()``
        """

        return self._make_api_request(
            "buyItem",
            {
                "sourceObjID": vendor_planet_id,
                "itemID": item_id,
                "itemCount": item_count,
            },
        )

    def sell_fleet(
        self, fleet_id: int, buyer_obj_id: int, resources: List[int] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Sell a fleet to a planet

        :param fleet_id: The ID of the fleet that you are selling
        :param buyer_obj_id: The ID of the planet to whom you are selling your fleet
        :param resources: The resources that you want to sell in the alternating id-quantity form
        :return: A refreshed version of ``Anacreon.get_objects()``
        """

        if resources is None:
            resources = self.objects_dict[fleet_id]["resources"]

        return self._make_api_request(
            "sellFleet",
            {"objID": fleet_id, "buyerObjID": buyer_obj_id, "resources": resources},
        )

    def get_tactical(self, world_id: int) -> List[Dict[str, Any]]:
        """
        Get battlefield information of a planet, such as battle groups and squadron locations

        :param world_id: The ID of the planet

        :return: Battlefield info
        """
        return self._make_api_request("getTactical", {"objID": world_id}, process=False)

    def tactical_order(
        self, order: str, battlefield_id: int, squadron_tactical_id: int, **kwargs
    ) -> bool:
        """
        Give a tactical order

        :param order: Whether you wish to ``orbit`` at a certain altitude, ``land`` your transports, ``target`` another squadron, etc
        :param battlefield_id: The object ID of the battlefield
        :param squadron_tactical_id: The tactical ID of the
        :param kwargs: Keyword arguments specific to the tactical order, if applicable
        :return: If your order was carried out
        """

        data = {
            "objID": battlefield_id,
            "order": order,
            "tacticalID": squadron_tactical_id,
        }

        data.update(dict(**kwargs))

        return self._make_api_request("tacticalOrder", data, process=False)

    def set_history_read(self, history_id: int) -> bool:
        """
        Delete one of those popups that show up over planets

        :param history_id: The history ID of one of those popups, potentially found in ``Anacreon.history_dict``
        :return: If the popup was cleared successfully
        """

        return self._make_api_request(
            "setHistoryRead", {"historyID": history_id}, process=False
        )

    def send_message(self, recipient_id: int, message: str) -> None:
        """
        Send a message to another empire

        :param recipient_id: The ID of the sovereign to whom you're sending a message (it can be yourself)
        :param message: The message that you are sending
        :return: None
        """

        self._make_api_request(
            "sendMessage",
            {"recipientID": recipient_id, "messageText": message},
            process=False,
        )

    def _endpoint(self, endpoint: str, params: dict = None) -> str:
        """
        Make a request to a specified endpoint
        :param endpoint: The endpoint to make a request to
        :param params: Parameters to add onto the URL if this is a GET request
        :return: The full URL of the API endpoint
        """
        if endpoint[-1] == "/":
            endpoint = endpoint[:-1]
        if params is not None:
            endpoint += "/?" + self._dict_to_params(params)
        if self._HTTPS:
            return "https://anacreon.kronosaur.com/api/" + endpoint
        else:
            return "http://anacreon.kronosaur.com/api/" + endpoint

    def _make_api_request(
        self, endpoint: str, data: dict = None, headers: dict = None, **kwargs
    ) -> Any:
        """
        Make a request to the API
        :param endpoint: The endpoint of the API call (e.g ``getObjects``)
        :param data: The payload of the API call
        :param headers: The headers of the API call

        :return:
        """
        if data is None:
            data = {}

        data["authToken"] = self.authtoken
        data["gameID"] = self.gameID
        data["sovereignID"] = self.sovID

        res = requests.post(self._endpoint(endpoint), json=data, headers=headers).json()

        return self._check_for_error(res, **kwargs)

    def _check_for_error(
        self, res: Any, full: bool = False, process: bool = True
    ) -> Any:
        """
        Check if the response from the API indicates that an error has occurred

        :param res: A parsed response from the API
        :param full: If res is expected to contain all objects in the game
        :param process: If we should process the information
        :return: The result if it is not an error; otherwise, raise a `HexArcException`
        """
        if type(res) not in (dict, str) and type(res[0]) is str:
            raise HexArcException(res)
        elif type(res) is not list or not process:
            return res  # cannot possibly be a getObjects response
        else:
            if full:
                self.objects_dict = {}

            return self._process_update(res)

    def _process_update(
        self, update_list: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Process an update, whether it is partial or full

        :param update_list: A response from the API containing some data about game objects
        :return: The state of all known objects in the game in a dictionary where the key is object ID and value is object information
        """
        for thing in update_list:
            thing_class = thing["class"]

            if thing_class == "battlePlan":
                self.objects_dict[thing["id"]]["battlePlan"] = thing["battlePlan"]

            elif thing_class == "destroyedSpaceObject":
                try:
                    del self.objects_dict[thing["id"]]
                except KeyError:
                    pass  # couldn't find it; it's gone anyways

            elif thing_class == "fleet":
                self.objects_dict[thing["id"]] = thing

            # elif thing_class == "history":
            #     historyObj = thing

            # elif thing_class == "region":
            #     self.region_list[thing['id']] =  Region(thing)

            elif thing_class == "relationship":
                self.sovereign_dict[thing["id"]].relationship = thing["relationship"]

            # elif thing_class == "selection":
            #     SelectionID = thing['id']

            elif thing_class == "siege":
                self.siege_dict[thing["id"]] = thing

            elif thing_class == "sovereign":
                self.sovereign_dict[thing["id"]] = thing

            elif thing_class == "world":
                self.objects_dict[thing["id"]] = thing

            elif thing_class == "update":
                self.update_dict = thing

            elif thing_class == "history":
                for history_record in thing["history"]:
                    self.history_dict[history_record["id"]] = history_record

        return self.objects_dict

    def most_recent_fleet(self, refresh=False) -> int:
        """
        (utility method)
        Gets the most recently created fleet based on the fleet name

        The premise is that fleets have names like 5th fleet or 10th fleet i.e they are named sequentially. We find the
        fleet with the biggest number in its name

        :param refresh: Whether or not to refresh the objects cache

        :return: The ID of the most recently created fleet
        """
        if refresh:
            self.get_objects()

        candidate_fleets = {}
        for id, thing in self.objects_dict.items():
            if thing[u"class"] == "fleet":
                if int(thing[u"sovereignID"]) == self.sovID:
                    try:
                        candidate_fleets[int(thing[u"name"][:-8])] = thing[u"id"]

                    except (ValueError, IndexError):
                        # the fleet in question has existed long enough for a user to manually rename it
                        continue
        return candidate_fleets[max(list(candidate_fleets.keys()))]

    @staticmethod
    def _dict_to_params(dict: dict) -> str:
        """
        Convert a dictionary to parameters that belong at the end of URL for a GET request
        :param dict: A dictionary of ``{"keys": "values", "more_keys": "more_values", . . .}``
        :return: A string that belongs at the end of a URL
        """
        result = ""
        for key, val in dict.items():
            result += str(key) + "=" + str(val) + "&"
        return result

    @staticmethod
    def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """
        Given 2 ordered pairs, find the distance between them
        :param a: One point
        :param b: Another point
        :return: The distance
        """

        return ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5

    def get_obj_by_id(self, id: int, refresh: bool = False) -> Dict[str, Any]:
        """
        Get an object by its ID

        :param id: the ID of the object
        :param refresh: Whether or not to refresh the objects cache

        :return: The dictionary representing all the details of the object
        """

        if refresh:
            objects_dict = self.get_objects()
        else:
            objects_dict = self.objects_dict

        try:
            return objects_dict[id]
        except KeyError:
            raise KeyError("An object with ID " + str(id) + " was not found")

    def get_obj_by_name(self, name: str, refresh: bool = False) -> Dict[str, Any]:
        """
        Get an object by its name

        :param name: the name of the object
        :param refresh: Whether or not to refresh the objects cache

        :return: The dictionary representing all the details of the object
        """
        if refresh:
            self.get_objects()

        for id, obj in self.objects_dict.items():
            try:
                if obj[u"name"] == name:
                    return obj
            except KeyError:  # It is better to ask for forgiveness than to ask for permission
                pass
        raise NameError("An object with the name " + str(name) + " was not found")

    def get_fleet_ftl_speed(self, fleetobj: Dict[str, Any]) -> float:
        """
        Get the speed (in lightyears per watch) of a particular fleet

        :param fleetobj: The object containing information relevant to that fleet
        :return: The speed of the fleet
        """
        if self.game_info is None:
            self.get_game_info()

        if self.scenario_info == {}:
            self._build_scenario_info()

        ftl = 1000  # no fleet is this fast

        for resource_id in fleetobj["resources"][::2]:
            try:
                max_ship_speed = self.scenario_info[resource_id]["FTL"]
                ftl = min((max_ship_speed, ftl))
            except KeyError:
                pass

        if ftl == 1000:
            raise KeyError("None of the resources in this object seem to have a speed")

        return ftl

    def _build_scenario_info(self) -> Dict[int, Any]:
        if self.game_info is None:
            self.get_game_info()
        for thing in self.game_info["scenarioInfo"]:
            try:
                self.scenario_info[int(thing[u"id"])] = thing
            except KeyError:
                pass

        return self.scenario_info

    def get_fleet_eta(self, fleetobj: Dict[str, Any], refresh: bool = False) -> float:
        """
        Get the number of seconds that it will take for a fleet to arrive at its destination

        :param fleetobj: The object containing the information pertaining to the fleet
        :param refresh: If we should call `Anacreon.get_objects()` before calculating ETA
        :return: The number of seconds until the fleet will arrive at its destination
        """
        if refresh:
            self.get_objects()
        try:
            ms_to_next_watch = self.update_dict["nextUpdateTime"]

            ms_from_watch_start = 60000 - ms_to_next_watch

            ftl = self.get_fleet_ftl_speed(fleetobj)

            dist_to_dest = self.dist(fleetobj["pos"], fleetobj["dest"])

            watches_to_finish = fleetobj["eta"] - self.update_dict["update"]

            ms_to_finish = (watches_to_finish) * 60 * 1000  # watches to seconds to ms

            return (ms_to_finish - ms_from_watch_start) / 1000

        except KeyError:
            return 0.0  # fleet has probably arrived

    def generate_production_info(self, world_id: int, refresh: bool = False) -> dict:
        """
        Generate info that can be found in the production tab of a planet
        :param world_id: The ID of the planet to find production info for
        :param refresh: Whether or not to refresh the internal game objects cache
        :return: A list of all the things that the planet has produced, imported, exported, etc
        """

        # This is more or less exactly how the game client calculates production as well
        # I ported this from JavaScript
        worldobj = self.get_obj_by_id(world_id, refresh)

        result = {}

        def get_entry(resource_id: int) -> Dict[str, float]:
            if resource_id not in result.keys():
                result[resource_id] = {
                    "resType": resource_id,
                    "available": 0,
                    "consumed": 0,
                    "exported": 0,
                    "imported": 0,
                    "produced": 0,
                    "consumedOptimal": 0,
                    "exportedOptimal": 0,
                    "importedOptimal": 0,
                    "producedOptimal": 0,
                }
            return result[resource_id]

        if "baseConsumption" in worldobj.keys():
            # First we take into account the base consumption of the planet
            for i in range(0, len(worldobj["baseConsumption"]), 3):

                entry = get_entry(worldobj["baseConsumption"][i])
                optimal = worldobj["baseConsumption"][i + 1]
                actual = worldobj["baseConsumption"][i + 2]

                entry["consumedOptimal"] += optimal

                if actual is None:
                    entry["consumed"] += optimal
                else:
                    entry["consumed"] += actual

        for i, trait in enumerate(worldobj["traits"]):
            # Next, we take into account what our structures are consuming
            if type(trait) == dict:
                if "productionData" in trait.keys():
                    for j in range(0, len(trait["productionData"]), 3):

                        entry = get_entry(trait["productionData"][j])
                        optimal = trait["productionData"][j + 1]
                        actual = trait["productionData"][j + 2]

                        if optimal > 0.0:
                            entry["producedOptimal"] += optimal

                            if actual is None:
                                entry["produced"] += optimal
                            else:
                                entry["produced"] += actual
                        else:

                            entry["consumedOptimal"] += -optimal

                            if actual is None:
                                entry["consumed"] += -optimal
                            else:
                                entry["consumed"] += -actual

        if "tradeRoutes" in worldobj.keys():
            # Finally, we account for trade routes
            for tradeRoute in worldobj["tradeRoutes"]:
                exports = None
                imports = None
                if "return" in tradeRoute.keys():
                    # The data for this trade route belongs to another planet
                    partnerObj = self.get_obj_by_id(tradeRoute["partnerObjID"])
                    if partnerObj is not None:
                        for partnerTradeRoute in partnerObj["tradeRoutes"]:
                            if partnerTradeRoute["partnerObjID"] == world_id:
                                if "exports" in partnerTradeRoute.keys():
                                    imports = partnerTradeRoute["exports"]
                                if "imports" in partnerTradeRoute.keys():
                                    exports = partnerTradeRoute["imports"]
                else:
                    if "exports" in tradeRoute.keys():
                        exports = tradeRoute["exports"]
                    if "imports" in tradeRoute.keys():
                        imports = tradeRoute["imports"]

                if exports is not None:
                    for j in range(0, len(exports), 4):
                        entry = get_entry(exports[j])
                        optimal = exports[j + 2]
                        actual = exports[j + 3]

                        if actual is None:

                            entry["exported"] += optimal
                        else:
                            entry["exported"] += actual

                        entry["exportedOptimal"] += optimal

                if imports is not None:
                    for j in range(0, len(imports), 4):
                        entry = get_entry(imports[j])
                        optimal = imports[j + 2]
                        actual = imports[j + 3]

                        if actual is None:

                            entry["imported"] += optimal
                        else:
                            entry["imported"] += actual

                        entry["importedOptimal"] += optimal

                if "resources" in worldobj.keys():
                    for i in range(0, len(worldobj["resources"]), 2):
                        resID = worldobj["resources"][i]
                        count = worldobj["resources"][i + 1]

                        if count > 0:
                            result[resID] = get_entry(resID)
                            result[resID]["available"] = count

        return result

    def get_forces(self, resources: list) -> Tuple[float, float]:
        """
        Calculate the space and ground force of something

        :param resources: The resources list of the object
        :return: A tuple of the form (space force, ground force)
        """
        if self.sf_calc is None or self.gf_calc is None:
            self._generate_force_calculation_dict()
        currentID = None
        sf = 0.0
        gf = 0.0
        for i, x in enumerate(resources):
            if i % 2 == 0:
                currentID = x  # x is the id of the resource
            else:

                if currentID in self.sf_calc.keys():  # x is the count of the resource
                    sf += float(x) * self.sf_calc[currentID] / 100.0
                elif currentID in self.gf_calc.keys():
                    gf += float(x) * self.gf_calc[currentID] / 100.0
        return sf, gf

    def _generate_force_calculation_dict(self) -> None:
        """
        Generate the dictionaries required to calculate space and ground force of an object

        :return: None
        """
        if self.game_info is None:
            self.get_game_info()
        for item in self.game_info["scenarioInfo"]:
            try:
                if (
                    item[u"category"] == "fixedUnit"
                    or item["category"] == "orbitalUnit"
                    or item["category"] == "maneuveringUnit"
                ):
                    self.sf_calc[int(item["id"])] = float(item["attackValue"])
                elif item["category"] == "groundUnit":
                    self.gf_calc[int(item["id"])] = float(item["attackValue"])
            except KeyError:
                # There are 3 or 4 items in the scenario info that do not have a category
                continue
