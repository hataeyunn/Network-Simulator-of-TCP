from packet import Packet


class Buffer:
    def __init__(self, _max_size: int) -> None:
        self.queue = []
        self.max_size = _max_size

    def put(self, _data: Packet) -> None:
        if len(self.queue) <= self.max_size:
            self.queue.append(_data)
        else:
            pass
#sequence 넘버로 정렬
    def get(self) -> Packet:
        result = self.queue[0]
        del self.queue[0]
        return result

    def get_first(self) -> Packet:
        return self.queue[0]렬

    def print_queue(self, _arg: str = "") -> None:
        result = []
        if _arg == "":
            print(self.queue)
        else:
            for packet in self.queue:
                result.append(packet.header[_arg])
            print(result)


class InflightBuffer(Buffer):
    def __init__(self, max_size: int) -> None:
        super().__init__(max_size)


class ReceiveBuffer(Buffer):
    def __init__(self, _max_size: int) -> None:
        super().__init__(_max_size)


a = Buffer(5000)
for i in range(0, 1000):
    b1 = Packet(
        _destination_ip="localhost",
        _destination_port=5000,
        _source_ip="localhost",
        _source_port=5000,
        _squence_num=3,
        _protocol="TCP",
    )
    b2 = Packet(
        _destination_ip="localhost",
        _destination_port=5000,
        _source_ip="localhost",
        _source_port=5000,
        _squence_num=1,
        _protocol="TCP",
    )
    b3 = Packet(
        _destination_ip="localhost",
        _destination_port=5000,
        _source_ip="localhost",
        _source_port=5000,
        _squence_num=4,
        _protocol="TCP",
    )

a.put(b1)
a.put(b2)
a.put(b3)


a.print_queue("squence_num")
