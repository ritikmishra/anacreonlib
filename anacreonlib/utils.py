"""Utility function to help with decode information from the Anacreon API

Where possible, function signatures have been ordered with partial application 
(see :py:func:`functools.partial`) in mind.
"""

import math
from typing import (
    List,
    Dict,
    Optional,
    Sequence,
    TypeVar,
    Union,
    Tuple,
    cast,
)

from anacreonlib.types.response_datatypes import World, Trait
from anacreonlib.types.scenario_info_datatypes import ScenarioInfoElement
from anacreonlib.types.type_hints import Location

T = TypeVar("T")
U = TypeVar("U")


def flat_list_to_tuples(lst: Sequence[T]) -> List[Tuple[T, T]]:
    """Turn a flat list of alternating key-value pairs into a list of tuples

    Example:
        A common use case of this function is to iterate over a ``resources`` list

        >>> resources = [130, 500, 159, 15000]
        >>> for res_id, res_qty in utils.flat_list_to_tuples(resources):
        ...     print(f"We have {res_qty} of resource id {res_id}")
        ...
        We have 500 of resource id 130
        We have 15000 of resource id 159

    Args:
        lst (Sequence[T]): A flat sequence of alternating key-value pairs

    Returns:
        List[Tuple[T, T]]: A list of key-value tuples
    """
    return list(zip(lst[::2], lst[1::2]))


def flat_list_to_n_tuples(n: int, lst: List[T]) -> List[Tuple[T, ...]]:
    """Converts a list ``[1,2,3,4,5,6,...]`` into a list of tuples ``[(1,2,3), (4,5,6), ...]``
    where the length of each tuple is specified by the parameter ``n``

    Example:
        One use case of this function is to handle import data

        >>> imports = [130, 100, 5700, None, 260, 100, 6400, 500]
        >>> for res_id, pct, optimal, actual in flat_list_to_n_tuples(4, imports):
        ...     print(f"Imported {actual or optimal} units of resource id {res_id} (optimal: {optimal})")
        ...
        Imported 5700 units of resource id 130 (optimal: 5700)
        Imported 500 units of resource id 260 (optimal: 6400)

    Args:
        n (int): The length of each tuple in the returned list
        lst (List[T]): A flat list of all of the items

    Returns:
        List[Tuple[T, ...]]: A list of tuples, where each item in the original list appears exactly once.
    """
    zip_args = [lst[i::n] for i in range(n)]
    return list(zip(*zip_args))


def dist(pointA: Location, pointB: Location) -> float:
    """Retuns the distance between 2 points

    Example:

        >>> pointA = (0, 0)
        >>> pointB = (3, 4)
        >>> utils.dist(pointA, pointB)
        5.0

    Args:
        pointA (Location): An ``(x, y)`` coordinate pair
        pointB (Location): An ``(x, y)`` coordinate pair

    Returns:
        float: The distance between the two points
    """
    ax, ay = pointA
    bx, by = pointB

    dx = bx - ax
    dy = by - ay

    return math.sqrt(dx * dx + dy * dy)


def world_has_trait(
    scninfo: List[ScenarioInfoElement],
    world: World,
    target_trait_id: int,
    include_world_characteristics: bool = True,
) -> bool:
    """Checks whether a world has a given trait, or a child trait extends the
    given trait

    Args:
        scninfo (List[ScenarioInfoElement]): The scenario info for the game.
        world (World): The world to check
        target_trait_id (int): The trait to check the presence of
        include_world_characteristics (bool, optional): Whether or not we should
            take intrinsic world characteristics (e.g world type, designation)
            into account. Defaults to True.

    Returns:
        bool: Whether or not the planet has the given trait.
    """
    trait_dict = world.squashed_trait_dict

    trait_id: int
    for trait_id in trait_dict.keys():
        if target_trait_id == trait_id:
            return True
        elif trait_inherits_from_trait(scninfo, trait_id, target_trait_id):
            return True

    if include_world_characteristics:
        characteristic_traits = (world.world_class, world.designation, world.culture)
        characteristic_inherits_from_target = any(
            trait_inherits_from_trait(scninfo, characteristic, target_trait_id)
            for characteristic in characteristic_traits
        )

        if (
            target_trait_id in characteristic_traits
            or characteristic_inherits_from_target
        ):
            return True

    return False


