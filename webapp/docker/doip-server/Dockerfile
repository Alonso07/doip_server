FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "doip-server>=0.5.4"

RUN mkdir -p /config

EXPOSE 13400/tcp
EXPOSE 13400/udp
EXPOSE 8080/tcp

# Entrypoint: requires /config/gateway.yaml to be mounted
CMD ["python", "-m", "doip_server.main", \
     "--gateway-config", "/config/gateway.yaml", \
     "--web", "--web-host", "0.0.0.0", "--web-port", "8080"]
