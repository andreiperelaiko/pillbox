FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

COPY src ./src
COPY run_api.py run_bot.py run_scheduler.py run_mailer.py run_test_seeder.py run_tests.py schema.sql ./

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
