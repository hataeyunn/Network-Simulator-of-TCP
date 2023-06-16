#!/bin/bash

# 포트 번호를 변수로 저장
PORT1=8000
PORT2=9000
PORT3=10000
PORT4=5000

# 포트 번호에 해당하는 프로세스 종료
fuser -k "$PORT1/tcp"
fuser -k "$PORT2/tcp"

echo "포트 $PORT1, $PORT2, $PORT3, $PORT4를 종료했습니다."

