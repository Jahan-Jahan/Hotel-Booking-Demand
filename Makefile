.PHONY: install eda sql train test serve docker-build docker-run all

install:
	pip install -r requirements-dev.txt

eda:
	python -m src.eda

sql:
	python -m src.run_sql

train:
	python -m src.train

test:
	pytest -q

serve:
	uvicorn src.app:app --reload --port 8000

docker-build:
	docker build -t hotel-cancellation-api .

docker-run:
	docker run --rm -p 8000:8000 hotel-cancellation-api

all: eda sql train test
