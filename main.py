import simpy
import random
from collections import deque
import heapq
import matplotlib.pyplot as plt
import logging
from copy import deepcopy

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class Task:
    def __init__(self, time, func, name, *args):
        if not callable(func):
            raise ValueError(f"{func} must be a callable function, not a {type(func)}")
        self.time = time
        self.func = func
        self.name = name
        self.args = args

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
            print(f"At time {self.env.now}s: Task Name: {task.name}, Function: {task.func}")
            if self.env.now < task_time:
                yield self.env.timeout(task_time - self.env.now)

            task.func(*task.args)


class Client:
    def __init__(self, env, network, acks, scheduler, num_paths, path_characteristics, packet_size=1500, initial_window_size=1):
        self.env = env
        self.network = network
        self.acks = acks
        self.scheduler = scheduler
        self.path_characteristics = deepcopy(path_characteristics)  # 수정된 부분
        self.unacked_packets = [deque() for _ in range(num_paths)]

        self.packet_size = packet_size
        self.packet_number = 0
        self.window_sizes = [initial_window_size] * num_paths
        self.inflight_packets = [0] * num_paths
        self.window_size_logs = [[] for _ in range(num_paths)]
        self.window_size_drops = [0] * num_paths
        self.last_congestion_time = [0] * num_paths
        self.sent_time_logs = [[] for _ in range(num_paths)]
        self.ack_time_logs = [[] for _ in range(num_paths)]

    def send_packet(self, path_index):
        self.packet_number += 1
        data = (self.packet_number, 'This is packet %d' % self.packet_number, path_index)
        self.unacked_packets[path_index].append(data)
        self.start_ack_timer(path_index, data)
        task = Task(self.env.now, self.network.send, "Send Packet", data)
        self.scheduler.add_task(task.time, task)

    def start_ack_timer(self, path_index, data):
        timeout = 1.0  # Set your timeout value here
        task = Task(self.env.now + timeout, self.resend_packet, "Resend Packet", path_index, data)
        self.scheduler.add_task(task.time, task)

    def resend_packet(self, path_index, data):
        if data in self.unacked_packets[path_index]:
            self.inflight_packets[path_index] += 1
            self.send_packet(path_index)

    def send(self, path_index):
        for _ in range(int(self.window_sizes[path_index])):
            self.send_packet(path_index)
        self.sent_time_logs[path_index].append(self.env.now)

    def receive_ack(self, ack):
        print(f"At time {self.env.now}s: ACK of packet {ack[0]} arrived using path {ack[2]}")
        self.ack_time_logs[ack[2]].append(self.env.now)
        if ack in self.unacked_packets[ack[2]]:
            self.unacked_packets[ack[2]].remove(ack)

    def retransmit_unacked_packets(self):
        for path_index in range(num_paths):
            for packet in list(self.unacked_packets[path_index]):
                print(f"Retransmitting packet {packet[0]} on path {packet[2]}")
                self.send_packet(packet[2])
                self.unacked_packets[path_index].remove(packet)

    def receive_ack_and_send(self):
        while True:
            ack = yield self.acks.get()
            self.receive_ack(ack)
            self.inflight_packets[ack[2]] -= 1

            if random.random() < self.path_characteristics[ack[2]][2]:  # packet loss
                self.last_congestion_time[ack[2]] = self.env.now
                self.window_sizes[ack[2]] /= 2
                if ack in self.unacked_packets[ack[2]]:
                    self.unacked_packets[ack[2]].remove(ack)
                    self.resend_packet(ack[2], ack)
            else:
                self.window_sizes[ack[2]] += 1
            self.window_size_logs[ack[2]].append((self.env.now, self.window_sizes[ack[2]]))

            available_slots = int(self.window_sizes[ack[2]]) - self.inflight_packets[ack[2]]
            if available_slots > 0:
                self.send_packet(ack[2])
                self.inflight_packets[ack[2]] += 1

            # 변경: 부분 실행 및 가비지 컬렉션
            if len(self.window_size_logs[ack[2]]) > 50000:  # 조건에 따라 임의 설정
                # window_size_logs가 특정 크기 이상이면 처음부터 일부분을 제거
                self.window_size_logs[ack[2]] = self.window_size_logs[ack[2]][10000:]

    def start_sending(self):
        for i in range(num_paths):
            self.send(i)

        env.process(self.receive_ack_and_send())

