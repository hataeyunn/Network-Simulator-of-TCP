import socket
import threading
import random

class Network:
    def __init__(self):
        self.host = 'localhost'
        self.client_ports = [5000, 5001, 5002]  # Client ports
        self.server_port = 6000  # Server port
        self.queue_locks = [threading.Lock() for _ in range(3)]  # Locks for each queue
        self.queues = [[] for _ in range(3)]  # Queues for each path
        self.acks = [[] for _ in range(3)]  # ACK queues for each path
        self.error_rates = [0.1, 0.2, 0.3]  # Error rates for each path
        self.rtt_values = [1, 2, 3]  # RTT values for each path
        self.bandwidths = [1000000, 2000000, 3000000]  # Bandwidths for each path

    def start(self):
        # Start the server thread
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()

        # Start the client threads
        client_threads = []
        for i in range(3):
            t = threading.Thread(target=self.receive_packets, args=(self.client_ports[i], i))
            client_threads.append(t)
            t.start()

        for t in client_threads:
            t.join()

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.host, self.server_port))
            server_sock.listen(1)
            conn, addr = server_sock.accept()
            with conn:
                while True:
                    data = conn.recv(1024)  # Adjust buffer size as needed
                    if not data:
                        break
                    self.process_packet(data)
                    conn.sendall(b'ACK')  # Send ACK

    def receive_packets(self, port, index):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, port))
            while True:
                packet = sock.recv(1024)  # Adjust buffer size as needed
                if not packet:
                    break
                if random.random() >= self.error_rates[index]:  # Random drop based on error rate
                    self.queue_locks[index].acquire()
                    self.queues[index].append(packet)
                    self.queue_locks[index].release()
                time.sleep(0.001)  # Simulate processing delay

    def process_packet(self, packet):
        # Process the received packet and perform any necessary operations
        pass


network = Network()
network.start()
