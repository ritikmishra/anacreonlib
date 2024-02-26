import base64
import json
from functools import cached_property
from typing import Tuple, Any
import typing

from pydantic import ConfigDict, BaseModel, validator, PlainSerializer, BeforeValidator


def _snake_case_to_lower_camel(snake: str) -> str:
    """Converts a string that is in `snake_case_form` to `lowerCamelCase`, but special-casing the string "ID"."""

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
    """Convert some value to a Hexarc ``ipInteger`` if appropriate

    The conversion is only done when
    - The parameter ``o`` is a :py:class:`int`
    - The value of ``o`` cannot fit into a 32-bit signed integer

    Args:
        o (Any): Any value

    Returns:
        Any: The value of ``o``, unless it was an int that did not fit into 32
        bits, in which case it is converted to an ``ipInteger``, which is a list of
        the form ``["AEON2011:ipInteger:v1", "KzFQSQQAAACDIVYA"]``
    """
    if isinstance(o, int) and (abs(o) > (2**31 - 1)):
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
    """Convert a Hexarc ``ipInteger`` of the form
    ``["AEON2011:ipInteger:v1", "KzFQSQQAAACDIVYA"]`` into a numeric value

    Encoding a very large number (on the order of billions) in JSON can be
    sketchy because all numbers in JSON are technically 64-bit floating point
    numbers, so after a certain point, not all integers can be represented.

    To solve this problem, Hexarc (the platform on which the Anacreon API runs)
    will encode numbers that cannot fit in a 32 bit signed integer (i.e the
    number has a magnitude beyond 2^31) in a special format. In the JSON, this
    comes across as a 2-element tuple: the first element is a sentinel value to
    check that the JSON list is representing a large number, and the second
    element is the actual encoded number.

    This validator decodes any numbers the Anacreon API encoded in order to
    avoid overflow, and converts them to a python `int`, which should not
    normally overflow.

    Args:
        v (Any): Any value returned by the Anacreon API

    Returns:
        Any: If ``v`` was a Hexarc ``ipInteger``, then the decoded integer value
        is returned. Otherwise, ``v`` is returned.
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


#: Helper to convert large integers from/into the AEON IP integer format.
LargeInt = typing.Annotated[
    int,
    PlainSerializer(_convert_int_to_aeon_ipinteger, when_used="json-unless-none"),
    BeforeValidator(_convert_aeon_ipinteger_to_int),
]


class DeserializableDataclass(BaseModel, metaclass=type):
    # TODO[pydantic]: The following keys were removed: `json_dumps`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        alias_generator=_snake_case_to_lower_camel,
        ignored_types=(cached_property, set),
    )
