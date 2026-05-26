FROM python:3.12-slim

WORKDIR /app

COPY smtp_bridge/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY smtp_bridge/server.py .

EXPOSE 8080 2525

CMD ["python", "server.py"]
