import io

from a2s.exceptions import BrokenMessageError
from a2s.defaults import default_encoding, default_timeout
from a2s.a2sstream import request
from a2s.byteio import ByteReader



A2S_RULES_RESPONSE = 0x45
A2S_CHALLENGE_RESPONSE = 0x41

class RulesResponse:
    def __init__(self, rule_count, rules):
        self.rule_count = rule_count
        self.rules = rules

def rules(address, challenge=0, timeout=default_timeout):
    resp_data = request(
        address, b"\x56" + challenge.to_bytes(4, "little"), timeout)
    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=default_encoding)

    # A2S_RESPONSE misteriously seems to add a FF FF FF FF
    # long to the beginning of the response which isn't
    # mentioned on the wiki.
    #
    # Behaviour witnessed with TF2 server 94.23.226.200:2045
    # As of 2015-11-22, Quake Live servers on steam do not
    # Source: valve-python messages.py
    if reader.peek(4) == b"\xFF\xFF\xFF\xFF":
        reader.read(4)

    response_type = reader.read_uint8()
    if response_type == A2S_CHALLENGE_RESPONSE:
        challenge = reader.read_int32()
        return rules(address, challenge, timeout)

    if response_type != A2S_RULES_RESPONSE:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    rule_count = reader.read_int16()
    resp = RulesResponse(
        rule_count=rule_count,
        rules={
            reader.read_cstring(): reader.read_cstring()
            for rule_num in range(rule_count)
        }
    )

    return resp

