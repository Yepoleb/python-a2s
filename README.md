# Python A2S

Library to query Source and GoldSource servers.
Implements [Valve's Server Query Protocol](https://developer.valvesoftware.com/wiki/Server_queries).
Rewrite of the [python-valve](https://github.com/serverstf/python-valve) module.
Supports both synchronous and asyncronous applications.

Official demo application: [Sourcequery](https://sourcequery.yepoleb.at)

## Requirements

Python >=3.9, no external dependencies

## Install

`pip3 install python-a2s` or `python3 setup.py install`

## API

### Functions

* `a2s.info(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING)`
* `a2s.players(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING)`
* `a2s.rules(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING)`

All functions also have an async version as of package 1.2.0 that adds an `a` prefix, e.g.
`ainfo`, `aplayers`, `arules`.

### Parameters

* address: `Tuple[str, int]` - Address of the server.
* timeout: `float` - Timeout in seconds. Default: 3.0
* encoding: `str` or `None` - String encoding, None disables string decoding. Default: utf-8

### Return Values

* info: SourceInfo or GoldSrcInfo. They are documented in the
  [source file](a2s/info.py).
* players: List of Player items. Also documented in the corresponding
  [source file](a2s/players.py).
* rules: Dictionary of key - value pairs.

### Exceptions

* `a2s.BrokenMessageError(Exception)` - General decoding error
* `a2s.BufferExhaustedError(BrokenMessageError)` - Response too short
* `socket.timeout` - No response (synchronous calls)
* `asyncio.exceptions.TimeoutError` - No response (async calls)
* `socket.gaierror` - Address resolution error
* `ConnectionRefusedError` - Target port closed
* `OSError` - Various networking errors like routing failure

## Examples

Example output shown may be shortened. Also the server shown in the example may be down by the time you see this.

```py
>>> import a2s
>>> address = ("chi-1.us.uncletopia.com", 27015)
>>> a2s.info(address)
SourceInfo(protocol=17, server_name='Uncletopia | Chicago | 1', map_name='pl_badwater',
folder='tf', game='Team Fortress', app_id=440, player_count=24, max_players=24, bot_count=0,
server_type='d', platform='l', password_protected=False, vac_enabled=True, version='7370160',
edf=241, port=27015, steam_id=85568392924469984, stv_port=27016,
stv_name='Uncletopia | Chicago | 1 | STV', keywords='nocrits,nodmgspread,payload,uncletopia',
game_id=440, ping=0.2339219159912318)

>>> a2s.players(address)
[Player(index=0, name='AmNot', score=22, duration=8371.4072265625),
Player(index=0, name='TAAAAANK!', score=15, duration=6251.03173828125),
Player(index=0, name='Tiny Baby Man', score=17, duration=6229.0361328125)]

>>> a2s.rules(address)
{'coop': '0', 'cronjobs_version': '2.0', 'crontab_version': '2.0', 'deathmatch': '1',
'decalfrequency': '10', 'discord_accelerator_version': '1.0', 'discord_version': '1.0',
'extendedmapconfig_version': '1.1.1', 'metamod_version': '1.11.0-dev+1145V', 'mp_allowNPCs': '1'}
```

## Notes

* Some servers return inconsistent or garbage data. Filtering this out is left to the specific application, because there is no general approach to filtering that makes sense for all use cases. In most scenarios, it makes sense to at least remove players with empty names. Also the `player_count` value in the info query and the actual number of players returned in the player query do not always match up. Sometimes the player query returns an empty list of players.

* For some games, the query port is different from the actual connection port. The Steam server browser will show the connection port and querying that will not return an answer. There does not seem to be a general solution to this problem so far, but usually probing port numbers up to 10 higher and lower than the connection port usually leads to a response. There's also the option of using `http://api.steampowered.com/ISteamApps/GetServersAtAddress/v0001?addr={IP}` to get a list of game servers on an IP (thanks to Nereg for this suggestion). If you're still not successful, use a network sniffer like Wireshark to monitor outgoing packets while refreshing the server popup in Steam.

* Player counts above 255 do not work and there's no way to make them work. This is a limitation in the specification of the protocol.

* This library does not implement rate limiting. It's up to the application to limit the number of requests per second to an acceptable amount to not trigger any firewall rules.

## Tested Games

Half-Life 2, Half-Life, Team Fortress 2, Counter-Strike: Global Offensive, Counter-Strike 1.6, ARK: Survival Evolved, Rust

## Similar Projects

* [dayzquery](https://github.com/Yepoleb/dayzquery) - Module for decoding DayZ rules responses
* [l4d2query](https://github.com/Yepoleb/l4d2query) - Module for querying additional data from L4D2 servers

## License

MIT
