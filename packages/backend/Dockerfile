# Use Python 3.13 slim as the base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry==1.8.2

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy project files
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Start the FastAPI application with hot reload for development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]