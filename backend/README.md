# PDFItDown Backend

Backend API for [PDFItDown](https://pdfitdown.app): handles file-to-PDF conversion, authentication, rate limiting, and observability.

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Redis (for rate limiting)
- An [Axiom](https://axiom.co) account (observability and logging)

### Install & Run

```bash
uv sync
uv run serve
```

The server starts on port `9999`.

### Run with Docker

```bash
docker compose up --build
```

## Testing

```bash
uv run pytest
```

Tests use `pytest` with mocked Redis, logging, and OpenTelemetry spans.

## Linting, formatting and type-checking

```bash
# lint
uv run ruff check
# format
uv run ruff format
# typecheck
uv run ty check src/
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/conversions` | Bearer token | Convert an uploaded file to PDF |
| `GET` | `/health` | — | Health check |

### POST /conversions

**Headers:**
- `Authorization: Bearer <token>` — WorkOS JWT
- `x-user-id` (optional) — for per-user rate limiting

**Form Data:**
- `file` — the file to convert (max 25 MB)
- `file_name` — original filename
- `title` (optional) — PDF document title

**Response:** PDF file stream (`application/octet-stream`)

## Architecture

```
src/backend/
├── api.py       # FastAPI app, routes, conversion logic
├── auth.py      # WorkOS JWT verification
├── limiter.py   # Redis-backed rate limiting
└── exporter.py  # OpenTelemetry tracing setup
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `REDIS_URI` | Redis connection URL for rate limiting |
| `WORKOS_CLIENT_ID` | WorkOS client ID for JWT validation |
| `WORKOS_API_KEY` | WorkOS API key |
| `AXIOM_API_KEY` | Axiom API key for logging & tracing |
| `AXIOM_ENDPOINT_URL` | Axiom edge endpoint |
| `AXIOM_DATASET_NAME` | Axiom dataset for traces |
| `AXIOM_LOGS_COLLECTION` | Axiom dataset for logs |
| `BASE_FRONTEND_URL` | Allowed CORS origin (default: `http://localhost:5174`) |
| `DEVELOPMENT_ENV` | Set to `true` for debug logging |

## Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com)
- **Conversion:** [pdfitdown](https://github.com/AstraBert/PdfItDown) (LibreOffice + ImageMagick pipeline)
- **Auth:** [WorkOS](https://workos.com) (JWT via JWKS)
- **Rate Limiting:** [fastapi-limiter](https://github.com/long2ice/fastapi-limiter) + Redis
- **Observability:** [OpenTelemetry](https://opentelemetry.io) + [Axiom](https://axiom.co)
