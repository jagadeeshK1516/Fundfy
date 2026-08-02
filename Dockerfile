FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "." && pip install --no-cache-dir uvicorn[standard]

# Copy application code
COPY fundfy/ ./fundfy/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create generated files directory
RUN mkdir -p /app/generated_files

EXPOSE 8000

CMD ["uvicorn", "fundfy.main:app", "--host", "0.0.0.0", "--port", "8000"]
