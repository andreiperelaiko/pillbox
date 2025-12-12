FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock ./
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:${PATH}"
COPY src ./src
COPY run_api.py ./
CMD ["python", "run_api.py"]
