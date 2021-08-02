Writing your first script with ``anacreonlib``
================================================================================

This tutorial will guide you through creating your first script with 
``anacreonlib``. This script will use all preexisting explorer fleets to visit
every planet visible to you in the galaxy (taking into account planets that are
newly discovered during script execution).

At a high level, the steps we will want our script to do are

1. Log into anacreon (obviously)
2. Find all of our preexisting explorer fleets
3. For each fleet,

   a. Find the next planet it should go to

   b. Go to that planet

   c. Add this planet to the set of planets visited 

   d. Wait for the fleet to get to the planet in the game

-----

First, we need to set up our :py:class:`~anacreonlib.Anacreon` instance. Import 
it, and use the :py:func:`~anacreonlib.Anacreon.log_in` class method inside a
``main`` coroutine.

We will also need to import :py:mod:`asyncio` to run our ``main`` coroutine.

.. code-block:: python

    from anacreonlib import Anacreon
    import asyncio

    async def main():
        ## Step 1: Log into anacreon
        print("Logging in")
        # Replace `username` and `password` with real values
        client = await Anacreon.log_in("8JNJ7FNZ", "username", "password")
        print("Logged in!")

        ## Now what?


    if __name__ == "__main__":
        asyncio.run(main())


Next, we will need to find all of our existing explorer fleets. All space 
objects in the game (i.e all of the :py:class:`~anacreonlib.World` and 
:py:class:`~anacreonlib.Fleet` objects that are in the game), are 
stored in the dict 
:py:attr:`client.space_objects <anacreonlib.Anacreon.space_objects>`. 
Each world and fleet has a :py:attr:`~anacreonlib.Fleet.sovereign_id` attribute indicating 
who the owner is, which we can compare to :py:attr:`~Anacreon.sov_id`, which is
our own sovereign ID. Additionally, each :py:class:`~anacreonlib.Fleet` has a 
:py:attr:`~anacreonlib.Fleet.ftl_type` attribute indicating whether the fleet is ``jump``, 
``warp``, or ``explorer``. 


.. code-block:: python

    explorer_fleets = [
        fleet_id
        for fleet_id, fleet in client.space_objects.items()
        if isinstance(fleet, Fleet)
        and fleet.ftl_type == "explorer"
        and fleet.sovereign_id == client.sov_id
    ]

Great! Now we have a list of all of our explorer fleets. Next, we will need some
kind of function that manages an individual fleet which finds the next planet to
go to, sends the fleet to that planet, and waits for it to arrive.


For simplicity, we will choose the nearest planet to the fleet that has not been
visited before. To do this we will need

- A key function to pass to :py:func:`min` that computes the distance between
  a given world and the fleet
- A list of worlds we have not visited

.. code-block:: python

    from typing import Set
    from anacreonlib.utils import dist

    async def explorer_fleet_manager(
        client: Anacreon, fleet_id: int, visited_world_ids: Set[int]
    ) -> None:
        def dist_to_world(world: World) -> float:
            """Distance between world and current position of fleet"""
            this_fleet = client.space_objects[fleet_id]
            return dist(this_fleet.pos, world.pos)

        while True:
            ## Step 3a: find which world we should go to next
            world_ids_i_could_go_to = [
                world
                for world_id, world in client.space_objects.items()
                if isinstance(world, World) and world_id not in visited_world_ids
            ]

            try:
                next_world_to_go_to = min(world_ids_i_could_go_to, key=dist_to_world)
            except ValueError:  # Thrown when `world_ids_i_could_go_to` is empty
                print(f"Fleet {fleet_id}: done going to planets")
                return  # exit

            # TODO: go to the world
            # TODO: wait to arrive at the world


Next, we need to send the fleet to the world. This is a simple call to 
:py:func:`client.set_fleet_destination <anacreonlib.Anacreon.set_fleet_destination>`.

.. code-block:: python
    :emphasize-lines: 24-29

    async def explorer_fleet_manager(
        client: Anacreon, fleet_id: int, visited_world_ids: Set[int]
    ) -> None:
        def dist_to_world(world: World) -> float:
            """Distance between world and current position of fleet"""
            this_fleet = client.space_objects[fleet_id]
            return dist(this_fleet.pos, world.pos)

        while True:
            ## Step 3a: find which world we should go to next
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


            ## Step 3b: go to that world
            print(
                f"Fleet {fleet_id}: going to planet ID {next_world_to_go_to.id} (name: {next_world_to_go_to.name})"
            )
            visited_world_ids.add(next_world_to_go_to.id)
            await client.set_fleet_destination(fleet_id, next_world_to_go_to.id)


            # TODO: wait to arrive at the world

After sending the fleet, we need to wait for our fleet to arrive at the planet. 
An easy way to do this is to just repeatedly check 
:py:attr:`client.space_objects <anacreonlib.Anacreon.space_objects>` to see
whether or not the fleet :py:attr:`eta <anacreonlib.Anacreon.space_objects>` has
gone away, which will happen once the fleet reaches its destination.


.. code-block:: python
    :emphasize-lines: 31-38

    async def explorer_fleet_manager(
        client: Anacreon, fleet_id: int, visited_world_ids: Set[int]
    ) -> None:
        def dist_to_world(world: World) -> float:
            """Distance between world and current position of fleet"""
            this_fleet = client.space_objects[fleet_id]
            return dist(this_fleet.pos, world.pos)

        while True:
            ## Step 3a: find which world we should go to next
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


            ## Step 3b: go to that world
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

As written, our ``explorer_fleet_manager`` will first send fleets to the planet 
that they are currently stationed on, and then wait around a minute for the
fleet to get there. It would be smarter to check to see if the fleet being 
managed is sitting at a world, and to mark that world as visited.

Let's do that.

.. code-block:: python
    :emphasize-lines: 4-5

    async def explorer_fleet_manager(
        client: Anacreon, fleet_id: int, visited_world_ids: Set[int]
    ) -> None:
        if (anchor_obj_id := client.space_objects[fleet_id].anchor_obj_id) is not None:
            visited_world_ids.add(anchor_obj_id)

        def dist_to_world(world: World) -> float:
            """Distance between world and current position of fleet"""
            this_fleet = client.space_objects[fleet_id]
            return dist(this_fleet.pos, world.pos)

        ...



Finally, in our main function, we need to call :py:func:`asyncio.create_task`
to create a fleet manager for each of our fleets

.. literalinclude:: ../../examples/visit_all_planets.py
   :language: python
   :pyobject: main
   :emphasize-lines: 16-27


Now, our script is complete!


----

Below is the complete code for the example

.. literalinclude:: ../../examples/visit_all_planets.py
   :language: python
   :linenos: