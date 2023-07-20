import simpy
import random
from collections import deque
import heapq
import matplotlib.pyplot as plt
import logging
from copy import deepcopy
from tqdm import tqdm
import itertools

DEBUG = False
CLIENT = False
SERVER = False
CONGESTION = True

if DEBUG :
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
simtime = 100

class ProgressBar:
    def __init__(self, env, end_time):
        self.env = env
        self.end_time = end_time
        self.progress_bar = tqdm(total=self.end_time, ncols=70)

    def progress(self):
        while True:
            self.progress_bar.update(1)
            if self.env.now >= self.end_time:
                self.progress_bar.close()
                return
            yield self.env.timeout(1)
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
        self.task_counter = itertools.count()  # add this line

    def add_task(self, task_time, task):
        count = next(self.task_counter)  # increment task_counter
        heapq.heappush(self.priority_queue, (task_time, count, task))  # add count to the tuple

    def schedule(self):
        while True:
            if not self.priority_queue:
                yield self.env.timeout(0.0001)
                continue

            task_time, _, task = heapq.heappop(self.priority_queue)  # change this line
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
        self.logger = logging.getLogger(self.__class__.__name__)
        self.packet_size = packet_size
        self.packet_number = 0
        self.window_sizes = [initial_window_size] * num_paths
        self.inflight_packets = [0] * num_paths
        self.window_size_logs = [[] for _ in range(num_paths)]
        self.window_size_drops = [0] * num_paths
        self.last_congestion_time = [0] * num_paths
        self.sent_time_logs = [[] for _ in range(num_paths)]
        self.ack_time_logs = [[] for _ in range(num_paths)]

        self.rtt_estimations = [0] * num_paths
        self.alpha = 0.125  # Parameter for RTT estimation
        self.resend_enabled = False

    def send_packet(self, path_index):
        self.packet_number += 1
        data = (self.packet_number, 'This is packet %d' % self.packet_number, path_index)
        self.unacked_packets[path_index].append(data)
        self.start_ack_timer(path_index, data)
        if CLIENT :
            self.logger.info(f"At time {self.env.now}s: send packet using path {path_index} : {data}")
        task = Task(self.env.now, self.network.send, "Send Packet", data)
        self.scheduler.add_task(self.env.now, task)
    def start_resend_packet(self, path_index, data):
        if data in self.unacked_packets[path_index]:
            if CLIENT:
                self.logger.info(f"At time {self.env.now}s: resend packet using path {path_index} : {data}")
            task = Task(self.env.now, self.network.send, "Resend Packet", data)
            self.scheduler.add_task(self.env.now, task)
    def start_resend_timer(self, resend_timeout):
        self.resend_enabled = True
        self.env.process(self.stop_resend_timer(resend_timeout))

        # 재전송 타이머 정지 함수 추가
    async def stop_resend_timer(self, resend_timeout):
        await self.env.timeout(resend_timeout)
        self.resend_enabled = False

    def start_ack_timer(self, path_index, data):
        timeout = self.rtt_estimations[path_index] * 2 if self.rtt_estimations[path_index] > 0 else 1.0  # Use RTT estimation to set timeout
        task = Task(self.env.now + timeout, self.resend_packet, "Resend Packet", path_index, data, self.env.now + timeout)  # Include the timeout time as an argument
        self.scheduler.add_task(task.time, task)

    def resend_packet(self, path_index, data, task_time):
        if data in self.unacked_packets[path_index] and self.resend_enabled:
            if CLIENT:
                self.logger.info(f"At time {self.env.now}s: resend packet using path {path_index} : {data}")
            task = Task(task_time, self.network.send, "Resend Packet", data)
            self.scheduler.add_task(task.time, task)

    def send(self, path_index):
        for _ in range(int(self.window_sizes[path_index])):
            self.send_packet(path_index)
        self.sent_time_logs[path_index].append(self.env.now)
        self.inflight_packets[path_index] += 1

    def receive_ack(self, ack):
        rtt_sample = self.env.now - self.sent_time_logs[ack[2]][-1]  # Calculate RTT sample

        if self.rtt_estimations[ack[2]] == 0:
            self.rtt_estimations[ack[2]] = rtt_sample
        else:
            self.rtt_estimations[ack[2]] = (1 - self.alpha) * self.rtt_estimations[ack[2]] + self.alpha * rtt_sample
        if CLIENT:
            self.logger.info(f"At time {self.env.now}s: ACK of packet {ack[0]} arrived using path {ack[2]}")
        self.ack_time_logs[ack[2]].append(self.env.now)
        if ack in self.unacked_packets[ack[2]]:
            self.unacked_packets[ack[2]].remove(ack)

    def retransmit_unacked_packets(self):
        for path_index in range(num_paths):
            for packet in list(self.unacked_packets[path_index]):
                if CLIENT:
                    self.logger.info(f"Retransmitting packet {packet[0]} on path {packet[2]}")
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
                    self.start_resend_packet(ack[2], ack)
            else:
                self.window_sizes[ack[2]] += 1
            self.window_size_logs[ack[2]].append((self.env.now, self.window_sizes[ack[2]]))

            available_slots = int(self.window_sizes[ack[2]]) - self.inflight_packets[ack[2]]
            if available_slots > 0:
                self.send(ack[2])
            if CONGESTION:
                self.logger.info(f"At time {self.env.now}s: Window size for path {ack[2]} changed to {self.window_sizes[ack[2]]}")


    def start_sending(self):
        def send_initial_packets(env, path_indices):
            yield env.timeout(1.0)  # add this line to delay the initial packet by 1 second
            for i in path_indices:
                yield env.timeout(0.001)
                self.send(i)

        self.env.process(send_initial_packets(self.env, range(num_paths)))
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
        self.transmitted_packets = [0] * self.num_paths

    def send(self, data):
        path_index = data[2]
        bandwidth, _, _ = self.path_characteristics[path_index]
        packet_size = 1500  # bits
        max_packets_in_bandwidth = bandwidth // packet_size

        # check the bandwidth limit when a new packet is to be sent
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
        self.logger = logging.getLogger(self.__class__.__name__)

    def receive(self, data):
        self.received_data.append(data)
        if SERVER:
            if data[2] in [0, 1, 2]:
                self.logger.info(f"At time {self.env.now}s: received packet number: {data[0]} on path {data[2]}")
        ack = (data[0], 'ACK for packet %d' % data[0], data[2])
        self.ack_queues[data[2]].append(ack)
        if not self.is_sending_ack[data[2]]:
            task = Task(self.env.now + 0.0001, self.send_ack, "Send ACK", data[2])  # Adjusted the task time here
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

path_characteristics = [(10000, 1, 0.1)]
num_paths = len(path_characteristics)
acks = simpy.Store(env)
server = Server(env, acks, path_characteristics, scheduler)
network = Network(env, server, path_characteristics, scheduler)
client = Client(env, network, acks, scheduler, num_paths=num_paths, path_characteristics=path_characteristics)
client.start_sending()

env.process(client.receive_ack_and_send())

scheduler_process = env.process(scheduler.schedule())
if not DEBUG:
    progress_bar = ProgressBar(env, simtime)
    env.process(progress_bar.progress())
# Modify this part of the code
env.run(until=simtime)

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