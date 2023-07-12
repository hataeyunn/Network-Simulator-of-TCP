import simpy
import random
from collections import deque
import heapq

class Task:
    def __init__(self, time, func):
        assert callable(func), "func must be a callable function, not a generator"
        self.time = time
        self.func = func

    def __lt__(self, other):
        return self.time < other.time


class Scheduler:
    def __init__(self, env):
        self.env = env
        self.priority_queue = []

    def add_task(self, task_time, task):
        heapq.heappush(self.priority_queue, (task_time, task))

    def schedule(self):
        while True:
            if not self.priority_queue:
                yield self.env.timeout(0.0001)
                continue

            task_time, task = heapq.heappop(self.priority_queue)
            if self.env.now < task_time:
                yield self.env.timeout(task_time - self.env.now)

            task.func()

class Client:
    def __init__(self, env, network, acks, scheduler, num_paths, packet_size=1500, initial_window_size=1):
        self.env = env
        self.network = network
        self.acks = acks
        self.scheduler = scheduler
        self.packet_size = packet_size
        self.packet_number = 0
        self.window_sizes = [initial_window_size] * num_paths

    def send(self, path_index):
        for _ in range(int(self.window_sizes[path_index])):
            self.packet_number += 1
            data = (self.packet_number, 'This is packet %d' % self.packet_number, path_index)
            print(f"At time {self.env.now}s: {data[0]} packet using path {path_index} ")

            task = Task(self.env.now, lambda: self.network.send(data))
            self.scheduler.add_task(task.time, task)

    def receive_ack_and_send(self):
        while True:
            ack = yield self.acks.get()
            # 혼잡창 크기 조정 알고리즘 구현
            if ack[0] % 10 == 0:
                self.window_sizes[ack[2]] /= 2  # 혼잡창을 절반으로 줄임
            else:
                self.window_sizes[ack[2]] += 1  # 혼잡창을 증가시킴

            # 혼잡 제어 창 크기만큼 패킷을 전송
            for _ in range(int(self.window_sizes[ack[2]])):
                self.packet_number += 1
                data = (self.packet_number, 'This is packet %d' % self.packet_number, ack[2])
                print(f"At time {self.env.now}s: {data[0]} packet using path {ack[2]} ")
                self.network.send(data)


class Network:
    def __init__(self, env, server, path_characteristics, scheduler):
        self.env = env
        self.server = server
        self.path_characteristics = path_characteristics
        self.num_paths = len(path_characteristics)
        self.incoming_queues = [simpy.Store(env) for _ in range(self.num_paths)]
        self.packet_queues = [deque() for _ in range(self.num_paths)]
        self.is_transmitting = [False for _ in range(self.num_paths)]
        self.scheduler = scheduler

    def send(self, data):
        path_index = data[2]
        self.packet_queues[path_index].append(data)
        if not self.is_transmitting[path_index]:
            task = Task(self.env.now, lambda: self._path_run(path_index))
            self.scheduler.add_task(task.time, task)

    def _path_run(self, path_index):
        self.is_transmitting[path_index] = True
        while self.packet_queues[path_index]:
            data = self.packet_queues[path_index].popleft()
            bandwidth, latency, error_rate = self.path_characteristics[path_index]
            packet_size = 1500  # bytes
            transmission_time = packet_size / bandwidth  # Calculate transmission time

            if random.random() > error_rate:  # If not error
                # 패킷이 도착하자마자 latency/2를 적용하고, 그 후에 패킷을 전송합니다.
                task1 = Task(self.env.now + latency, lambda: self.server.receive(data))
                self.scheduler.add_task(task1.time, task1)

        self.is_transmitting[path_index] = False

    def run(self):
        for i in range(self.num_paths):
            self.env.process(self._path_run(i))

class Server:
    def __init__(self, env, acks, path_characteristics,scheduler):
        self.env = env
        self.received_data = []
        self.acks = acks
        self.path_characteristics = path_characteristics
        self.scheduler = scheduler
        self.ack_queues = [deque() for _ in range(len(path_characteristics))]
        self.is_sending_ack = [False for _ in range(len(path_characteristics))]
        self.packet_arrival_times = {}  # To record the arrival times of packets

    def receive(self, data):
        self.received_data.append(data)
        if data[2] in [0, 1, 2]:
            print(f"At time {self.env.now}s: received packet number: {data[0]} on path {data[2]}")
        ack = (data[0], 'ACK for packet %d' % data[0], data[2])
        self.ack_queues[data[2]].append(ack)
        if not self.is_sending_ack[data[2]]:
            task = Task(self.env.now, lambda: self.send_ack(data[2]))
            self.scheduler.add_task(task.time, task)

    def send_ack(self, path_index):
        self.is_sending_ack[path_index] = True
        while self.ack_queues[path_index]:
            ack = self.ack_queues[path_index].popleft()
            bandwidth, latency, error_rate = self.path_characteristics[path_index]
            packet_size = 1500  # bytes
            transmission_delay = packet_size / bandwidth  # Fixed transmission delay

            if random.random() > error_rate:  # If not error
                task2 = Task(self.env.now + latency, lambda: self.acks.put(ack))
                self.scheduler.add_task(task2.time, task2)
                print(f"At time {self.env.now}s: ACK of packet {ack[0]} arrived using path {ack[2]}")

        self.is_sending_ack[path_index] = False


env = simpy.Environment()
scheduler = Scheduler(env)

num_paths = 3
path_characteristics = [(1000, 1, 0.01), (500, 2, 0.02), (2000, 0.5, 0.005)]  # (bandwidth, latency, error_rate) for each path
acks = simpy.Store(env)
server = Server(env, acks, path_characteristics, scheduler)
network = Network(env, server, path_characteristics, scheduler)
client = Client(env, network, acks, scheduler, num_paths=num_paths)

for i in range(num_paths):
    client.send(i)

scheduler.add_task(0, Task(0, client.receive_ack_and_send))
env.process(scheduler.schedule())
env.run(until=10)
