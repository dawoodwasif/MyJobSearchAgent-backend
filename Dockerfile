# 1) Use the official Python 3.8 slim image (now based on Debian 12 “bookworm”)
FROM python:3.8-slim

# avoid any interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# 2) Copy in your list of TeX + font packages
COPY packages.txt /tmp/packages.txt

# 3) Update & install exactly what's in packages.txt (no extra recommends), then clean up
RUN apt-get update \
 && xargs -r -a /tmp/packages.txt apt-get install -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# 4) App setup
WORKDIR /app
COPY . /app

# 5) Install your Python deps
RUN pip install --no-cache-dir -r requirements.txt

# 6) Expose & run
EXPOSE 5000
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
