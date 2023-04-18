import bisect
from model import packet, node


class Event:
    def __init__(self, _packet: packet.Packet, _node: node.Node) -> None:
        self.packet = _packet
        self.node = _node


class Scheduler:
    def __init__(self) -> None:
        self.queue = []

    def insert_event(self, _event: Event, _time: float) -> None:
        new_event = (_time, _event)

        # 이진 검색을 사용하여 이벤트를 정렬된 위치에 추가
        index = bisect.bisect_left(self.queue, new_event)
        self.queue.insert(index, new_event)

    def get_next_event(self) -> Event:
        result = self.queue[0]
        del self.queue[0]
        return result


# scheduler = Scheduler()

# scheduler.insert_event(Event(1, 1), 50)
# scheduler.insert_event(Event(1, 2), 10)

# print(scheduler.get_next_event())
# print(scheduler.get_next_event())
