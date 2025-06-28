### 1) Builder: install TeX Live, build PDF
FROM ubuntu:22.04 AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      texlive-latex-base texlive-latex-recommended texlive-xetex latexmk \
      cm-super \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . /src
RUN latexmk -pdf -silent main.tex   # <-- adjust to your .tex filename

### 2) Runtime: tiny Flask image with just the PDF + Python
FROM python:3.8-slim

WORKDIR /app
COPY --from=builder /src/main.pdf /app/

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app   # your Flask code if it needs to read templates etc.

EXPOSE 5000
CMD ["flask","--app","app","run","--host=0.0.0.0","--port=5000"]
