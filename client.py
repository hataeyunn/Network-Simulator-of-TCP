import socket
import threading
import time

class Client:
    def __init__(self):
        self.host = 'localhost'
        self.ports = [5000, 5001, 5002]  # Three ports for different paths
        self.packet_number = 0
        self.packet_size = 1500
        self.total_data_size = 10 * 1024 * 1024  # 10MB
        self.data_sent = 0
        self.start_time = None
        self.lock = threading.Lock()

    def start(self):
        for i in range(3):
            t = threading.Thread(target=self.send_packets, args=(self.ports[i],))
            t.start()

    def send_packets(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, port))
            while self.data_sent < self.total_data_size:
                self.lock.acquire()
                packet = self.generate_packet()
                self.data_sent += self.packet_size
                if self.start_time is None:
                    self.start_time = time.time()
                self.lock.release()
                sock.sendall(packet)
                time.sleep(0.001)  # Simulate transmission delay

            if self.data_sent >= self.total_data_size:
                elapsed_time = time.time() - self.start_time
                throughput = self.total_data_size / elapsed_time
                latency = elapsed_time / (self.total_data_size / self.packet_size)
                print(f"Throughput: {throughput} bytes/sec")
                print(f"Latency: {latency} sec")
                # Perform any necessary cleanup and exit

    def generate_packet(self):
        self.packet_number += 1
        return f"Packet {self.packet_number}".encode()


client = Client()
client.start()