def trait_inherits_from_trait(
    scninfo: List[ScenarioInfoElement],
    child_trait: Union[Trait, int],
    parent_trait: Union[Trait, int],
) -> bool:
    """Check if a trait inherits from another trait

    Traits can extend other traits. For example, the trait for having abundant
    chronimium deposits, ID ``50``, inherits from the trait for having any
    chronimium deposits, ID ``56``. A world that has trait ID ``50`` also has trait ID
    ``56``. However, this is only implied by the inheritance hierarchy of traits --
    the world object as returned by the API does would only give the "most
    specific" trait. In this case, it would only `explicitly` say the world has
    trait ID ``50``. This function can be used to figure out that the world also has
    trait ID ``56`` as a result.

    Args:
        scninfo (List[ScenarioInfoElement]): The scenario info
        child_trait (Union[Trait, int]): The 'more advanced/specific' trait
            (e.g the trait id for abundant chronimium deposits)
        parent_trait (Union[Trait, int]): The 'less advanced/specific' trait
            (e.g the trait id for chronimium deposits)

    Raises:
        LookupError: Raised if the child trait ID could not be found in the
        scenario info

    Returns:
        bool: ``True`` if the child trait supplants the parent trait, like how a
            sealed arcology supplants a domed city. ``False`` otherwise.
    """
    try:
        # looks up up trait in scenario info based on id. information from Trait object is not used.
        childs_parent_list = next(
            trait.inherit_from for trait in scninfo if trait.id == child_trait
        )
        if childs_parent_list is None:
            return False

        return parent_trait in childs_parent_list or any(
            trait_inherits_from_trait(scninfo, trait, parent_trait)
            for trait in childs_parent_list
        )
    except StopIteration as e:
        raise LookupError("child trait was not found in scenario info") from e
    except KeyError:
        return False


def trait_under_construction(
    squashed_trait_dict: Dict[int, Union[int, Trait]], trait_id: int
) -> bool:
    """Check whether a world is still building a trait

    Args:
        squashed_trait_dict (Dict[int, Union[int, Trait]]): A dict mapping from
            trait ID to either the trait ID or trait object. This can be
            obtained from
            :func:`anacreonlib.types.response_datatypes.World.squashed_trait_dict`

        trait_id (int): The ID of the trait to check for

    Returns:
        bool: ``True`` if the world has the trait, and it is still building.
        ``False`` if the world has fully built the trait, or if it does not have
        the trait at all.
    """
    if trait_id not in squashed_trait_dict.keys():
        return False  # world doesn't have it at all
    trait = squashed_trait_dict[trait_id]
    if isinstance(trait, int):
        return False  # its a simple structure, world has it, and its built
    if trait.build_complete is not None:
        return True

    return False


def world_has_fully_built_trait(
    scninfo: List[ScenarioInfoElement], world: World, target_trait_id: int
) -> bool:
    """Check that a world has fully built a trait to completion.

    This function is aware of the trait inheritance hierarchy. So, for example,
    we would consider a planet that has a sealed arcology (trait ID ``218``) to have
    'fully built' a domed city (trait ID ``88``), because a sealed arcology upgrades
    a domed city.

    Args:
        scninfo (List[ScenarioInfoElement]): The scenario info for the game
        world (World): The world to check for
        target_trait_id (int): The trait ID to check for

    Returns:
        bool: ``True`` if the world has the specified trait, or a successor to
        the specified trait. ``False`` otherwise.
    """
    return world_has_trait(
        scninfo, world, target_trait_id, True
    ) and not trait_under_construction(world.squashed_trait_dict, target_trait_id)


def does_trait_depend_on_trait(
    scninfo: List[ScenarioInfoElement],
    trait_a: int,
    trait_b: int,
) -> bool:
    """Check if a ``trait_b`` has another ``trait_a`` anywhere in the chain of
    requirements.

    For example, a sealed arcology (trait ID 218) is an upgrade to a domed city
    (trait id 88). So, the call
    ``utils.does_trait_depend_on_trait(scninfo, 218, 88)`` would return ``True``
    because trait ID 218 needs trait ID 88 to be built first.

    Note that there can be multiple upgrade paths to a more advanced
    trait/improvement. For example, the the sealed arcology ruins (ID 219) are
    also a predecessor to the sealed arcology (ID 218).

    Args:
        scninfo (List[ScenarioInfoElement]): The scenario info
        trait_a (int): The ID of the 'more advanced' trait
        trait_b (int): The ID of the 'less advanced' trait

    Returns:
        bool: Whether ``trait_a`` needs ``trait_b`` to be built first.
    """
    more_advanced_improvement = scninfo[trait_a]
    if more_advanced_improvement.build_upgrade is not None:
        return trait_b in more_advanced_improvement.build_upgrade or any(
            does_trait_depend_on_trait(scninfo, trait, trait_b)
            for trait in more_advanced_improvement.build_upgrade
        )
    return False


def get_world_primary_industry_products(world: World) -> Optional[List[int]]:
    """Get the list of resource IDs that a planet produces with its primary
    industry

    Args:
        world (World): The world in question

    Returns:
        Optional[List[int]]: A list of resource IDs that the planet's
        designation produces. If this is ``None``, then the planet's designation
        does not produce items (e.g it may be a foundation world, or autonomous)
    """
    primary_industry = next(
        (
            trait
            for trait in world.traits
            if isinstance(trait, Trait) and trait.is_primary
        ),
        None,
    )

    if primary_industry is None or primary_industry.production_data is None:
        return None

    return [
        cast(int, res_id)
        for res_id, pct_alloc, cannot_build in flat_list_to_n_tuples(
            3, primary_industry.build_data
        )
    ]
