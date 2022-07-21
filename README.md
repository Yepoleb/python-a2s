# Python A2S

Library to query Source and GoldSource servers.
Implements [Valve's Server Query Protocol](https://developer.valvesoftware.com/wiki/Server_queries).
Rewrite of the [python-valve](https://github.com/serverstf/python-valve) module.
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
>>> address = ('46.251.238.245', 27037)
>>> a2s.info(address)
SourceInfo(protocol=17, server_name='PVP-Official-Fjordur-ARKpocalypse12 - (v348.2)', map_name='Fjordur', folder='ark_survival_evolved', game='ARK: Survival Evolved', app_id=0, player_count=70, max_players=70, bot_count=0, server_type='d', platform='w', password_protected=False, vac_enabled=True, version='1.0.0.0', edf=177, port=7799, steam_id=90161518848227331, stv_port=None, stv_name=None, keywords=',OWNINGID:90161518848227331,OWNINGNAME:90161518848227331,NUMOPENPUBCONN:8,P2PADDR:90161518848227331,P2PPORT:7799,LEGACY_i:0', game_id=346110, ping=0.25)
>>> a2s.players(address)
[Player(index=0, name='GammaBreinek', score=0, duration=28108.4375), Player(index=0, name='123', score=0, duration=28099.265625), Player(index=0, name='', score=0, duration=26686.79296875), Player(index=0, name='reckper', score=0, duration=26636.46484375), Player(index=0, name='', score=0, duration=26489.970703125), ... , Player(index=0, name='Babidjon', score=0, duration=86.51565551757812)]
>>> a2s.rules(address)
{'ALLOWDOWNLOADCHARS_i': '1', 'ALLOWDOWNLOADITEMS_i': '1', 'ClusterId_s': 'PCArkpocalypse', 'CUSTOMSERVERNAME_s': 'pvp-official-fjordur-arkpocalypse12', 'DayTime_s': '140', 'GameMode_s': 'TestGameMode_C', 'HASACTIVEMODS_i': '0', 'LEGACY_i': '0', 'MATCHTIMEOUT_f': '120.000000', 'ModId_l': '0', 'Networking_i': '0', 'NUMOPENPUBCONN': '8', 'OFFICIALSERVER_i': '1', 'OWNINGID': '90161518848227331', 'OWNINGNAME': '90161518848227331', 'P2PADDR': '90161518848227331', 'P2PPORT': '7799', 'SEARCHKEYWORDS_s': 'Custom', 'ServerPassword_b': 'false', 'SERVERUSESBATTLEYE_b': 'true', 'SESSIONFLAGS': '1707', 'SESSIONISPVE_i': '0'}
```

## Notes

* Some servers return inconsistent or garbage data. Filtering this out is left to the specific application, because there is no general approach to filtering that makes sense for all use cases. In most scenarios, it makes sense to at least remove players with empty names. Also the `player_count` value in the info query and the actual number of players returned in the player query do not always match up.

* For some games, the query port is different from the actual connection port. The Steam server browser will show the connection port and querying that will not return an answer. There does not seem to be a general solution to this problem so far, but usually probing port numbers up to 10 higher and lower than the connection port usually leads to a response. There's also the option of using `http://api.steampowered.com/ISteamApps/GetServersAtAddress/v0001?addr={IP}` to get a list of game servers on an IP (thanks to Nereg for this suggestion). If you're still not successful, use a network sniffer like Wireshark to monitor outgoing packets while refreshing the server popup in Steam.

* Player counts above 255 do not work and there's no way to make them work. This is a limitation in the specification of the protocol.

* This library does not implement rate limiting. It's up to the application to limit the number of requests per second to an acceptable amount to not trigger any firewall rules.

## Tested Games

Half-Life 2, Half-Life, Team Fortress 2, Counter-Strike: Global Offensive, Counter-Strike 1.6, ARK: Survival Evolved, Rust

## License

MIT
