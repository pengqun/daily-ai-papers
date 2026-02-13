FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source first so hatchling can find the package, then install
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "daily_ai_papers.main:app", "--host", "0.0.0.0", "--port", "8000"]
