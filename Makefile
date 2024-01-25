.PHONY: monitor start start-webui build push run down test twine log pull

image := "beidongjiedeguang/openai-forward:latest"
webui_image := "beidongjiedeguang/openai-forward:webui-latest"
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
	-v $(shell pwd)/FLAXKV_DB:/home/openai-forward/FLAXDV_DB \
    -v $(shell pwd)/openai_forward:/home/openai-forward/openai_forward \
    $(image) --port=8000 --workers=1
	@make log


start-webui:
	@docker run -d \
    --name $(container) \
    --env-file .env \
    -p 8000:8000 \
    -p 8001:8001 \
    -v $(shell pwd)/Log:/home/openai-forward/Log \
	-v $(shell pwd)/FLAXKV_DB:/home/openai-forward/FLAXDV_DB \
    -v $(shell pwd)/openai_forward:/home/openai-forward/openai_forward \
    $(webui_image)
	@make log

exec:
	docker exec -it $(container) sh

log:
	docker logs -f $(container)

rm:
	docker rm -f $(container)

stop:
	docker stop $(container)

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

build-webui:
	docker build --tag $(webui_image) . -f webui.Dockerfile

build-push:
	docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag $(image) .

pull:
	 docker pull $(image)

deploy:
	vercel --prod
