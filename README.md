# anacreonlib

This library provides a Python interface to the API of an online game called [Anacreon](https://anacreon.kronosaur.com), which is made by Kronosaur Productions, LLC.

## Usage


### Authentication

```python
from anacreonlib import Anacreon

api = Anacreon("Username", "Password")
api.gameID = GAME_ID
api.sovID = SOV_ID
```

You can find `GAME_ID` by looking at the URL when you play Anacreon in your browser.  
For example, when I play on my Era 4 Alpha empire, the url is `http://anacreon.kronosaur.com/trantor.hexm?gameID=4365595`. Therefore, the 
game ID for the Era 4 Alpha is `4365595`


You can find `SOV_ID` by inspecting the results of `api.get_game_info()` (which can be called without setting `SOV_ID`). Open the result up in a text editor, and `Ctrl+F` for your empire name. 
The ID in that same JSON object is your `SOV_ID`.

### Getting all objects in the game

```python
objects = api.getObjects()
```

After this call, `objects` will contain a `list` of `dict`s, where each `dict` contains data regarding a specific world. More information can be found on the wiki. 

