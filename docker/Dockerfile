FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies as a separate layer so they cache across source changes
COPY pyproject.toml .
RUN uv pip install --system --no-cache .

COPY . .

EXPOSE 8002

CMD ["python", "run.py"]
