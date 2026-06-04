FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir "sovd-server>=1.4.0"

RUN mkdir -p /config

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080/tcp

ENTRYPOINT ["/entrypoint.sh"]
