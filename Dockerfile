#########################
# 1) BUILDER: Ubuntu + TeX Live
#########################
FROM ubuntu:22.04 AS tex-builder

# avoid prompts, install only what you list
ENV DEBIAN_FRONTEND=noninteractive

# copy your exact packages list
COPY packages.txt /tmp/packages.txt

# install TeX Live + fonts
RUN apt-get update \
 && xargs -r -a /tmp/packages.txt \
      apt-get install -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# copy in your .tex sources
WORKDIR /src
COPY . /src

# build all .tex files to PDF (adjust the command to your filenames)
RUN for f in *.tex; do \
      pdflatex -interaction=batchmode "$f"; \
    done

#########################
# 2) RUNTIME: slim Python + PDFs
#########################
FROM python:3.8-slim

WORKDIR /app

# copy only the generated PDFs from the builder
COPY --from=tex-builder /src/*.pdf /app/

# now bring in your Flask app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5000
CMD ["flask","--app","app","run","--host=0.0.0.0","--port=5000"]
