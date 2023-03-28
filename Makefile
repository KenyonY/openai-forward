.PHONY: build push run down twine

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
	twine upload dist/*