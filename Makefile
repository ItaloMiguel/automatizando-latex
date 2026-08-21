.PHONY: run build stop logs test clean

run:
	docker compose up --build

build:
	docker compose build

stop:
	docker compose down

logs:
	docker compose logs -f

test:
	python -m unittest discover -v

clean:
	docker compose down --volumes --remove-orphans
