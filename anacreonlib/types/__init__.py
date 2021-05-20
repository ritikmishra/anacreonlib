import base64
import json
from functools import cached_property
from typing import Tuple, Any

from pydantic import BaseModel, validator


def _snake_case_to_lower_camel(snake: str) -> str:
    """Converts a string that is in `snake_case_form` to `lowerCamelCase`"""

    def ensure_correct_case(pair: Tuple[int, str]) -> str:
        i, word = pair
        if i == 0:
            return word.lower()
        elif word.lower() == "id":
            return word.upper()
        else:
            return word.capitalize()

    camel_words = map(ensure_correct_case, enumerate(snake.split("_")))
    return "".join(camel_words)


_AEON_IP_INTEGER_SENTINEL_VALUE = "AEON2011:ipInteger:v1"
_AEON_IP_INT_POSITIVE = b"IP1+"
_AEON_IP_INT_NEGATIVE = b"IP1-"


def _convert_int_to_aeon_ipinteger(o: Any) -> Any:
    """
    Convert an integer to the Hexarc representation for an integer with magnitude greater than 2^31 ONLY IF
    - the parameter `o` is an integer
    - the value of `o` is bigger than 2**31

    :param o: anything
    :return: o, unless it was an int bigger than 2^31. then, a list of the form
    `["AEON2011:ipInteger:v1", "KzFQSQQAAACDIVYA"]` where `KzFQSQQAAACDIVYA` is the Hexarc representation for a large
    number
    """
    if isinstance(o, int) and (abs(o) > (2 ** 31 - 1)):
        is_pos = int(o >= 0)
        try:
            num_bytes = abs(o).to_bytes(6, byteorder="big")
        except OverflowError:
            num_bytes = abs(o).to_bytes(1023, byteorder="big")

        size_bytes = (1024).to_bytes(2, byteorder="big")
        sign_bytes = _AEON_IP_INT_POSITIVE if is_pos else _AEON_IP_INT_NEGATIVE

        num_together = sign_bytes[::-1] + size_bytes + num_bytes
        encoded_num = base64.b64encode(num_together)
        return [_AEON_IP_INTEGER_SENTINEL_VALUE, encoded_num]

    return o

def _convert_aeon_ipinteger_to_int(v: Any) -> Any:
    """
    Encoding a very large number (on the order of billions) in JSON can be sketchy because all numbers in JSON
    are technically 64-bit floating point numbers, so after a certain point, not all integers can be represented.

    To solve this problem, Hexarc (the platform on which the Anacreon API runs) will encode numbers that cannot
    fit in a 32 bit signed integer (i.e the number has a magnitude beyond 2^31) in a special format. In the JSON,
    this comes across as a 2-element tuple: the first element is a sentinel value to check that the JSON list is
    representing a large number, and the second element is the actual encoded number.

    This validator decodes any numbers the Anacreon API encoded in order to avoid overflow, and converts them to a
    python `int`, which should not normally overflow.

    :param v: Any arbitrary object, list, string, etc
    :return: If `v` was an encoded integer, the decoded integer value is returned. Otherwise, the original value is
    returned.
    """
    if (
            isinstance(v, list)
            and len(v) == 2
            and v[0] == _AEON_IP_INTEGER_SENTINEL_VALUE
            and isinstance(v[1], str)
    ):
        b64_encoded_num: bytes = bytes(v[1], encoding="utf-8")

        # num still has aux data
        encoded_num: bytes = base64.b64decode(b64_encoded_num)

        # decode sign
        encoded_sign: bytes = encoded_num[0:4][::-1]
        sign: int
        if encoded_sign == _AEON_IP_INT_POSITIVE:
            sign = 1
        elif encoded_sign == _AEON_IP_INT_NEGATIVE:
            sign = -1
        else:
            return v

        # bytes [4:6] are the size of the int, we don't care about that in python
        # bytes [6:] are the actual bytes of the integer

        decoded_num: int = int.from_bytes(
            encoded_num[6:], byteorder="big", signed=False
        )
        return decoded_num * sign

    return v

def _dumps_convert_large_ints_to_aeon_ipinteger(item, **kwargs):
    """Behaves like json.dumps, but all large numbers greater than 2^31 are converted to the Hexarc
    representation of a large number"""

    def convert_big_nums_to_json(el):
        if isinstance(el, list) or isinstance(el, tuple):
            return list(map(convert_big_nums_to_json, el))  # tuples would get serialized as list anyways
        elif isinstance(el, dict):
            for thingy_key in el.keys():
                el[thingy_key] = convert_big_nums_to_json(el[thingy_key])
            return el

        return _convert_int_to_aeon_ipinteger(el)

    convert_big_nums_to_json(item)
    return json.dumps(item, **kwargs)


class DeserializableDataclass(BaseModel, metaclass=type):
    class Config:
        alias_generator = _snake_case_to_lower_camel
        keep_untouched = (cached_property, set)
        json_dumps = _dumps_convert_large_ints_to_aeon_ipinteger

    @validator("*", pre=True)
    def convert_aeon_ipinteger_to_python_int(cls, v):
        return _convert_aeon_ipinteger_to_int(v)

    @validator("*", pre=True)
    def handle_large_ints_in_lists(cls, v):
        if isinstance(v, list):
            ret = map(_convert_aeon_ipinteger_to_int, v)
            return list(ret)
        return v
