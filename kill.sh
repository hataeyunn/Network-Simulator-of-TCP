#!/bin/bash

# 포트 번호를 변수로 저장
PORT1=5001
PORT2=5002

# 포트 번호에 해당하는 프로세스 종료
fuser -k "$PORT1/tcp"
fuser -k "$PORT2/tcp"

echo "포트 $PORT1와 $PORT2를 종료했습니다."

