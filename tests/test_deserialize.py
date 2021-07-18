import json
from typing import Any, List
import unittest
from anacreonlib.types import response_datatypes
from pathlib import Path
from collections import Counter
from pprint import pformat

current_file_path = Path(__file__).resolve().parent / "getObjects_2020_07_18.json"


class DeserializationTest(unittest.TestCase):
    def test_get_objects_load(self):
        with open(current_file_path, "r") as f:
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
        self.assertEqual(counter[response_datatypes.OwnedWorld], 379)
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
            self.assertEqual({**before, **after}, after)


if __name__ == "__main__":
    unittest.main()
