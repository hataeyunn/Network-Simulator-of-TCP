import socket
import pickle
import queue


class Node:
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip_address = "localhost"  # server address
        self.port = 5000  # server port
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


def receive_packet(sock, expected_packet_num, packet_size):
    global des

    # receive packet
    data, addr = sock.recvfrom(packet_size)
    packet = pickle.loads(data)

    des = (packet[2], packet[3])
    # check packet number
    packet_num = packet[2]
    if packet_num != expected_packet_num:
        print(
            f"Error: Expected packet number {expected_packet_num}, but received {packet_num}"
        )
        return None, None

    # send ACK
    ack_packet = [packet[0], packet[1], packet_num, 1, packet[2], packet[3]]
    ack_data = pickle.dumps(ack_packet)
    sock.sendto(ack_data, addr)

    return packet, addr


def main():
    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(des)

    # set initial expected packet number
    expected_packet_num = 0

    # receive and process packets
    while True:
        packet, addr = receive_packet(sock, expected_packet_num, 1024)
        if packet is not None:
            # update expected packet number
            expected_packet_num += 1

            # print received packet
            print(f"Received packet from {addr}: {packet}")


if __name__ == "__main__":
    main()
