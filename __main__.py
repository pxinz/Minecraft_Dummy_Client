import socket

from packs import *
from encoding import *
import base64

if __name__ == '__main__':
    import json

    print("Minecraft服务器信息查询工具")
    ip, port, version = input("IP: "), int(input("Port: ")), int(
        input("版本协议号(详见https://wiki.vg/Protocol_version_numbers): "))
    print("\n查询中, 请稍等...\n")
    soc = socket.socket()
    soc.connect((ip, port))
    soc.send(hand_shaking(version, ip, port, ConnectTypes.STATUS))
    soc.send(ask_status())
    status = json.loads(String.read_string(soc.recv(2048).split(b"\x00", 1)[1]))
    soc.close()
    with open("favicon.png", "wb") as f:
        f.write(base64.b64decode(status["favicon"].split("base64,", 1)[1]))
    print(
        "版本: {2[version][name]} 地址: {0}:{1} 在线: {2[players][online]}/{2[players][max]}\n"
        "在线成员: {3}\n"
        "简介:\n{2[description][text]}\n"
        "图标: 见favicon.png".format(
            ip, port, status, ", ".join([i["name"] for i in status["players"]["sample"]])))
