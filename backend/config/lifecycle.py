import asyncio
from pathlib import Path
from typing import Any

import httpx
from django.conf import settings


class Runtime:
    def __init__(self) -> None:
        self.http_client: httpx.AsyncClient | None = None
        self.turn_admission = asyncio.Semaphore(5)
        self.ready = False

    async def startup(self) -> None:
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=5.0),
            follow_redirects=False,
            trust_env=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        Path(settings.DATA_ROOT).mkdir(parents=True, exist_ok=True)
        self.ready = True

    async def shutdown(self) -> None:
        self.ready = False
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None


runtime = Runtime()


class LifespanApplication:
    def __init__(self, django_application: Any) -> None:
        self.django_application = django_application

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "lifespan":
            await self.django_application(scope, receive, send)
            return
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    await runtime.startup()
                except Exception as exc:
                    await send(
                        {
                            "type": "lifespan.startup.failed",
                            "message": exc.__class__.__name__,
                        }
                    )
                    return
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await runtime.shutdown()
                await send({"type": "lifespan.shutdown.complete"})
                return
