.PHONY: start build push run down test twine log pull

image := "beidongjiedeguang/openai-forward:latest"
container := "openai-forward-container"
compose_path := "docker-compose.yaml"

start:
	docker run -d \
    --name $(container) \
    --env-file .env \
    -p 27001:8000 \
    -v $(shell pwd)/Log:/home/openai-forward/Log \
    -v $(shell pwd)/openai_forward:/home/openai-forward/openai_forward \
    $(image)


exec:
	docker exec -it $(container) bash

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