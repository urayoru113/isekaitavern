FROM python:3.13-slim

RUN apt-get update && apt-get install --no-install-recommends -y git curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen --no-install-project

COPY . .

RUN uv sync --frozen --no-dev

CMD ["uv", "run", "main.py"]
