# Python A2S

Library to query Source and GoldSource servers. Rewrite of the
[python-valve](https://github.com/serverstf/python-valve) module.

Official demo application: [Sourcequery](https://sourcequery.yepoleb.at)

## Requirements

Python >=3.6, no external dependencies

## Install

`pip3 install python-a2s` or `python3 setup.py install`

## API

### Functions

* `a2s.info(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING)`
* `a2s.players(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING)`
* `a2s.rules(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING)`

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

## Examples

Example output shown may be shortened.

```py
>>> import a2s
>>> address = ("stomping.kinofnemu.net", 27015)
>>> a2s.info(address)
SourceInfo(protocol=17, server_name=" 24/7 Dustbowl :: Nemu's Stomping Ground", map_name='cp_dustbowl',
folder='tf', game='Team Fortress', app_id=440, player_count=31, max_players=33, bot_count=21,
server_type='d', platform='l', password_protected=True, vac_enabled=True, version='5579073',
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
```

## Tested Games

Half-Life 2, Half-Life, Team Fortress 2, Counter-Strike: Global Offensive, Counter-Strike 1.6, ARK: Survival Evolved, Rust

## License

MIT
