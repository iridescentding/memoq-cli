FROM python:3.11-slim

WORKDIR /app

COPY README.md setup.py ./
COPY memoq_cli ./memoq_cli

RUN pip install --no-cache-dir .

EXPOSE 8088

ENV MEMOQ_CALLBACK_EVENTS_PATH=/data/memoq_callback_events.jsonl

CMD ["memoq", "callback", "serve", "--host", "0.0.0.0", "--port", "8088", "--events-path", "/data/memoq_callback_events.jsonl"]
