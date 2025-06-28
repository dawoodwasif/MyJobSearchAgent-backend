# 1. Use the full Bullseye variant so all texlive-* and fonts-* metas live in main
FROM python:3.8-bullseye

# 2. Avoid any interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# 3. Bring in your TeX + font package list
COPY packages.txt /tmp/packages.txt

# 4. Update, install exactly what's in packages.txt (no extra recommends), then clean up
RUN apt-get update \
 && xargs -r -a /tmp/packages.txt \
      apt-get install -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# 5. Set up your Flask app
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# 6. Expose & run
EXPOSE 5000
CMD ["flask","--app","app","run","--host=0.0.0.0","--port=5000"]
