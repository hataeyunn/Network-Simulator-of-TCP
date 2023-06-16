import socket
import threading
 
class Server:
    def __init__(self):
        self.expected_packet_number = 0
        self.received_packets = {}
        self.lock = threading.Lock()

    def process_packet(self, packet):
        packet_number = int(packet.split("#")[1])
        if packet_number == self.expected_packet_number:
            self.received_packets[packet_number] = packet
            self.expected_packet_number += 1
            while self.expected_packet_number in self.received_packets:
                packet = self.received_packets.pop(self.expected_packet_number)
                self.expected_packet_number += 1
                # ACK 보내기
                client_socket.send(packet)
        else:
            # 재전송을 요청하는 ACK 보내기
            client_socket.send(f"ACK #{self.expected_packet_number - 1}".encode())

# 서버 실행
server = Server()
server_address = 'localhost'
server_port = 6000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_address, server_port))

while True:
    packet = client_socket.recv(1024)
    server.process_packet(packet)
    if not packet:
        break

client_socket.close()
