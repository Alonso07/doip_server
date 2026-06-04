.PHONY: help build-images start stop dev-backend dev-frontend status logs clean

HOST_DATA_DIR ?= $(shell pwd)/data

help:
	@echo ""
	@echo "  Diagnostic Servers Manager"
	@echo ""
	@echo "  Setup:"
	@echo "    make build-images     Build DoIP and SOVD server Docker images"
	@echo "    make start            Build images + start management webapp"
	@echo "    make stop             Stop management webapp"
	@echo ""
	@echo "  Development:"
	@echo "    make dev-backend      Run backend with hot-reload on :8000"
	@echo "    make dev-frontend     Run Vite dev server on :5173"
	@echo ""
	@echo "  Maintenance:"
	@echo "    make status           Show running diagnostic containers"
	@echo "    make logs             Stream backend logs"
	@echo "    make clean            Remove all containers, images and data"
	@echo ""

build-images:
	@echo ">>> Building DoIP server image..."
	docker build -t diag-doip-server:latest docker/doip-server/
	@echo ">>> Building SOVD server image..."
	docker build -t diag-sovd-server:latest docker/sovd-server/
	@echo ">>> Images ready."

start: build-images
	@mkdir -p "$(HOST_DATA_DIR)"
	@echo "HOST_DATA_DIR=$(HOST_DATA_DIR)" > .env
	docker-compose up -d --build
	@echo ""
	@echo "  Management app  →  http://localhost:3000"
	@echo "  Backend API     →  http://localhost:8000"
	@echo "  API docs        →  http://localhost:8000/docs"
	@echo ""

stop:
	docker-compose down

dev-backend:
	@mkdir -p data
	cd backend && \
		pip install -r requirements.txt && \
		DATA_DIR="../data" HOST_DATA_DIR="$(HOST_DATA_DIR)" \
		uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm install && npm run dev

status:
	@echo "--- Diagnostic server containers ---"
	@docker ps --filter "label=diag-manager=true" \
		--format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || \
		echo "No containers found (is Docker running?)"

logs:
	docker-compose logs -f backend

clean:
	docker-compose down -v
	@docker rm -f $$(docker ps -aq --filter "label=diag-manager=true") 2>/dev/null || true
	@docker rmi diag-doip-server:latest diag-sovd-server:latest 2>/dev/null || true
	rm -rf data/
	rm -f .env
	@echo "Cleaned up."
