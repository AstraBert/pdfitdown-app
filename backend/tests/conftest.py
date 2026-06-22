from typing import Any, Literal

from opentelemetry.trace import StatusCode


class RedisMock:
    def __init__(self) -> None:
        pass

    @classmethod
    def from_url(cls, url: str, *args: Any, **kwargs: Any) -> "RedisMock":
        return cls()

    async def evalsha(self, *args: Any, **kwargs: Any) -> float:
        return 0

    async def script_load(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def close(self) -> None:
        pass


class MockSpan:
    def __init__(self) -> None:
        self.attributes: dict[str, Any] = {}
        self.status: Literal["ok", "err", "unset"] = "unset"

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes.update({key: value})

    def set_attributes(self, map: dict[str, Any]) -> None:
        self.attributes.update(**map)

    def set_status(self, status: StatusCode) -> None:
        if status.value == 1:
            self.status = "ok"
        elif status.value == 2:
            self.status = "err"


class MockTrace:
    def __init__(self) -> None:
        self.span = MockSpan()

    def get_current_span(self) -> MockSpan:
        return self.span


class MockLogger:
    def __init__(self) -> None:
        self.logs = {"info": [], "error": [], "exception": [], "debug": []}

    def info(self, message: str, *args: Any, extra: dict[str, Any]) -> None:
        self.logs["info"].append(message)
        assert "request_id" in extra

    def debug(self, message: str, *args: Any, extra: dict[str, Any]) -> None:
        self.logs["debug"].append(message)
        assert "request_id" in extra

    def exception(self, message: str, *args: Any, extra: dict[str, Any]) -> None:
        self.logs["exception"].append(message)
        assert "request_id" in extra

    def error(self, message: str, *args: Any, extra: dict[str, Any]) -> None:
        self.logs["error"].append(message)
        assert "request_id" in extra
