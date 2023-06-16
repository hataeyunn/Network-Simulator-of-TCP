import socket
import threading

def handle_client(client_socket):
    received_packets = []  # 받은 패킷 저장
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            packet_order = int(data[:8])  # 패킷 순서 추출
            packet_data = data[8:]
            received_packets.append((packet_order, packet_data))  # 받은 패킷 저장
            client_socket.send(data.encode())
        except ConnectionResetError:
            print("Connection reset by peer")
            break
        except ValueError:
            print("Invalid packet format")
            break
    
    # 패킷 순서 확인
    ordered = True
    for i in range(1, len(received_packets)):
        if received_packets[i][0] != received_packets[i-1][0] + 1:
            ordered = False
            break
    
    if ordered:
        print("Received packets in order")
    else:
        print("Received packets out of order")
    
    client_socket.close()

def start_server(host, ports):
    server_sockets = []
    
    # 서버 소켓 생성 및 바인딩
    for port in ports:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)
        server_sockets.append(server_socket)
        print("Server listening on port", port)
    
    # 클라이언트 연결 처리
    while True:
        for server_socket in server_sockets:
            client_socket, addr = server_socket.accept()
            print("Connected to", addr)
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()

# 메인 서버 시작
host = "127.0.0.1"  # 로컬 호스트 IP 주소
ports = [8000, 9000, 10000]  # 클라이언트와 연결될 포트 번호들
start_server(host, ports)
