import socket
import threading
import queue
import time

# 서버 주소와 포트
server_address = ("localhost", 5000)
source_address = ("localhost", 4000)
# 패킷 번호 초기값
packet_num = 0

# ACK 패킷을 저장할 큐
ack_queue = queue.Queue()


# 송신 함수
def send_packet():
    global packet_num

    # 소켓 생성
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        # 패킷 생성
        packet = [
            server_address[0],
            server_address[1],
            packet_num,
            0,
            source_address[0],
            source_address[1],
        ]

        # 리스트를 문자열로 변환하여 송신
        packet_str = ",".join(str(e) for e in packet)
        sock.sendto(packet_str.encode(), server_address)

        # 보낸 패킷을 큐에 추가
        ack_queue.put(packet_num)

        # 패킷 번호 증가
        packet_num += 1

        # 1초 대기
        time.sleep(1)

    # 소켓 닫기
    sock.close()


# 수신 함수
def receive_packet():
    # 소켓 생성
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", 4000))

    while True:
        # 패킷 수신
        data, addr = sock.recvfrom(1024)

        # 문자열을 리스트로 변환
        packet = [int(e) for e in data.decode().split(",")]

        # ACK 패킷인 경우
        if packet[3] == 1:
            # 해당 패킷 번호를 큐에서 제거
            if not ack_queue.empty() and ack_queue.queue[0] == packet[2]:
                ack_queue.get()
        # ACK 패킷이 아닌 경우
        else:
            # ACK 패킷 생성하여 송신
            ack_packet = [
                server_address[0],
                server_address[1],
                packet[2],
                1,
                source_address[0],
                source_address[1],
            ]
            ack_packet_str = ",".join(str(e) for e in ack_packet)
            sock.sendto(ack_packet_str.encode(), server_address)

    # 소켓 닫기
    sock.close()


# 송신 스레드 시작
send_thread = threading.Thread(target=send_packet)
send_thread.start()

# 수신 스레드 시작
receive_thread = threading.Thread(target=receive_packet)
receive_thread.start()
