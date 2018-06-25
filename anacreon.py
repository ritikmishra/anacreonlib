import sys
from typing import Tuple, Dict, Any, List

import requests
from anacreonlib.exceptions import AuthenticationException, HexArcException
import urllib.parse

from copy import deepcopy


class Anacreon:
    """
    Contains all the methods for interacting with the Anacreon API
    """

    def __init__(self, username: str, password: str, secure: bool = True) -> None:
        """
        Create a new instance of the API
        :param username: Your username
        :param password: Your password
        :param secure: Whether or not to force use of HTTPS as opposed to HTTP
        """

        self._HTTPS = True
        """Whether or not we are using HTTPS to communicate"""

        try:
            res = requests.post(self._endpoint("login"),
                                data={"actual": True, "username": username, "password": password}).json()
        except requests.exceptions.SSLError as e:
            if secure:
                print("Could not connect using HTTPS. You can try again with secure=False, but that is insecure",
                      file=sys.stderr)
                raise e
            else:
                self._HTTPS = False
                print("Warning: Using HTTP rather than HTTPS", file=sys.stderr)
                res = requests.post(self._endpoint("login"),
                                    data={"actual": True, "username": username, "password": password}).json()

        try:
            self.authtoken_get = urllib.parse.quote_plus(res["authToken"])
            self.authtoken = res["authToken"]
        except KeyError:
            raise AuthenticationException(res[3])

        self.gameID = None
        self.sovID = None
        self.game_objects_cache = {}
        self._sf_calc = None
        self._gf_calc = None

    def get_game_list(self) -> List[Dict[str, Any]]:
        """
        Get the list of games we are in right now (?)
        :return: said list
        """
        return requests.get(self._endpoint("gameList", params={"authToken": self.authtoken})).json()

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

        res = requests.get(
            self._endpoint("getGameInfo", params={"authToken": self.authtoken_get, "gameID": self.gameID})).json()

        return self._check_for_error(res, cache=False)

    def get_objects(self, cache: bool = True) -> List[Dict[str, Any]]:
        """
        :return: A list of all objects that you have explored and data relevant to them, such as object ID's, planet
        designations, resources contained in fleets, and similar information relevant to gameplay
        """
        return self._make_api_request("getObjects", cache=cache)

    def deploy_fleet(self, resources: List[int], source_obj_id: int, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Deploy a fleet

        :param resources: A list that alternates between object ID and quantity. For example, suppose that Helions are
        ID number 100. To deploy 10 Helions, resources would have to be ``[100,  10]``

        :param source_obj_id: The ID of the object from which the new fleet will come from

        :param cache: Whether or not to cache the result in ``self.game_objects_cache``

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request("deployFleet", {"sourceObjID": source_obj_id, "resources": resources},
                                      cache=cache)

    def transfer_fleet(self, dest_obj_id: int, fleet_obj_id: int, resources: List[int], cache: bool = True) -> List[
        Dict[str, Any]]:
        """
        Transfer a fleet's resources

        :param dest_obj_id: The id of the object to which resources are being transferred
        :param resources: A list that alternates between object ID and change in quantity *for the fleet*. For example, suppose that Helions are
        ID number 100. To tranfer 10 Helions down to a planet, resources would have to be ``[100,  -10]``

        :param fleet_obj_id: The id of the fleet.

        :param cache: Whether or not to cache the result in ``self.game_objects_cache``

        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request("transferFleet",
                                      {"fleetObjID": fleet_obj_id, "destObjID": dest_obj_id, "resources": resources,
                                       "source_obj_id": None}, cache=cache)

    def rename_object(self, id: int, new_name: str, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Rename an object that belongs to your sovereign

        :param id: ID of the object
        :param new_name: The object's new name
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request("renameObject", {"objID": id, "name": new_name}, cache=cache)

    def set_fleet_destination(self, fleet_id: int, dest_obj_id: int, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Send a fleet somewhere

        :param fleet_id: The ID of the fleet
        :param dest_obj_id: The ID of the planet to which you are sending the fleet
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request("setDestination", {"objID": fleet_id, "dest": dest_obj_id}, cache=cache)

    def attack(self, victim_id: int, objective: str, sovereign: int = 1, battlefield_id: int = None,
               cache: bool = True) -> List[Dict[str, Any]]:
        """
        Initiate an attack on an object

        :param victim_id: The ID of the object that you are attacking
        :param objective: Whether you wish to invade (``"invasion"``) or clear space forces (``"spaceSupremacy"``)
        :param sovereign: The sovereign that you are attacking (independent by default)
        :param battlefield_id: The ID of the battlefield
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: A refreshed version of ``Anacreon.get_objects()``
        """

        if objective not in ['invasion', 'spaceSupremacy']:
            raise ValueError("objective must be either 'invasion' or 'spaceSupremacy'")

        if battlefield_id is None:
            battlefield_id = victim_id

        data = {
            "attackerObjID": victim_id,
            "battlePlan": {
                "battleFieldID": battlefield_id,
                "objective": objective,
                "enemySovereignIDs": [int(sovereign)]
            }
        }

        return self._make_api_request("attack", data=data, cache=cache)

    def designate_world(self, world_id: int, designation_id: int, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Designate a world to something

        :param world_id: The ID of the world to designate
        :param designation_id: The scenario ID of the designation
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request("designateWorld", {"sourceObjID": world_id, "newDesignation": designation_id},
                                      cache=cache)

    def build_improvement(self, world_id: int, improvement_id: int, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Build an improvement on a world

        :param world_id: The ID of the world
        :param improvement_id: The scenario ID of the improvement
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request("buildImprovement", {"sourceObjID": world_id, "improvementID": improvement_id},
                                      cache=cache)

    def set_industry_alloc(self, world_id: int, industry_id: int, alloc_value: float, cache: bool = False) -> List[
        Dict[str, Any]]:
        """
        Change the allocation of an industry as a percent of labor on the world

        :param world_id: The object ID of the world on which the industry resides
        :param industry_id: The scenario ID of the industry
        :param alloc_value: What percent (between 0 and 100) of the world's labor should go to that industry
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        return self._make_api_request("setIndustryAlloc",
                                      {"objID": world_id, "industryID": industry_id, "allocValue": alloc_value},
                                      cache=cache)

    def set_trade_route(self, importer: int, exporter: int, alloc_type: str, alloc_value: Any = None,
                        cache: bool = True) -> List[Dict[str, Any]]:
        """
        Add a trade route between two worlds

        :param importer: The ID of the object that is importing stuff
        :param exporter: The ID of the object that is exporting stuff
        :param alloc_type: The type of allocation (``"tech"`` or ``"addDefaultRoute"``)
        :param alloc_value: ?
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: A refreshed version of ``Anacreon.get_objects()``
        """
        data = {"objID": importer, "sourceObjID": exporter, "allocType": alloc_type}

        if alloc_value is not None:
            data["allocValue"] = alloc_value

        return self._make_api_request("setTradeRoute", data, cache=cache)

    def get_tactical(self, world_id: int) -> List[Dict[str, Any]]:
        """
        Get battlefield information of a planet, such as battle groups and squadron locations

        :param world_id: The ID of the planet
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: Battlefield info
        """
        return self._make_api_request("getTactical", {"objID": world_id}, cache=False)

    def most_recent_fleet(self, refresh=False, cache: bool = True) -> int:
        """
        (utility method)
        Gets the most recently created fleet based on the fleet name

        The premise is that fleets have names like 5th fleet or 10th fleet i.e they are named sequentially. We find the
        fleet with the biggest number in its name

        :param refresh: Whether or not to refresh the objects cache
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: The ID of the most recently created fleet
        """
        if refresh:
            self.get_objects(cache=cache)

        candidate_fleets = {}
        for thing in self.game_objects_cache:
            if thing[u'class'] == "fleet":
                if int(thing[u'sovereignID']) == self.sovID:
                    try:
                        candidate_fleets[int(thing[u"name"][:-8])] = thing[u'id']

                    except (ValueError, IndexError):
                        # the fleet in question has existed long enough for a user to manually rename it
                        continue
        return candidate_fleets[max(list(candidate_fleets.keys()))]

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

    def _make_api_request(self, endpoint: str, data: dict = None, headers: dict = None, cache: bool = True) -> Any:
        """
        Make a request to the API
        :param endpoint: The endpoint of the API call (e.g ``getObjects``)
        :param data: The payload of the API call
        :param headers: The headers of the API call
        :param cache: Whether or not to cache the result API call in ``Anacreon.game_objects_cache``
        :return: 
        """
        if data is None:
            data = {}

        data["authToken"] = self.authtoken
        data["gameID"] = self.gameID
        data["sovereignID"] = self.sovID

        res = requests.post(self._endpoint(endpoint), json=data, headers=headers).json()

        return self._check_for_error(res, cache=cache)

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

    def get_obj_by_id(self, id: int, refresh: bool = False, cache: bool = True) -> Dict[str, Any]:
        """
        Get an object by its ID

        :param id: the ID of the object
        :param refresh: Whether or not to refresh the objects cache
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: The dictionary representing all the details of the object
        """

        if refresh:
            self.get_objects(cache=cache)

        for obj in self.game_objects_cache:
            if obj[u'id'] == id:
                return obj
        raise KeyError("An object with ID " + str(id) + " was not found")

    def get_obj_by_name(self, name: str, refresh: bool = False, cache: bool = True) -> Dict[str, Any]:
        """
        Get an object by its name

        :param name: the name of the object
        :param refresh: Whether or not to refresh the objects cache
        :param cache: Whether or not to cache the result in ``self.game_objects_cache``
        :return: The dictionary representing all the details of the object
        """
        if refresh:
            self.get_objects(cache=cache)

        for obj in self.game_objects_cache:
            try:
                if obj[u'name'] == name:
                    return obj
            except KeyError:  # It is better to ask for forgiveness than to ask for permission
                pass
        raise NameError("An object with the name " + str(name) + " was not found")

    def get_fleet_eta(self, fleetobj: Dict[str, Any], refresh: bool = False) -> float:
        if refresh:
            self.get_objects()

        lastpart = self.game_objects_cache[-1]
        updatebit = lastpart[u'update']
        try:
            return fleetobj[u'eta'] - updatebit
        except KeyError:
            return 0.0  # fleet has probably arrived

    def get_forces(self, resources: list) -> Tuple[float, float]:
        """

        :param resources:
        :return:
        """
        if self._sf_calc is None or self._gf_calc is None:
            self._generate_force_calculation_dict()
        currentID = None
        sf = 0.0
        gf = 0.0
        for i, x in enumerate(resources):
            if i % 2 == 0:
                currentID = x  # x is the id of the resource
            else:

                if currentID in self._sf_calc.keys():  # x is the count of the resource
                    sf += float(x) * self._sf_calc[currentID] / 100.0
                elif currentID in self._gf_calc.keys():
                    gf += float(x) * self._gf_calc[currentID] / 100.0
        return sf, gf

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
            for tradeRoute in worldobj['tradeRoutes']:
                exports = None
                imports = None
                if "return" in tradeRoute.keys():
                    # The data for this trade route belongs to another planet
                    partnerObj = self.get_obj_by_id(tradeRoute['partnerObjID'])
                    if partnerObj is not None:
                        for partnerTradeRoute in partnerObj['tradeRoutes']:
                            if partnerTradeRoute['partnerObjID'] == world_id:
                                if "exports" in partnerTradeRoute.keys():
                                    exports = partnerTradeRoute['exports']
                                if "imports" in partnerTradeRoute.keys():
                                    imports = partnerTradeRoute['imports']
                else:
                    if "exports" in tradeRoute.keys():
                        exports = tradeRoute['exports']
                    if "imports" in tradeRoute.keys():
                        imports = tradeRoute['imports']

                if exports is not None:
                    for j in range(0, len(exports), 4):
                        entry = get_entry(exports[j])
                        optimal = exports[j + 2]
                        actual = exports[j + 3]

                        if actual is None:

                            entry['exported'] += optimal
                        else:
                            entry['exported'] += actual

                        entry['exportedOptimal'] += optimal

                if imports is not None:
                    for j in range(0, len(imports), 4):
                        entry = get_entry(imports[j])
                        optimal = imports[j + 2]
                        actual = imports[j + 3]

                        if actual is None:

                            entry['exported'] += optimal
                        else:
                            entry['exported'] += actual

                        entry['importedOptimal'] += optimal

                if "resources" in worldobj.keys():
                    for i in range(0, len(worldobj['resources']), 2):
                        resID = worldobj['resources'][i]
                        count = worldobj['resources'][i + 1]

                        if count > 0:
                            result[resID] = get_entry(resID)
                            result[resID]['available'] = count

            return result

    def _check_for_error(self, res: Any, cache: bool = True) -> Any:
        """
        Check if the response from the API indicates that an error has occurred

        :param res: A parsed response from the API
        :param cache: If we  should cache the result if it's not an error
        :return: The result if it is not an error; otherwise, raise a `HexArcException`
        """
        if type(res) is not dict and type(res[0]) is str:
            raise HexArcException(res)
        else:
            if cache:
                cache = self.game_objects_cache
            else:
                cache = deepcopy(self.game_objects_cache)

            for item in res:
                try:
                    if item["class"] not in ("selection",):
                        cache[int(item["id"])] = item
                except KeyError:
                    pass  # Some objects in getObjects will not have an ID

            return cache

    def _generate_force_calculation_dict(self) -> None:
        """
        Generate the dictionaries required to calculate space and ground force of an object

        :return: None
        """
        for item in self.get_game_info()['scenarioInfo']:
            try:
                if item[u'category'] == 'fixedUnit' or item['category'] == 'orbitalUnit' or item[
                    "category"] == 'maneuveringUnit':
                    self._sf_calc[int(item['id'])] = float(item['attackValue'])
                elif item['category'] == 'groundUnit':
                    self._gf_calc[int(item['id'])] = float(item['attackValue'])
            except KeyError:
                # There are 3 or 4 items in the scenario info that do not have a category
                continue
