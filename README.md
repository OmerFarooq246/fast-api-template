setup:
1. venv create, pip install -r requirements.txt
2. env update if necessary
3. alembic revision --autogenerate -m "Initial migration"
4. alembic upgrade head
5. uvicorn app.main:app --reload --port 8000        => for dev
6. uvicorn app.main:app --host 0.0.0.0 --port 8000  => for prod

Remember:
1. include new models in app/alembic/env.py