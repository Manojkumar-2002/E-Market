# Use the official lightweight Python 3.12 image
FROM python:3.12-slim

# Set environment variables to optimize Python inside Docker
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED: Ensures console output is emitted immediately without buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install minimal system dependencies required at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements folder structurally to maintain file paths
COPY requirements/development.txt /app/requirements/development.txt

# Install your exact Python dependencies
RUN pip install --no-cache-dir -r requirements/development.txt

# Copy the rest of your Django project code into the container
COPY . /app/