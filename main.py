import simpy
import random
from collections import deque
import heapq
import matplotlib.pyplot as plt


class Task:
    def __init__(self, time, func, name, *args):
        assert callable(func), "func must be a callable function, not a generator"
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
            #print(f"At time {self.env.now}s: Task Name: {task.name}, Function: {task.func}")
            if self.env.now < task_time:
                yield self.env.timeout(task_time - self.env.now)

            task.func(*task.args)


class Client:
    def __init__(self, env, network, acks, scheduler, num_paths, packet_size=1500, initial_window_size=1):
        self.env = env
        self.network = network
        self.acks = acks
        self.scheduler = scheduler
        self.packet_size = packet_size
        self.packet_number = 0
        self.window_sizes = [initial_window_size] * num_paths
        self.inflight_packets = [0] * num_paths  # To keep track of inflight packets
        self.window_size_logs = [[] for _ in range(num_paths)]  # To log window size changes


    def send(self, path_index):
        for _ in range(int(self.window_sizes[path_index])):
            self.packet_number += 1
            data = (self.packet_number, 'This is packet %d' % self.packet_number, path_index)
            print(f"At time {self.env.now}s: {data[0]} packet using path {path_index} ")

            task = Task(self.env.now, self.network.send, "Send Packet", data)
            self.scheduler.add_task(task.time, task)

    def receive_ack(self, ack):
        print(f"At time {self.env.now}s: ACK of packet {ack[0]} arrived using path {ack[2]}")

    def receive_ack_and_send(self):
        while True:
            ack = yield self.acks.get()
            self.receive_ack(ack)
            self.inflight_packets[ack[2]] -= 1  # ACK received, decrement inflight packets

            if ack[0] % 10 == 0:
                self.window_sizes[ack[2]] /= 2
            else:
                self.window_sizes[ack[2]] += 1

            # Record the window size change
            self.window_size_logs[ack[2]].append((self.env.now, self.window_sizes[ack[2]]))


            # Calculate the number of available slots in the congestion window
            available_slots = int(self.window_sizes[ack[2]]) - self.inflight_packets[ack[2]]
            if available_slots > 0:
                self.packet_number += 1
                data = (self.packet_number, 'This is packet %d' % self.packet_number, ack[2])
                print(f"At time {self.env.now}s: {data[0]} packet using path {ack[2]} ")
                task = Task(self.env.now, self.network.send, "Send Packet After Receiving ACK", data)
                self.scheduler.add_task(task.time, task)
                self.inflight_packets[ack[2]] += 1  # Increment inflight packets
    def start_sending(self):
        for i in range(num_paths):
            self.send(i)

        env.process(self.receive_ack_and_send())


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
            task = Task(self.env.now, self._path_run, "Start Path Run", path_index)
            self.scheduler.add_task(task.time, task)

    def _path_run(self, path_index):
        self.is_transmitting[path_index] = True
        while self.packet_queues[path_index]:
            data = self.packet_queues[path_index].popleft()
            bandwidth, latency, error_rate = self.path_characteristics[path_index]
            packet_size = 1500  # bytes
            transmission_time = packet_size / bandwidth  # Calculate transmission time

            if random.random() > error_rate:  # If not error
                task1 = Task(self.env.now + transmission_time + latency, self.server.receive, "Server Receives Packet", data)
                self.scheduler.add_task(task1.time, task1)

        self.is_transmitting[path_index] = False

    def run(self):
        for i in range(self.num_paths):
            task = Task(self.env.now, self._path_run, "Run Path", i)
            self.scheduler.add_task(task.time, task)


class Server:
    def __init__(self, env, acks, path_characteristics, scheduler):
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
            task = Task(self.env.now, self.send_ack, "Send ACK", data[2])
            self.scheduler.add_task(task.time, task)

    def send_ack(self, path_index):
        self.is_sending_ack[path_index] = True
        while self.ack_queues[path_index]:
            ack = self.ack_queues[path_index].popleft()
            bandwidth, latency, error_rate = self.path_characteristics[path_index]
            packet_size = 1500  # bytes
            transmission_delay = packet_size / bandwidth  # Fixed transmission delay

            if random.random() > error_rate:  # If not error
                task2 = Task(self.env.now + transmission_delay + latency, self.acks.put, "Client Receives ACK",
                             ack)  # Here we call client's receive_ack function
                self.scheduler.add_task(task2.time, task2)

        self.is_sending_ack[path_index] = False


env = simpy.Environment()
scheduler = Scheduler(env)

num_paths = 3
path_characteristics = [(1000, 1, 0), (1000, 1, 0), (1000, 1 , 0)]  # (bandwidth, latency, error_rate) for each path
acks = simpy.Store(env)
server = Server(env, acks, path_characteristics, scheduler)
network = Network(env, server, path_characteristics, scheduler)
client = Client(env, network, acks, scheduler, num_paths=num_paths)
client.start_sending()

# Let's start the process for client to receive ack and send packets
env.process(client.receive_ack_and_send())

scheduler_process = env.process(scheduler.schedule())

env.run(until=100)
for path_index in range(num_paths):
    times, window_sizes = zip(*client.window_size_logs[path_index])
    plt.plot(times, window_sizes, label=f'Path {path_index + 1}')

plt.title('Congestion Window Size Over Time')
plt.xlabel('Time (s)')
plt.ylabel('Window Size')
plt.legend()
plt.show()
print(f"Server received data: {server.received_data}")
