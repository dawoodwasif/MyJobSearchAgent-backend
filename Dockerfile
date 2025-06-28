# Use full Bullseye (not slim) so texlive-* and font packages are available
FROM python:3.8-bullseye

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# (Re)define APT sources to include main, contrib, and non-free
RUN printf '\
deb http://deb.debian.org/debian bullseye main contrib non-free\n\
deb http://deb.debian.org/debian bullseye-updates main contrib non-free\n\
deb http://security.debian.org/debian-security bullseye-security main contrib non-free\n' \
  > /etc/apt/sources.list

# Bring in your list of TeX + font packages
COPY packages.txt /tmp/packages.txt

# Install exactly what's in packages.txt (no extra recommends), then clean up
RUN apt-get update \
 && xargs -r -a /tmp/packages.txt \
      apt-get install -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# Set working directory for your app
WORKDIR /app

# Copy application code and install Python dependencies
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port
EXPOSE 5000

# Launch the Flask app
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
