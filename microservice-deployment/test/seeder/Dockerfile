FROM python:3.12-slim

RUN pip install --no-cache-dir requests

COPY microservice-deployment/test/seeder/seed.py /seed.py

CMD ["python", "/seed.py"]
