from typing import Tuple

from pydantic import BaseModel

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


class DeserializableDataclass(BaseModel, metaclass=type):
    class Config:
        alias_generator = _snake_case_to_lower_camel
