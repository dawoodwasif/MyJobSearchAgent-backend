# Use the *full* Python 3.8 image (Debian Bookworm) instead of the slim variant
FROM python:3.8

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Copy in your list of TeX + font packages
COPY packages.txt /tmp/packages.txt

# Update & install exactly what's in packages.txt (no extra recommends), then clean up
RUN apt-get update \
 && xargs -r -a /tmp/packages.txt \
      apt-get install -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy your code and install Python dependencies
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port & start the app
EXPOSE 5000
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
