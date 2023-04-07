.PHONY: start build push run down test twine

start:
	openai_forward run

image = "beidongjiedeguang/openai-forward:latest"
build:
	@docker build -t $(image) -f docker/Dockerfile .

push:
	@docker push $(image)

compose_path = "docker-compose.yaml"
up:
	@docker-compose  -f $(compose_path) up -d

down:
	@docker-compose  -f $(compose_path) down

run:
	@docker-compose -f $(compose_path) run -it -p 8000:8000 openai_forward bash

test:
	pytest -v tests

twine:
	@twine upload dist/*
	@rm -rf dist/*

build-web:
	@cd third-party/forward_web && npm run build
	@cd third-party/forward_web/build && npx uglify-js index.js -m -o index.min.js
	@mv third-party/forward_web/build/index.min.js openai_forward/web/index.js

start-web:
	@openai_forward node --port=9099 --base_url="https://api.openai.com"

