# anacreonlib

This **unofficial** library provides a Python interface to the API of [Anacreon 3](https://anacreon.kronosaur.com), which is an online [4X](https://en.wikipedia.org/wiki/4X) game produced by [Kronosaur Productions, LLC.](http://kronosaur.com/).

## Usage

### Authentication (version 2.0)

Below is a minimum working example to get authenticated with the Anacreon API

```python
from anacreonlib.types.scenario_info_datatypes import ScenarioInfo
from anacreonlib.types.response_datatypes import AuthenticationResponse
from anacreonlib.types.request_datatypes import (
    AnacreonApiRequest,
    AuthenticationRequest,
)
from anacreonlib.anacreon_async_client import AnacreonAsyncClient
from pprint import pprint
import asyncio


async def main():
    # you can find the game_id of the current game by looking at the url
    # when you're playing anacreon in the browser
    game_id = "8JNJ7FNZ"

    # Step 1: obtain auth token
    client: AnacreonAsyncClient = AnacreonAsyncClient()
    response: AuthenticationResponse = await client.authenticate_user(
        AuthenticationRequest(username="your_username", password="your_password")
    )

    auth_token = response.auth_token

    # Step 2: obtain sovereign id (this never changes)
    game_info: ScenarioInfo = await client.get_game_info(auth_token, game_id)
    sov_id = game_info.user_info.sovereign_id

    # Step 3: Make API requests
    objects = await client.get_objects(
        AnacreonApiRequest(
            auth_token=auth_token, game_id="8JNJ7FNZ", sovereign_id=sov_id
        )
    )

    # Step 4: use API request results
    pprint(objects[0].dict())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

```

## Rate Limits

The API has rate limits which are detailed in [this Ministry record](https://ministry.kronosaur.com/record.hexm?id=79981). Beware that they apply to both any scripts you write AND the online client.