class Network:
    def __init__(self, env, server, path_characteristics, scheduler):
        self.env = env
        self.server = server
        self.path_characteristics = deepcopy(path_characteristics)  # 수정된 부분
        self.num_paths = len(path_characteristics)
        self.incoming_queues = [simpy.Store(env) for _ in range(self.num_paths)]
        self.packet_queues = [deque() for _ in range(self.num_paths)]
        self.is_transmitting = [False for _ in range(self.num_paths)]
        self.scheduler = scheduler
        self.transmitted_packets = [0] * self.num_paths  # 각 path로 전송된 패킷 수를 저장하기 위한 리스트를 추가합니다.

    def send(self, data):
        path_index = data[2]
        bandwidth, _, _ = self.path_characteristics[path_index]
        packet_size = 1500  # bits
        max_packets_in_bandwidth = bandwidth // packet_size

        # 현재 path로 전송된 패킷의 수가 bandwidth를 초과하지 않는 경우에만 packet_queue에 추가합니다.
        if self.transmitted_packets[path_index] < max_packets_in_bandwidth:
            self.packet_queues[path_index].append(data)
            self.transmitted_packets[path_index] += 1
        if not self.is_transmitting[path_index]:
            task = Task(self.env.now, self._path_run, "Start Path Run", path_index)
            self.scheduler.add_task(task.time, task)

    def _path_run(self, path_index):
        self.is_transmitting[path_index] = True
        bandwidth, latency, error_rate = self.path_characteristics[path_index]
        packet_size = 1500  # bits
        max_packets_in_bandwidth = bandwidth // packet_size
        try:
            # packet_queue가 비어있지 않고, 현재 path로 전송된 패킷의 수가 bandwidth를 초과하지 않는 동안 패킷을 전송합니다.
            while self.packet_queues[path_index] and self.transmitted_packets[path_index] <= max_packets_in_bandwidth:
                data = self.packet_queues[path_index].popleft()
                transmission_time = packet_size / bandwidth
                if random.random() > error_rate:
                    self.env.process(self._send_packet_to_server(data, path_index, transmission_time, latency))
                # 패킷이 전송되면 해당 path로 전송된 패킷의 수를 감소시킵니다.
                self.transmitted_packets[path_index] -= 1
        finally:
            self.is_transmitting[path_index] = False

    def _send_packet_to_server(self, data, path_index, transmission_time, latency):
        yield self.env.timeout(transmission_time + latency)
        task1 = Task(self.env.now, self.server.receive, "Server Receives Packet", data)
        self.scheduler.add_task(task1.time, task1)


class Server:
    def __init__(self, env, acks, path_characteristics, scheduler):
        self.env = env
        self.received_data = []
        self.acks = acks
        self.path_characteristics = deepcopy(path_characteristics)  # 수정된 부분
        self.scheduler = scheduler
        self.ack_queues = [deque() for _ in range(len(path_characteristics))]
        self.is_sending_ack = [False for _ in range(len(path_characteristics))]
        self.packet_arrival_times = {}

    def receive(self, data):
        self.received_data.append(data)
        if data[2] in [0, 1, 2]:
            print(f"At time {self.env.now}s: received packet number: {data[0]} on path {data[2]}")
        ack = (data[0], 'ACK for packet %d' % data[0], data[2])
        self.ack_queues[data[2]].append(ack)
        if not self.is_sending_ack[data[2]]:
            task = Task(self.env.now, self.send_ack, "Send ACK", data[2])
            self.scheduler.add_task(task.time, task)

    def send_ack(self, path_index):
        self.is_sending_ack[path_index] = True
        while self.ack_queues[path_index]:
            ack = self.ack_queues[path_index].popleft()
            bandwidth, latency, error_rate = self.path_characteristics[path_index]
            packet_size = 1500  # bytes
            transmission_delay = packet_size / bandwidth

            if random.random() > error_rate:
                task2 = Task(self.env.now + transmission_delay + latency, self.acks.put, "Client Receives ACK",
                             ack)
                self.scheduler.add_task(task2.time, task2)

        self.is_sending_ack[path_index] = False


env = simpy.Environment()
scheduler = Scheduler(env)

num_paths = 3
path_characteristics = [(10000, 1, 0.001), (100000, 1, 0.001), (10000, 1 , 0.1)]
acks = simpy.Store(env)
server = Server(env, acks, path_characteristics, scheduler)
network = Network(env, server, path_characteristics, scheduler)
client = Client(env, network, acks, scheduler, num_paths=num_paths, path_characteristics=path_characteristics)
client.start_sending()

env.process(client.receive_ack_and_send())

scheduler_process = env.process(scheduler.schedule())

# Modify this part of the code
env.run(until=30)

for path_index in range(num_paths):
    # Plot window size
    times, window_sizes = zip(*client.window_size_logs[path_index])
    plt.plot(times, window_sizes, label=f'Path {path_index + 1}')

plt.title('Congestion Window Size Over Time')
plt.xlabel('Time (s)')
plt.ylabel('Window Size')
plt.legend()
plt.show()

# Throughput and RTT calculation
total_throughput = 0
total_rtt = 0
for path_index in range(num_paths):
    # Calculate throughput (total received packets / total time)
    throughput = len(client.ack_time_logs[path_index]) / client.ack_time_logs[path_index][-1]
    total_throughput += throughput
    print(f"Path {path_index + 1} throughput: {throughput}")

    # Calculate RTT (average of (ack_time - sent_time))
    rtt = sum(ack_time - sent_time for sent_time, ack_time in zip(client.sent_time_logs[path_index], client.ack_time_logs[path_index])) / len(client.ack_time_logs[path_index])
    total_rtt += rtt
    print(f"Path {path_index + 1} average RTT: {rtt}")

# Print total throughput and average RTT
print(f"Total throughput: {total_throughput}")
print(f"Average RTT: {total_rtt / num_paths}")

#print(f"Server received data: {server.received_data}")
