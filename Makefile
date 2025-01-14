.PHONY: install run

install:
	poetry install
	(cd frontend && npm install)

format:
	poetry run black codenames/
	poetry run black tests/

run-tests:
	poetry run pytest tests/codenames $(pytest_args)

run-backend:
	poetry run uvicorn --app-dir codenames/ api:app --reload --log-level debug

run-frontend:
	(cd frontend && npm start)

run-jupyter:
	poetry run jupyter lab

init-db:
	mkdir -p instance/
	poetry run alembic upgrade head
