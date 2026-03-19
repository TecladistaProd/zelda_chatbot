.PHONY: dev start

dev:
	.venv/Scripts/uvicorn main:app --reload --host 0.0.0.0 --port 8000

start:
	.venv/Scripts/uvicorn main:app --host 0.0.0.0 --port 8000
