FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

COPY app/ /app/

EXPOSE 19132/udp
EXPOSE 19132/tcp
EXPOSE 8090

CMD ["python", "/app/main.py"]
