from encoding import *
from io import BytesIO
from enum import Enum
from time import time


# 统一包格式
def base_pack(id: int,
              content: bytes) -> bytes:
    # <Varint:PackLength><Varint:PackID><ByteArray:Content>
    pack = BytesIO()
    # PackID
    LEB128.write_leb128_2stream(id, pack)
    # Content
    pack.write(content)

    value = pack.getvalue()
    pack.close()
    return LEB128.write_leb128(len(value)) + value  # PackLength


class ConnectTypes(Enum):
    STATUS = b"\x01"
    LOGIN = b"\x02"


# 握手
def hand_shaking(version: int,  # 版本协议号, 详见	https://wiki.vg/Protocol_version_numbers
                 ip: str,
                 port: int,
                 connect_type: ConnectTypes) -> bytes:
    # <Varint:版本协议号><String:IP><UnsignedShort:Port><Varint:ConnectType>
    pack = BytesIO()
    # 版本协议号
    LEB128.write_leb128_2stream(version, pack)
    # IP
    String.write_string2stream(ip, pack)
    # Port
    UnsignedByteInt.write_unsigned_byte_int2stream(port, pack, UnsignedByteInt.UNSIGNED_SHORT)
    # ConnectType
    pack.write(connect_type.value)

    value = pack.getvalue()
    pack.close()
    return base_pack(0, value)


# 连接状态STATUS下的操作
def ask_status() -> bytes:
    return base_pack(0, b"")


def ping() -> bytes:
    return base_pack(1, ByteInt.write_byte_int(round(time() * 1000), ByteInt.LONG))
