"""
MIT License

Copyright (c) 2020 Gabriel Huber

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Type, Union, overload

if TYPE_CHECKING:
    from .a2s_sync import A2SStream
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
