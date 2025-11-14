setup:
1. venv create: python3 -m venv ./venv
2. venv activate: source venv/bin/activate
3. pip install -r requirements.txt | pip freeze > requirements.txt
4. env update if necessary
5. alembic revision --autogenerate -m "Initial migration"
6. alembic upgrade head
7. uvicorn app.main:app --reload --port 8000        => for dev
8. uvicorn app.main:app --host 0.0.0.0 --port 8000  => for prod

Remember:
1. include new models in app.models.__init__.py
2. create public folder in root of project