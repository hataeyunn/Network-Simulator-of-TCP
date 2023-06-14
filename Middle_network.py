import socket
import queue
import threading
import time
import random

# 소켓 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 소켓 바인딩
sock.bind(('localhost', 12345))

# Queue 생성
q = queue.Queue()

# 데이터 처리 함수
def process_data():
    while True:
        # Queue에서 데이터가 없으면 대기
        if q.empty():
            time.sleep(0.1)
            continue

        # Queue에서 데이터를 꺼내서 전송
        data = q.get()
        # 데이터 전송 속도를 10Mbps로 가정하여 전송에 소요되는 시간 계산
        time.sleep(len(data) * 8 / (10 * 1024 * 1024))
        #time.sleep(5)
        # 0.0001의 확률로 데이터 손실 발생
        if random.random() < 0.001:
            print("Data loss occurred")
        else:
            print(f"Data sent to destination. Size: {len(data)} bytes")

# 데이터 수신 함수
def receive_data():
    while True:
        # 150 KB 크기의 패킷을 수신
        data, addr = sock.recvfrom(150 * 1024)
        if random.random() < 0.001:
            print("Data loss occurred")
        else:
            # 수신한 데이터를 Queue에 추가
            q.put(data)
            print(len(q.queue))
            # 전송 성공한 경우 로그 출력
            print(f"Data received. Size: {len(data)} bytes")
        

# 쓰레드 생성
t1 = threading.Thread(target=receive_data)
t2 = threading.Thread(target=process_data)

# 쓰레드 시작
t1.start()
t2.start()

# 쓰레드 종료 대기
t1.join()
t2.join()




