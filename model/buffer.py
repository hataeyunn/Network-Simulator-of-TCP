from model import packet
from util import watcher
class Buffer:
    def __init__(self, _max_size: int) -> None:
        self.queue = watcher.CallbackList([], callback=watcher.CallbackList.my_callback)
        self.max_size = _max_size

    def put(self, _data: packet.Packet) -> None:
        if len(self.queue) <= self.max_size:
            self.queue.append(_data)
        else:
            pass
#sequence 넘버로 정렬
    def get(self) -> packet.Packet:
        result = self.queue[0]
        del self.queue[0]
        return result

    def get_first(self) -> packet.Packet:
        return self.queue[0]

    def print_queue(self, _arg: str = "") -> None:
        result = []
        if _arg == "":
            print(self.queue)
        else:
            print([i.header[_arg] for i in self.queue])

    
class InflightBuffer(Buffer):
    def __init__(self, max_size: int) -> None:
        super().__init__(max_size)

    def remove_received_ack(self, _received : packet.Packet)->None:
        for i in self.queue:
            if i.header['squence_num'] == _received.header['sequence_num'] and _received.header['is_ack'] == True:
                self.queue.remove(i)

class ReceiveBuffer(Buffer):
    def __init__(self, _max_size: int) -> None:
        super().__init__(_max_size)