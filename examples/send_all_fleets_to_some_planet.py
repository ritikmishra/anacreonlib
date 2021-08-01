from anacreonlib import Anacreon, Fleet
import asyncio

async def main():
    ## Step 1: Log in
    client: Anacreon = await Anacreon.log_in(
        game_id="8JNJ7FNZ", 
        username="username",
        password="password"
    )

    ## Step 2: do cool stuff, automatically!
    # find all of our fleets
    all_my_fleets = [
        fleet 
        for fleet in client.space_objects.values()
        if isinstance(fleet, Fleet)
        and fleet.sovereign_id == client.sov_id
    ]

    # send all our fleets to world ID 100
    for fleet in all_my_fleets:
        await client.set_fleet_destination(fleet.id, 100)

if __name__ == "__main__":
    asyncio.run(main())
