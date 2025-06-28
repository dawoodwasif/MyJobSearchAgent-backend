# Use Python 3.8 base image
FROM python:3.8-slim-bullseye

# Optional: avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install apt packages
COPY packages.txt /tmp/packages.txt

RUN apt-get update && \
    xargs -a /tmp/packages.txt apt-get install -y && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy app code and install Python dependencies
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port
EXPOSE 5000

# Start Flask app
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
