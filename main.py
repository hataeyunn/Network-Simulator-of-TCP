import simpy
import random

class Client:
    def __init__(self, env, network, acks, num_paths, packet_size=1500, initial_window_size=1):
        self.env = env
        self.network = network
        self.acks = acks
        self.packet_size = packet_size
        self.packet_number = 0
        self.window_sizes = [initial_window_size] * num_paths

    def send(self):
        while True:
            for i in range(len(self.window_sizes)):
                for _ in range(int(self.window_sizes[i])):
                    self.packet_number += 1
                    data = (self.packet_number, 'This is packet %d' % self.packet_number, i)
                    print(f"{self.env.now}s: {data[0]} packet using path {i} ")
                    self.network.send(data)

            yield self.env.timeout(1)  # 매 1초마다 패킷을 생성
            yield self.env.process(self.receive_ack())

    def receive_ack(self):
        while self.acks.items:
            ack = yield self.acks.get()
            # 혼잡창 크기 조정
            if ack[0] % 10 == 0:
                self.window_sizes[ack[2]] /= 2  # 혼잡창을 절반으로 줄임
            else:
                self.window_sizes[ack[2]] += 1  # 혼잡창을 증가시킴



class Network:
    def __init__(self, env, server, path_characteristics):
        self.env = env
        self.server = server
        self.path_characteristics = path_characteristics
        self.num_paths = len(path_characteristics)
        self.incoming_queues = [simpy.Store(env) for _ in range(self.num_paths)]

    def send(self, data):
        path_index = data[2]
        self.incoming_queues[path_index].put(data)

    def run(self):
        for i in range(self.num_paths):
            self.env.process(self._path_run(i))

    def _path_run(self, path_index):
        last_transmission_end_time = 0
        while True:
            data = yield self.incoming_queues[path_index].get()
            bandwidth, latency, error_rate = self.path_characteristics[path_index]
            packet_size = 1500  # bytes
            transmission_time = packet_size / bandwidth  # Calculate transmission time

            if self.env.now < last_transmission_end_time:
                delay = max(0, last_transmission_end_time - self.env.now + latency)
            else:
                delay = transmission_time + latency

            last_transmission_end_time = self.env.now + delay

            if random.random() > error_rate:  # If not error
                yield self.env.timeout(delay)  # Transmission delay + latency
                self.server.receive(data)


class Server:
    def __init__(self, env, acks, path_characteristics):
        self.env = env
        self.received_data = []
        self.acks = acks
        self.path_characteristics = path_characteristics

    def receive(self, data):
        self.received_data.append(data)
        if data[2]==2:
            print(f"At time {self.env.now}, received packet number: {data[0]} on path {data[2]}")
        ack = (data[0], 'ACK for packet %d' % data[0], data[2])
        self.env.process(self.send_ack(ack))  # Process로 send_ack를 실행

    def send_ack(self, ack):
        path_index = ack[2]
        bandwidth, latency, error_rate = self.path_characteristics[path_index]

        if random.random() > error_rate:  # If not error
            yield self.env.timeout(latency)  # Transmission delay
            self.acks.put(ack)


env = simpy.Environment()

num_paths = 3
path_characteristics = [(1000, 1, 0.01), (500, 2, 0.02), (2000, 0.5, 0.005)]  # (bandwidth, latency, error_rate) for each path
acks = simpy.Store(env)
server = Server(env, acks, path_characteristics)
network = Network(env, server, path_characteristics)
client = Client(env, network, acks, num_paths=num_paths)

env.process(client.send())
network.run()
env.run(until=10)

