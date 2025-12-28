FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies
COPY server/pyproject.toml ./
RUN uv pip install --system -e .

# Copy app
COPY server/src ./src

# Create data directory
RUN mkdir -p /data

EXPOSE 8080

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
