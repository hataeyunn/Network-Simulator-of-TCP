import socket
import time
import json

# 소켓 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_id = "localhost"
port = 12345
packet = [server_id, port]

# 서버 주소와 포트 설정
server_addr = ("localhost", 12345)

# cubic 알고리즘 활성화

# 서버에 연결
sock.connect(server_addr)

# 150 KB 크기의 랜덤 데이터 생성
data = bytes([i % 256 for i in range(150 * 1024)])

# 데이터를 1024 바이트씩 나누어서 전송
for i in range(0, len(data), 1024):
    chunk = data[i : i + 1024]
    sock.sendall(chunk)
    time.sleep(0.01)  # 데이터가 너무 빠르게 전송되는 것을 방지하기 위해 잠시 대기
