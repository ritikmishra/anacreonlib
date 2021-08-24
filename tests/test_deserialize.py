import json
from typing import Any, List, TypedDict
import unittest
from anacreonlib.types import response_datatypes
from pathlib import Path
from collections import Counter
from pprint import pformat

current_folder_path = Path(__file__).resolve().parent


class DeserializationTest(unittest.TestCase):
    def test_get_objects_load(self) -> None:
        class GetObjectTestCase(TypedDict):
            file_path: Path
            expected_owned_world_count: int

        paths = (
            GetObjectTestCase(
                file_path=current_folder_path / "getObjects_2020_07_18.json",
                expected_owned_world_count=379,
            ),
            GetObjectTestCase(
                file_path=current_folder_path / "getObjects_2020_08_22.json",
                expected_owned_world_count=782,
            ),
        )

        for case in paths:
            with self.subTest(f"test load of {case!r}"):
                self.check_get_objects_load_is_correct(**case)

    def check_get_objects_load_is_correct(
        self, file_path: Path, expected_owned_world_count: int
    ) -> None:
        with open(file_path, "r") as f:
            get_objects_json_response: List[Any] = json.load(f)

        deserialized_objects: List[response_datatypes.AnacreonObject] = [
            response_datatypes._convert_json_to_anacreon_obj(
                response_datatypes.AnacreonObject, obj
            )
            for obj in get_objects_json_response
        ]
        # All objects should be deserialized
        self.assertEqual(len(get_objects_json_response), len(deserialized_objects))

        # Count the types of objects we deserialised
        counter = Counter(map(type, deserialized_objects))

        # When I made the getObjects call, my empire had 379 worlds
        self.assertEqual(
            counter[response_datatypes.OwnedWorld], expected_owned_world_count
        )
        self.assertEqual(counter[response_datatypes.OwnSovereign], 1)

        # All of the objects should have been deserialized successfully
        # i.e none should still be in raw json format
        self.assertEqual(
            counter[dict],
            0,
            msg=f"""
Encountered a `dict` that did not get deserialized into pydantic
{pformat(v) if (v := next((v for v in deserialized_objects if isinstance(v, dict)), None)) else "wait actually no something is really gone wrong"}
""",
        )
        self.assertEqual(counter[list], 0)

        reserialized_json: List[Any] = [
            json.loads(obj.json(by_alias=True)) for obj in deserialized_objects
        ]
        self.assertEqual(len(get_objects_json_response), len(reserialized_json))

        for before, after in zip(get_objects_json_response, reserialized_json):
            # Check that `after` is a superset of `before`
            # Only a shallow check that all keys in before are in after - does not verify that such information was actually kept
            self.assertEqual(
                {**before, **after},
                after,
                msg=f"""
before: 
{pformat(before)}

------

after:
{pformat(after)}

------

keys in before that are not in after:
{pformat(before.keys() - after.keys())}
                """
            )

    def test_aeon_ip_integer(self) -> None:
        raw = {
            "fleets": ["AEON2011:ipInteger:v1", "KzFQSQUAAAABOYqakg=="],
            "population": 10,
            "resources": [
                ["AEON2011:ipInteger:v1", "KzFQSQUAAAABOYqakg=="],
                ["AEON2011:ipInteger:v1", "KzFQSQUAAAABOYqakg=="],
            ],
            "techLevel": 9,
            "worlds": 10,
        }

        parsed = response_datatypes.SovereignStats.parse_obj(raw)

        self.assertEqual(5260352146, parsed.fleets)
        self.assertEqual([5260352146, 5260352146], parsed.resources)

    def test_owned_world_deserialization(self) -> None:
        # given: an API response from the player playing as the below sovereign id
        sov_id = 3913334
        with open(current_folder_path / "getObjects_2020_08_22.json", "r") as f:
            raw = json.load(f)

        # when: we parse all of the objects
        parsed_objects: List[response_datatypes.AnacreonObject] = [
            response_datatypes._convert_json_to_anacreon_obj(
                response_datatypes.AnacreonObject, obj
            )
            for obj in raw
        ]

        # then: all of the ones with class: world should be a world object, and
        # none of the ones without class: world should be a world object
        world_indexes = set(
            i for i, obj in enumerate(raw) if obj.get("class", None) == "world"
        )
        for i, obj in enumerate(parsed_objects):
            if i in world_indexes:
                self.assertIsInstance(obj, response_datatypes.World)
            else:
                self.assertNotIsInstance(obj, response_datatypes.World)

        # when: we look at all of the world objects
        worlds = [w for w in parsed_objects if isinstance(w, response_datatypes.World)]

        # then: it should only be an owned world iff we actually own it
        for world in worlds:
            with self.subTest(f"test world id {world.id}"):
                if world.sovereign_id == sov_id:
                    self.assertIsInstance(world, response_datatypes.OwnedWorld)
                else:
                    self.assertNotIsInstance(world, response_datatypes.OwnedWorld)


if __name__ == "__main__":
    unittest.main()
