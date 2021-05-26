from typing import List, Tuple, TypeVar

T = TypeVar("T")


def flat_list_to_n_tuples(n: int, lst: List[T]) -> List[Tuple[T, ...]]:
    """Converts a list `[1,2,3,4,5,6,...]` into a list of tuples [(1,2,3), (4,5,6), ...]
    where the length of each tuple is specified by the parameter `n`

    Args:
        n (int): The length of each tuple in the returned list
        lst (List[T]): A flat list of all of the items

    Returns:
        List[Tuple[T, ...]]: A list of tuples, where each item in the original list appears exactly once.
    """
    zip_args = [lst[i::n] for i in range(n)]
    return list(zip(*zip_args))
