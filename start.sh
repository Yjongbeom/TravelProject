#!/bin/bash

# 필요한 디렉토리 생성
mkdir -p /tmp/client_body /tmp/proxy /tmp/fastcgi /tmp/uwsgi /tmp/scgi
chmod 777 /tmp/client_body /tmp/proxy /tmp/fastcgi /tmp/uwsgi /tmp/scgi

# Gunicorn 서버 실행
gunicorn --bind 0.0.0.0:8002 config.wsgi:application &

# Daphne 서버 실행
daphne -b 0.0.0.0 -p 8003 config.asgi:application &

# 서비스들이 시작될 때까지 잠시 대기
sleep 5

# Nginx 서버 실행
nginx -g 'daemon off;'