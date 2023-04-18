import threading
from model import buffer


class Node:
    def __init__(self, _index: int, _des_index: int, _path: list, _type: str) -> None:
        self.index = _index
        self.des_index = _des_index
        self._path = _path
        if _type is "client" or _type is "server":
            self.type = _type
        self.cwnd = 1

        self.send_buffer = buffer.InflightBuffer
        self.receive_buffer = buffer.ReceiveBuffer

        self.send_th = threading.Thread(target=self.send_packet)
        self.receive_th = threading.Thread(target=self.receive_packet)

        self.send_th.start()
        self.receive_th.start()

    def receive_packet(self) -> None:
        while True:
            print("received")

    def send_packet(self) -> None:
        while True:
            print("send")
