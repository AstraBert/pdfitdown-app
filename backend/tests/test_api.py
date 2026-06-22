import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api import app
from backend.auth import verify_token

from .conftest import MockLogger, MockTrace, RedisMock


@pytest.fixture()
def authenticated_client() -> Generator[TestClient]:
    app.dependency_overrides[verify_token] = lambda: {"user": "user"}
    with patch("backend.limiter.Redis", new=RedisMock):
        with TestClient(app=app) as client:
            yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def client() -> Generator[TestClient]:
    with patch("backend.limiter.Redis", new=RedisMock):
        with TestClient(app=app) as client:
            yield client


@pytest.mark.parametrize(
    ("input_file", "mime_type"),
    [
        (
            "tests/data/test.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("tests/data/test.png", "image/png"),
        ("tests/data/test.txt", "text/plain"),
        ("tests/data/test.zip", "application/zip"),
    ],
)
def test_conversion(
    authenticated_client: TestClient, input_file: str, mime_type: str
) -> None:
    logger = MockLogger()
    with patch("backend.api.get_logger", new=Mock(side_effect=lambda: logger)):
        fl_name = os.path.basename(input_file)
        expected_filename = Path(fl_name).with_suffix(".pdf").name

        with open(input_file, "rb") as f:
            response = authenticated_client.post(
                "/conversions",
                files={"file": (fl_name, f, mime_type)},
                data={"file_name": fl_name},
                headers={"x-user-id": "user-1"},
            )

        assert response.status_code == 200
        assert "application/octet-stream" in response.headers.get("Content-Type", "")
        assert (
            response.headers.get("Content-Disposition")
            == f"attachment; filename={expected_filename}"
        )
        assert response.content[:4] == b"%PDF"
        assert len(logger.logs["info"]) == 2
        assert logger.logs["info"][0] == "Started handling request"
        assert logger.logs["info"][1].startswith("Done in")
        assert len(logger.logs["debug"]) == 2
        assert logger.logs["debug"][0] == "Done writing file"
        assert logger.logs["debug"][1].startswith("write latency:")
        assert len(logger.logs["error"]) == 0
        assert len(logger.logs["exception"]) == 0


def test_no_auth(client: TestClient) -> None:
    with patch("backend.api.get_logger", new=Mock(side_effect=lambda: MockLogger())):
        fl_name = os.path.basename("tests/data/test.txt")

        with open("tests/data/test.txt", "rb") as f:
            response = client.post(
                "/conversions",
                files={"file": (fl_name, f, "text/plain")},
                data={"file_name": fl_name},
            )
            assert response.status_code == 401


def test_unsupported(authenticated_client: TestClient) -> None:
    logger = MockLogger()
    with patch("backend.api.get_logger", new=Mock(side_effect=lambda: logger)):
        fl_name = os.path.basename("tests/data/test.ico")

        with open("tests/data/test.ico", "rb") as f:
            response = authenticated_client.post(
                "/conversions",
                files={"file": (fl_name, f, "image/vnd.microsoft.icon")},
                data={"file_name": fl_name},
                headers={"x-user-id": "user-1"},
            )

        assert response.status_code == 422
        assert response.json() == {"detail": "Unsupported file type for conversion"}
        assert len(logger.logs["error"]) == 1
        assert logger.logs["error"][0] == "Unsupported file type"
        assert len(logger.logs["info"]) == 1
        assert logger.logs["info"][0] == "Started handling request"
        assert len(logger.logs["debug"]) == 2
        assert logger.logs["debug"][0] == "Done writing file"
        assert logger.logs["debug"][1].startswith("write latency:")
        assert len(logger.logs["exception"]) == 0


def test_too_large(authenticated_client: TestClient) -> None:
    logger = MockLogger()
    with patch("backend.api.get_logger", new=Mock(side_effect=lambda: logger)):
        fl_name = "large.png"
        to_write = b"b" * 30 * 1024 * 1024
        with open(f"tests/data/{fl_name}", "wb") as f:
            f.write(to_write)

        with open("tests/data/large.png", "rb") as f:
            response = authenticated_client.post(
                "/conversions",
                files={"file": (fl_name, f, "image/png")},
                data={"file_name": fl_name},
                headers={"x-user-id": "user-1"},
            )

        assert response.status_code == 422
        assert response.json() == {"detail": "Cannot process files larger than 25 MB."}
        assert len(logger.logs["error"]) == 1
        assert logger.logs["error"][0] == "Cannot process file larger than 25 MB"
        assert len(logger.logs["info"]) == 0
        assert len(logger.logs["debug"]) == 0
        assert len(logger.logs["exception"]) == 0
        os.remove(f"tests/data/{fl_name}")


def test_exception(authenticated_client: TestClient) -> None:
    logger = MockLogger()
    with patch("backend.api.get_logger", new=Mock(side_effect=lambda: logger)):
        fl_name = "invalid.png"
        to_write = b"this is not an image"
        with open(f"tests/data/{fl_name}", "wb") as f:
            f.write(to_write)

        with open(f"tests/data/{fl_name}", "rb") as f:
            response = authenticated_client.post(
                "/conversions",
                files={"file": (fl_name, f, "image/png")},
                data={"file_name": fl_name},
                headers={"x-user-id": "user-1"},
            )

        assert response.status_code == 500
        assert response.json()["detail"].startswith(
            "Oops, something went wrong on our end! Please contact support with this request ID:"
        )
        assert len(logger.logs["exception"]) == 1
        assert logger.logs["exception"][0] == "An error occurred"
        os.remove(f"tests/data/{fl_name}")


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_otel_span_attributes(authenticated_client: TestClient) -> None:
    logger = MockLogger()
    with (
        patch("backend.api.get_logger", new=Mock(side_effect=lambda: logger)) as _,
        patch("backend.api.trace", new_callable=MockTrace) as trace,
    ):
        fl_name = os.path.basename("tests/data/test.txt")

        with open("tests/data/test.txt", "rb") as f:
            response = authenticated_client.post(
                "/conversions",
                files={"file": (fl_name, f, "text/plain")},
                data={"file_name": fl_name},
            )
            assert response.status_code == 200
            span = trace.span
            keys = (
                "request_id",
                "route",
                "file_type",
                "file_size_kb",
                "write_latency_s",
                "conversion_latency_s",
                "total_latency_s",
                "success",
            )
            for k in keys:
                assert k in span.attributes
            assert span.status == "ok"
            assert len(logger.logs["info"]) == 2
            assert logger.logs["info"][0] == "Started handling request"
            assert logger.logs["info"][1].startswith("Done in")
            assert len(logger.logs["debug"]) == 2
            assert logger.logs["debug"][0] == "Done writing file"
            assert logger.logs["debug"][1].startswith("write latency:")
            assert len(logger.logs["error"]) == 0
            assert len(logger.logs["exception"]) == 0


def test_otel_span_attributes_with_errors(authenticated_client: TestClient) -> None:
    with (
        patch(
            "backend.api.get_logger", new=Mock(side_effect=lambda: MockLogger())
        ) as _,
        patch("backend.api.trace", new_callable=MockTrace) as trace,
    ):
        fl_name = "large.png"
        to_write = b"b" * 30 * 1024 * 1024
        with open(f"tests/data/{fl_name}", "wb") as f:
            f.write(to_write)

        with open("tests/data/large.png", "rb") as f:
            response = authenticated_client.post(
                "/conversions",
                files={"file": (fl_name, f, "image/png")},
                data={"file_name": fl_name},
                headers={"x-user-id": "user-1"},
            )

        assert response.status_code == 422

        span = trace.span
        keys = ("request_id", "route", "file_type", "success", "error_kind")
        for k in keys:
            assert k in span.attributes
        assert span.status == "err"

        os.remove(f"tests/data/{fl_name}")
