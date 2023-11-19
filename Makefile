.PHONY: monitor start build push run down test twine log pull

image := "beidongjiedeguang/openai-forward:latest"
container := "openai-forward-container"
compose_path := "docker-compose.yaml"

monitor:
	@./scripts/ai-forward-monitor.sh

#stop-monitor:
#	@pkill -f ai-forward-monitor.sh
#	@pkill aifd

start:
	@docker run -d \
	--restart=unless-stopped \
    --name $(container) \
    --env-file .env \
    -p 8000:8000 \
    -v $(shell pwd)/Log:/home/openai-forward/Log \
	-v $(shell pwd)/CACHE_LMDB:/home/openai-forward/CACHE_LMDB \
	-v $(shell pwd)/CACHE_LEVELDB:/home/openai-forward/CACHE_LEVELDB \
    -v $(shell pwd)/openai_forward:/home/openai-forward/openai_forward \
    $(image) --port=8000 --workers=2
	@make log

exec:
	docker exec -it $(container) sh

log:
	docker logs -f $(container)

rm:
	docker rm -f $(container)

up:
	@docker-compose  -f $(compose_path) up

down:
	@docker-compose  -f $(compose_path) down

run:
	@docker-compose -f $(compose_path) run -it -p 8000:8000 openai_forward bash

test:
	pytest -v tests

twine:
	@twine upload dist/*
	@rm -rf dist/*

build:
	docker build --tag $(image) .

build-push:
	docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag $(image) .

pull:
	 docker pull $(image)

deploy:
	vercel --prod
