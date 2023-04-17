import socket
import pickle
import queue


class Node:
    def __init__(self, _ip_address : str = "localhost", _port : int = 5000) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip_address = _ip_address  # server address
        self.port = _port  # server port
        self.sock.bind(tuple([self.ip_address, self.port]))
        self.packet_size = 1024
        self.server_buffer = queue.Queue()

    def receive_packet(self, expected_packet_num: int, packet_size: int) -> None:
        # receive packet
        data, addr = self.sock.recvfrom(self.packet_size)
        packet = pickle.loads(data)
        des = (packet[2], packet[3])

        # check packet number
        packet_num = packet[2]
        if packet_num != expected_packet_num:
            if packet_num < expected_packet_num:
                print(
                    f"Error: Expected packet number {expected_packet_num}, but received {packet_num}"
                )
            self.input_buffer(packet)
        return packet, addr

    def send_ack(self, expected_packet_num, packet_size) -> None:
        pass

    def input_buffer(self, packet) -> None:
        self.server_buffer.put(packet)
        pass

    def compare_packet_num_in_queue(self) -> None:
        pass
