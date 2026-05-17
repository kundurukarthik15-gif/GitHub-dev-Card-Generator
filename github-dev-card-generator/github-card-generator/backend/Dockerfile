FROM python:3.12-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt --system

# Copy source code
COPY . .

# Ensure static directory exists
RUN mkdir -p static/cards

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
