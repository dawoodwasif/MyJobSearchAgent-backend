# Use the slim Python 3.8 image (Debian Bookworm under the hood)
FROM python:3.8-slim

# Avoid any interactive prompts when installing packages
ENV DEBIAN_FRONTEND=noninteractive

# Copy your exact list of TeX + font packages
COPY packages.txt /tmp/packages.txt

# 1) Update the package index
# 2) Normalize line endings in packages.txt (remove CR, if any)
# 3) Install exactly what’s in packages.txt, no recommends
# 4) Clean up apt cache
RUN apt-get update \
 && sed -i 's/\r$//' /tmp/packages.txt \
 && xargs -r -a /tmp/packages.txt \
      apt-get install -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# Set your app directory
WORKDIR /app

# Copy in your code and Python requirements
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose and run
EXPOSE 5000
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
