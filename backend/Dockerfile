FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim
WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libtesseract-dev \
    libleptonica-dev \
    libreoffice \
    imagemagick \
    ghostscript \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN uv sync --compile-bytecode --no-dev

CMD ["uv", "run", "serve"]
