# Use the official lightweight Python 3.12 image
FROM python:3.12-slim

# Set environment variables to optimize Python inside Docker
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED: Ensures console output is emitted immediately without buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (curl + WeasyPrint graphical libraries + fonts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-noto \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements folder structurally to maintain file paths
COPY requirements/development.txt /app/requirements/development.txt

# Install your exact Python dependencies
# MAKE SURE 'weasyprint' IS LISTED IN THIS TXT FILE!
RUN pip install --no-cache-dir -r requirements/development.txt

# Copy the rest of your Django project code into the container
COPY . /app/