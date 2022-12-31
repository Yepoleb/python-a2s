from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Type, Union, overload

from .a2s_sync import A2SStream

if TYPE_CHECKING:
    from .info import GoldSrcInfo, InfoProtocol, SourceInfo
    from .players import Player, PlayersProtocol
    from .rules import RulesProtocol

@overload
def request_sync(
    address: Tuple[str, int], timeout: float, encoding: str, a2s_proto: Type[InfoProtocol]
) -> Union[SourceInfo, GoldSrcInfo]: ...
@overload
def request_sync(
    address: Tuple[str, int], timeout: float, encoding: str, a2s_proto: Type[PlayersProtocol]
) -> List[Player]: ...
@overload
def request_sync(
    address: Tuple[str, int], timeout: float, encoding: str, a2s_proto: Type[RulesProtocol]
) -> Dict[str, str]: ...
@overload
def request_sync_impl(
    conn: A2SStream,
    encoding: str,
    a2s_proto: Type[InfoProtocol],
    challenge: int = ...,
    retries: int = ...,
    ping: Optional[float] = ...,
) -> Union[SourceInfo, GoldSrcInfo]: ...
@overload
def request_sync_impl(
    conn: A2SStream,
    encoding: str,
    a2s_proto: Type[PlayersProtocol],
    challenge: int = ...,
    retries: int = ...,
    ping: Optional[float] = ...,
) -> List[Player]: ...
@overload
def request_sync_impl(
    conn: A2SStream,
    encoding: str,
    a2s_proto: Type[RulesProtocol],
    challenge: int = ...,
    retries: int = ...,
    ping: Optional[float] = ...,
) -> Dict[str, str]: ...
