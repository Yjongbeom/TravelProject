FROM python:3.9-slim

WORKDIR /app

# 시스템 패키지 설치 및 nginx 사용자 생성
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    nginx \
    procps \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirments.txt .
RUN pip install --upgrade pip && pip install -r requirments.txt && pip install twisted[tls,http2]


COPY . .

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh
COPY start.sh /start.sh
COPY wait-for-it.sh /wait-for-it.sh

RUN chmod +x /entrypoint.sh /start.sh /wait-for-it.sh

RUN mkdir -p /app/db_data && chmod 777 /app/db_data
RUN mkdir -p /var/lib/nginx/body /var/cache/nginx && \
    chmod 777 /var/lib/nginx/body /var/cache/nginx
RUN chmod 777 /run

ENV SECRET_KEY=${SECRET_KEY}
ENV REDIS_URL=${REDIS_URL}

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/start.sh"]
