"""This is an example script that takes up to 10 pre-existing explorer fleets,
and sends them around the map. Fleets are only sent to worlds that have not been
visited before. This script could be used to explore the galaxy + remove fog of 
war, but more efficient implementations are possible.
"""
from typing import Set
from anacreonlib import Anacreon, Fleet, World
from anacreonlib.utils import dist
import asyncio


async def explorer_fleet_manager(
    client: Anacreon, fleet_id: int, visited_world_ids: Set[int]
) -> None:
    if (anchor_obj_id := client.space_objects[fleet_id].anchor_obj_id) is not None:
        visited_world_ids.add(anchor_obj_id)

    def dist_to_world(world: World) -> float:
        this_fleet = client.space_objects[fleet_id]
        return dist(this_fleet.pos, world.pos)

    while True:
        # Step 1: find which world we should go to next
        world_ids_i_could_go_to = (
            world
            for world_id, world in client.space_objects.items()
            if isinstance(world, World) and world_id not in visited_world_ids
        )

        try:
            next_world_to_go_to = min(world_ids_i_could_go_to, key=dist_to_world)
        except ValueError:  # Thrown when `world_ids_i_could_go_to` is empty
            print(f"Fleet {fleet_id}: done going to planets")
            return  # exit

        # Step 2: go to that world
        print(
            f"Fleet {fleet_id}: going to planet ID {next_world_to_go_to.id} (name: {next_world_to_go_to.name})"
        )
        visited_world_ids.add(next_world_to_go_to.id)

        await client.set_fleet_destination(fleet_id, next_world_to_go_to.id)

        # Wait to arrive at that world
        while True:
            await client.wait_for_get_objects()
            fleet = client.space_objects[fleet_id]
            if fleet.eta is None:
                break
            else:
                print(f"Fleet {fleet_id}: still waiting to arrive at planet")


async def main() -> None:
    print("Logging in")
    # Replace `username` and `password` with real values
    client = await Anacreon.log_in("8JNJ7FNZ", "username", "password")
    print("Logged in!")
    watch_refresh_task = client.call_get_objects_periodically()

    explorer_fleets = [
        fleet_id
        for fleet_id, fleet in client.space_objects.items()
        if isinstance(fleet, Fleet)
        and fleet.ftl_type == "explorer"
        and fleet.sovereign_id == client.sov_id
    ]

    visited_world_ids = set()

    explorer_fleet_tasks = [
        asyncio.create_task(explorer_fleet_manager(client, fleet_id, visited_world_ids))
        for fleet_id in explorer_fleets
    ]

    print("Spawned fleet managers, waiting for completion")
    for task in explorer_fleet_tasks:
        await task

    watch_refresh_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())

