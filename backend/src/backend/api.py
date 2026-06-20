import asyncio
import functools
import logging
import mimetypes
import os
import shutil
import tempfile
import time
import traceback
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import aiofiles
import uvicorn
from axiom_py import Client
from axiom_py.logging import AxiomHandler
from fastapi import Depends, FastAPI, Request
from fastapi.datastructures import UploadFile
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.param_functions import File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_limiter.depends import RateLimiter
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import StatusCode
from pdfitdown.pdfconversion import Converter
from starlette.background import BackgroundTask

from .auth import verify_token
from .exporter import setup_tracing
from .limiter import lifespan

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

app = FastAPI(lifespan=lifespan)


@functools.lru_cache(maxsize=1)
def get_logger() -> logging.Logger:
    client = Client(
        token=os.getenv("AXIOM_API_KEY"),
        edge=os.getenv("AXIOM_ENDPOINT_URL", "").removeprefix("https://"),
    )
    logger = logging.getLogger(__name__)
    if os.getenv("DEVELOPMENT_ENV", "false") == "true":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(
        AxiomHandler(client=client, dataset=os.getenv("AXIOM_LOGS_COLLECTION", ""))
    )
    return logger


@functools.lru_cache(maxsize=1)
def get_converter() -> Converter:
    return Converter()


async def custom_identifier(request: Request) -> str:
    user_id = request.headers.get("x-user-id")
    if user_id:
        return user_id
    ip = (
        request.headers.get(
            "x-forwarded-for", request.client.host if request.client else "0.0.0.0"
        )
        .split(",")[0]
        .strip()
    )
    return ip


@app.post(
    "/conversions",
    dependencies=[
        Depends(verify_token),
        Depends(RateLimiter(times=10, seconds=60, identifier=custom_identifier)),
    ],
)
async def conversions(
    file: UploadFile = File(...),
    file_name: str = Form(...),
    title: str | None = Form(default=None),
) -> StreamingResponse:
    logger = get_logger()
    span = trace.get_current_span()
    request_id = uuid.uuid4()
    span.set_attribute("request_id", str(request_id))
    span.set_attribute("route", "/conversions")
    content = await file.read()
    span.set_attributes(
        {
            "file_type": mimetypes.guess_type(file_name)[0] or "unknown",
            "file_size_kb": round(len(content) / 1024, 3),
        }
    )
    if len(content) > MAX_FILE_SIZE:
        logger.error(
            "Cannot process file larger than 25 MB",
            extra={"request_id": str(request_id)},
        )
        span.set_attribute("success", False)
        span.set_attribute("error_kind", "file_too_large")
        span.set_status(status=StatusCode.ERROR)
        raise HTTPException(
            status_code=422, detail="Cannot process files larger than 25 MB."
        )
    logger.info("Started handling request", extra={"request_id": request_id})
    start = time.time()
    tmp = tempfile.mkdtemp()
    tmp_file = os.path.join(tmp, file_name)
    with open(tmp_file, "wb") as f:
        f.write(content)
    file_write = time.time()
    output_path = Path(tmp_file).with_suffix(".pdf")

    async def cleanup():
        await asyncio.to_thread(shutil.rmtree, tmp, ignore_errors=True)

    logger.debug("Done writing file", extra={"request_id": request_id})
    try:
        converted = get_converter().convert(tmp_file, str(output_path), title)
        conversion = time.time()
        span.set_attributes(
            {
                "write_latency_s": file_write - start,
                "conversion_latency_s": conversion - start,
                "total_lantency_s": (file_write - start) + (conversion - start),
            }
        )
        logger.debug(
            f"write latency: {file_write - start}s; conversion latency: {conversion - start}s; total latency: {(file_write - start) + (conversion - start)}",
            extra={"request_id": request_id},
        )
    except Exception:
        logger.exception("An error occurred", extra={"request_id": request_id})
        stack_trace = traceback.format_exc()
        span.set_attribute("success", False)
        span.set_attribute("error_kind", "conversion_error")
        span.set_attribute("error_trace", stack_trace)
        span.set_status(status=StatusCode.ERROR)
        await cleanup()
        raise HTTPException(
            status_code=500,
            detail=f"Oops, something went wrong on our end! Please contact support with this request ID: {str(request_id)}",
        )
    if converted is not None:
        span.set_attribute("success", True)
        span.set_status(status=StatusCode.OK)

        async def iterfile() -> AsyncGenerator[bytes]:
            async with aiofiles.open(converted, "rb") as f:
                while chunk := await f.read(65536):  # 64KB chunks
                    yield chunk

        logging.info(f"Done in {time.time() - start}s")
        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={Path(converted).name}"
            },
            background=BackgroundTask(cleanup),
        )
    else:
        logger.error("Unsupported file type", extra={"request_id": request_id})
        span.set_attribute("success", False)
        span.set_attribute("error_kind", "unsupported_file")
        span.set_status(status=StatusCode.ERROR)
        await cleanup()
        raise HTTPException(
            status_code=422,
            detail="Unsupported file type for conversion",
        )


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(status_code=200, content={"status": "healthy"})


def main() -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("BASE_FRONTEND_URL", "http://localhost:5174")],
        allow_methods=["POST", "GET"],
        allow_credentials=True,
        allow_headers=["*"],
    )
    setup_tracing()
    FastAPIInstrumentor().instrument_app(app)
    uvicorn.run(app, host="0.0.0.0", port=9999)
