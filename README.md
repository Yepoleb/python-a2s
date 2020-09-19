# Python A2S

Library to query Source and GoldSource servers. Impliments [Valve's Server Query Protocol](https://developer.valvesoftware.com/wiki/Server_queries) Rewrite of the
[python-valve](https://github.com/serverstf/python-valve) module.
Supports both synchronous and asyncronous applications.

Official demo application: [Sourcequery](https://sourcequery.yepoleb.at)

## Requirements

Python >=3.7, no external dependencies

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
  [source file](a2s/players.py)
* rules: Dictionary of key - value pairs.

### Exceptions

* `a2s.BrokenMessageError(Exception)` - General decoding error
* `a2s.BufferExhaustedError(BrokenMessageError)` - Response too short
* `socket.timeout` - No response
* `socket.gaierror` - Address resolution error
* `concurrent.futures._base.TimeoutError`- No response async version
* `socket.gaierror: [Errno 11001] getaddrinfo failed` - Address resolution error async version
* `ConnectionRefusedError: [Errno 111] Connection refused` - Port is [closed](https://stackoverflow.com/questions/11585377/python-socket-error-errno-111-connection-refused) on destination machine. 

## Examples

Example output shown may be shortened.

```py
>>> import a2s
>>> address = ("stomping.kinofnemu.net", 27015)
>>> a2s.info(address)
SourceInfo(protocol=17, server_name=" 24/7 Dustbowl :: Nemu's Stomping Ground", map_name='cp_dustbowl',
folder='tf', game='Team Fortress', app_id=440, player_count=31, max_players=33, bot_count=21,
server_type='d', platform='l', password_protected=False, vac_enabled=True, version='5579073',
edf=177, port=27015, steam_id=85568392920040090, stv_port=None, stv_name=None,
keywords='brutus,celt,couch,cp,dustbowl,increased_maxplayers,nemu,nocrits,nodmgspread,pony,replays,vanilla',
game_id=440, ping=0.253798684978392)

>>> a2s.players(address)
[Player(index=0, name='Brutus', score=34, duration=836.4749145507812),
 Player(index=0, name='RageQuit', score=6, duration=1080.8099365234375),
 Player(index=0, name="Screamin' Eagles", score=1, duration=439.8598327636719)]

>>> a2s.rules(address)
{'coop': '0', 'deathmatch': '1', 'decalfrequency': '10', 'metamod_version': '1.10.7-devV',
 'mp_allowNPCs': '1', 'mp_autocrosshair': '1', 'mp_autoteambalance': '0', 'mp_disable_respawn_times': '0',
 'mp_fadetoblack': '0'}
>>> import asyncio
>>> asyncio.get_event_loop().run_until_complete(a2s.ainfo(address))
SourceInfo(protocol=17, server_name=" 24/7 Dustbowl :: Nemu's Stomping Ground", map_name='cp_dustbowl', folder='tf', game='Team Fortress', app_id=440, player_count=31, max_players=33, bot_count=24, server_type='d', platform='l', password_protected=False, vac_enabled=True, version='6064914', edf=177, port=27015, steam_id=85568392920040090, stv_port=None, stv_name=None, keywords='brutus,celt,couch,cp,dustbowl,increased_maxplayers,nemu,nocrits,nodmgspread,pony,replays,vanilla', game_id=440, ping=0.1720000000204891)
```

## Notes

* Some servers return inconsistent or garbage data. Filtering this out is left to the specific application, because there is no general approach to filtering that makes sense for all use cases. In most scenarios, it makes sense to at least remove players with empty names. Also the `player_count` value in the info query and the actual number of players returned in the player query do not always match up.

* For some games, the query port is different from the actual connection port. The Steam server browser will show the connection port and querying that will not return an answer. There does not seem to be a general solution to this problem so far, but usually probing port numbers up to 10 higher and lower than the connection port usually leads to a response. If you're still not successful, use a network sniffer like Wireshark to monitor outgoing packets while refreshing the server popup in Steam.

* Player counts above 255 do not work and there's no way to make them work. This is a limitation in the specification of the protocol.

## Tested Games

Half-Life 2, Half-Life, Team Fortress 2, Counter-Strike: Global Offensive, Counter-Strike 1.6, ARK: Survival Evolved, Rust

## License

MIT
