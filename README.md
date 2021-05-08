# anacreonlib

This **unofficial** library provides a Python interface to the API of [Anacreon 3](https://anacreon.kronosaur.com), which is an online [4X](https://en.wikipedia.org/wiki/4X) game produced by [Kronosaur Productions, LLC.](http://kronosaur.com/).

## Usage


### Authentication (version 1.0)

```python
from anacreonlib import Anacreon

api = Anacreon("Username", "Password")
api.gameID = GAME_ID
api.sovID = SOV_ID
```

You can find `GAME_ID` by looking at the URL when you play Anacreon in your browser.  
For example, when I play on my Era 4 Alpha empire, the url is `http://anacreon.kronosaur.com/trantor.hexm?gameID=4365595`. Therefore, the 
game ID for the Era 4 Alpha is `4365595`

Your `SOV_ID` is equal to 

```
api.sovID = api.get_game_info()['userInfo']['sovereignID']
```

Personally, I run this once and write down the result somewhere

### Getting all objects in the game

```python
objects = api.get_objects()
```

After this call, `objects` will be a `dict`, where the key is the ID of the object, and the value is a `dict` which 
contains data specific to that object, such as resources contained in the object, which sovereign owns the object, etc. More information can be found on the wiki. 


## Rate Limits

The API has rate limits which are detailed in [this Ministry record](https://ministry.kronosaur.com/record.hexm?id=79981). Beware that they apply to both any scripts you write AND the online client.
