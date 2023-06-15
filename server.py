import socket
import threading

class Server:
    def __init__(self):
        self.host = 'localhost'
        self.server_port = 6000
        self.expected_packet_number = 1

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.server_port))
            sock.listen(1)
            conn, addr = sock.accept()
            with conn:
                while True:
                    data = conn.recv(1024)  # Adjust buffer size as needed
                    if not data:
                        break
                    packet_number = self.process_packet(data)
                    if packet_number == self.expected_packet_number:
                        self.expected_packet_number += 1
                    elif packet_number < self.expected_packet_number:
                        # Resend ACK for the missing packet
                        conn.sendall(f'ACK {packet_number}'.encode())

    def process_packet(self, packet):
        # Process the received packet, check packet number, and perform any necessary operations
        pass


server = Server()
server.start()
