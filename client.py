import socket
import random
import string

def generate_random_data(size):
    return ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=size))


def start_client(host, ports):
    # 클라이언트 소켓 생성
    client_sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(len(ports))]
    
    try:
        # 서버에 연결
        for i, port in enumerate(ports):
            client_socket = client_sockets[i]
            client_socket.connect((host, port))
        
        # 가상의 데이터를 1500바이트로 나누어 보내기
        data_size = 10 * 1024 * 1024  # 데이터 크기 (10MB)
        packet_size = 1500  # 패킷 크기
        packets_sent = 0  # 전송한 패킷 수
        current_port = 0  # 현재 사용할 클라이언트 소켓의 인덱스
        while packets_sent * packet_size < data_size:
            data = generate_random_data(packet_size).encode()
            packet_info = str(packets_sent).zfill(8) + data.decode()  # 패킷 정보에 순서 추가
            client_socket = client_sockets[current_port]
            try:
                client_socket.sendall(packet_info.encode())  # sendall로 변경하여 전체 데이터 전송 보장
                response = client_socket.recv(1024).decode()
                print("Server response from port", ports[current_port], ":", response)
            except ConnectionResetError:
                print("Connection reset by peer")
                break
            except ConnectionAbortedError:
                print("Connection aborted")
                break
            except socket.error as e:
                print("Socket error:", e)
                break
            packets_sent += 1
            current_port = (current_port + 1) % len(client_sockets)
    
    finally:
        # 클라이언트 소켓 닫기
        for client_socket in client_sockets:
            client_socket.close()

# 클라이언트 시작
host = "127.0.0.1"  # 서버 IP 주소
ports = [8000, 9000, 10000]  # 서버의 포트 번호들
start_client(host, ports)
