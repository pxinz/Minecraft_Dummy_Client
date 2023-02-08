# coding:utf-8
from io import BytesIO
from math import ceil


def _read(content: bytes | str | int | list[int] | tuple[int,] | BytesIO, step=1):
    if not isinstance(content, BytesIO):
        if isinstance(content, str):
            content = content.encode()
        elif isinstance(content, int):
            content = bytes([content])
        elif isinstance(content, list) or isinstance(content, tuple):
            content = bytes(content)
        content = BytesIO(content)
    while True:
        byte = content.read(step)
        if not byte:
            break
        step = (yield byte) or step
    content.close()
    yield False


def _read_int(content: bytes | str | int | list[int] | tuple[int,] | BytesIO):
    r = _read(content, 1)
    byte = r.send(None)
    while True:
        if not byte:
            break
        yield byte[0]
        byte = r.send(None)
    yield False


def to_binary(num: int) -> str:
    return bin(num).split("b")[1]


class ByteInt:
    _BYTE = 0XFF  # 0XFF -> 0B11111111 One byte, use (num & BYTE) to cut the last byte
    SIGN = 0X80  # 0x80 -> 0B10000000 use (num(last byte) & SIGN) get if num is a negative number
    BYTE = 1  # A byte(-128~127)
    SHORT = 2  # Two bytes(-32768~23767)
    INT = 4  # Four bytes(-2^31~2^31-1)
    LONG = 8  # Eight bytes(-2^63~2^63-1)

    @staticmethod
    def invert(binary: str) -> str:
        return binary.replace("1", "a").replace("0", "1").replace("a", "0")

    @staticmethod
    def bin2int(binary: str, length: int) -> int:
        if length * 8 == len(binary):
            # 因为头位0会被自动省略, 因此达到了byte长度*8的字符串必定是负数
            # 按位非 这里不能用py自带的
            binary = ByteInt.invert(binary[1:])
            return -int(binary, 2)
        else:
            # 正数
            return int(binary, 2)

    @staticmethod
    def int2bin(integer: int, length: int) -> str:
        binary = to_binary(abs(integer))
        if integer >= 0:
            return binary
        else:
            return "1" * (length * 8 - len(binary)) + ByteInt.invert(binary)

    @staticmethod
    def read_byte_int(num) -> int:
        _num = _read_int(num)
        value = 0
        current = _num.send(None)
        while current:
            value <<= 8
            value |= current
            current = _num.send(None)
        return ByteInt.bin2int(to_binary(value), len(num))

    @staticmethod
    def read_byte_int_from_stream(num: BytesIO, length: int) -> int:
        return ByteInt.read_byte_int(num.read(length))

    @staticmethod
    def write_byte_int(num: int, length: int = None) -> bytes:
        num = int(ByteInt.int2bin(num, (length if length else ceil((len(to_binary(num)) + 1) / 8))), 2)
        byte = []
        while num:
            byte.insert(0, num & ByteInt._BYTE)
            num >>= 8
        if length:
            while len(byte) < length:
                byte.insert(0, 0)
        return bytes(byte)

    @staticmethod
    def write_byte_int2stream(num: int, io: BytesIO, length: int = None) -> bytes:
        byte = ByteInt.write_byte_int(num, length)
        io.write(byte)
        return byte


class UnsignedByteInt:
    _BYTE = 0XFF  # 0XFF -> 0B11111111 One byte, use (num & BYTE) to cut the last byte
    UNSIGNED_BYTE = 1  # A byte(0~255)
    UNSIGNED_SHORT = 2  # Two bytes(0~65535)

    @staticmethod
    def read_unsigned_byte_int(num) -> int:
        _num = _read_int(num)
        value = 0
        current = _num.send(None)
        while current:
            value <<= 8
            value |= current
            current = _num.send(None)
        return value

    @staticmethod
    def read_unsigned_byte_int_from_stream(num: BytesIO, length: int) -> int:
        return UnsignedByteInt.read_unsigned_byte_int(num.read(length))

    @staticmethod
    def write_unsigned_byte_int(num: int, length: int = None) -> bytes:
        byte = []
        while num:
            byte.insert(0, num & UnsignedByteInt._BYTE)
            num >>= 8
        if length:
            while len(byte) < length:
                byte.insert(0, 0)
        return bytes(byte)

    @staticmethod
    def write_unsigned_byte_int2stream(num: int, io: BytesIO, length: int = None) -> bytes:
        byte = UnsignedByteInt.write_unsigned_byte_int(num, length)
        io.write(byte)
        return byte


class LEB128:
    CONTINUE = 0X80  # 0X80 -> 0B10000000 The sign of leb128
    CONTENT = 0X7F  # 0X7F -> 0B01111111 The content of one byte in leb128

    @staticmethod
    def read_leb128(num) -> int:
        num = _read_int(num)
        value = 0
        offset = 0
        b = LEB128.CONTINUE
        while b and b & LEB128.CONTINUE:
            b = num.send(None)
            value |= (b & LEB128.CONTENT) << offset
            offset += 7
        return value

    @staticmethod
    def read_leb128_from_stream(stream: BytesIO) -> int:
        value = 0
        offset = 0
        b = LEB128.CONTINUE
        while b and b & LEB128.CONTINUE:
            b = stream.read(1)[0]
            value |= (b & LEB128.CONTENT) << offset
            offset += 7
        return value

    @staticmethod
    def write_leb128(num) -> bytes:
        # 唉这个转换真的难受 跟似了码一样
        if num == 0:
            return b"\x00"
        byte = []
        while num > LEB128.CONTINUE:
            byte.append(num & LEB128.CONTENT | LEB128.CONTINUE)
            num >>= 7
        if num:
            byte.append(num)
        return bytes(byte)

    @staticmethod
    def write_leb128_2stream(num, io: BytesIO) -> bytes:
        byte = LEB128.write_leb128(num)
        io.write(byte)
        return byte


class String:
    @staticmethod
    def read_string(string) -> str:
        return String.read_string_from_stream(BytesIO(string))

    @staticmethod
    def read_string_from_stream(string: BytesIO) -> str:
        length = LEB128.read_leb128_from_stream(string)
        value = string.read(length).decode()
        string.close()
        return value

    @staticmethod
    def write_string(string) -> bytes:
        return LEB128.write_leb128(len(string)) + string.encode()

    @staticmethod
    def write_string2stream(string, io: BytesIO) -> bytes:
        byte = String.write_string(string)
        io.write(byte)
        return byte
