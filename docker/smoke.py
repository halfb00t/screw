"""End-to-end smoke test: prove the CAD kernel, the exporters and the HTTP app all work.

Ported from spur's build-time smoke test. It drives the ASGI app straight through its
lifespan with raw ASGI messages and nothing that isn't already in the image: no HTTP client
is needed. A request for a model spawns a real build worker, so a pass proves the kernel,
the STL and STEP exporters, the process pool and the validation layer in one run.
"""

from __future__ import annotations

import anyio
from starlette.types import Message

from screw.app import app


async def get(path: str, query: bytes = b"") -> tuple[int, bytes]:
    """One GET straight through the ASGI app; there is no HTTP test client here."""
    status: int | None = None
    body = bytearray()
    pending = [{"type": "http.request", "body": b"", "more_body": False}]

    async def receive() -> Message:
        return pending.pop(0) if pending else {"type": "http.disconnect"}

    # Message is the type app.__call__ itself declares (starlette.types.ASGIApp's Send
    # parameter) -- using the library's own alias here needs no cast, and an untyped value
    # inside it is not written in our code (L04).
    async def send(message: Message) -> None:
        nonlocal status
        if message["type"] == "http.response.start":
            status = message["status"]
        elif message["type"] == "http.response.body":
            body.extend(message.get("body", b""))

    await app({
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": query,
        "root_path": "", "headers": [(b"host", b"smoke")],
        "client": ("127.0.0.1", 0), "server": ("smoke", 80),
    }, receive, send)
    assert status is not None, f"{path}: the app never responded"
    return status, bytes(body)


async def main() -> None:
    # The build pool starts in app.py's `lifespan`, which only runs under a real ASGI
    # server or a lifespan-aware client -- calling `app(...)` raw, as this script does,
    # never triggers it on its own. `/api/bolt/model.{stl,step}` needs a started pool
    # (build_backend() hard-fails otherwise, by design), so this smoke test drives the
    # lifespan itself via Starlette's own `router.lifespan_context`, the same callable a
    # real ASGI server invokes.
    async with app.router.lifespan_context(app):
        for path, query in (("/api/health", b""), ("/api/kinds", b""),
                            ("/api/schema", b"kind=bolt"), ("/api/bolt/info", b"")):
            status, _ = await get(path, query)
            assert status == 200, f"{path} -> {status}"

        status, stl = await get("/api/bolt/model.stl", b"quality=preview")
        assert status == 200, f"stl -> {status}"
        assert len(stl) > 1000, f"stl -> only {len(stl)} bytes"

        status, step = await get("/api/bolt/model.step")
        assert status == 200, f"step -> {status}"
        assert step.startswith(b"ISO-10303-21;"), "step -> not an ISO-10303-21 file"

        status, _ = await get("/api/bolt/info", b"m=5")
        assert status == 422, f"foreign field -> {status}, expected 422"

        status, _ = await get("/api/schema", b"kind=nut")
        assert status == 404, f"unknown kind -> {status}, expected 404"

    print("smoke: kernel, exports, ASGI stack and validation all live")


if __name__ == "__main__":
    # Required because /api/bolt/model.{stl,step} spawns a worker process (mp_context
    # "spawn", pool.py): spawn re-imports this module as __main__ in the child to bootstrap
    # it, and an unguarded module-level anyio.run(main) call would re-run this entire
    # script inside that child -- the recursive relaunch multiprocessing's own "Safe
    # importing of main module" guidance (and its RuntimeError when violated) warns about.
    anyio.run(main)
