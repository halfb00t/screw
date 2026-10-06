# syntax=docker/dockerfile:1
# screw: parametric thread and fastener generator. Builds for linux/amd64.
FROM python:3.12-slim-bookworm

# Shared libraries the OpenCascade (cadquery-ocp) and VTK wheels link against.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libx11-6 libexpat1 \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    XDG_CACHE_HOME=/tmp/.cache

WORKDIR /app

# Heavy CAD dependencies first so code changes don't invalidate this layer.
# --no-deps because requirements.txt is the entire pinned closure: that is what lets it
# leave out the ~550 MB of packages cadquery declares but screw never imports (VTK
# viewers, DXF export, the assembly solver, matplotlib). docker/smoke.py below is what
# makes that safe -- it fails the build if the closure is incomplete.
COPY requirements.txt .
RUN pip install --no-deps -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
COPY docker ./docker
RUN pip install --no-deps . \
 && python docker/smoke.py \
 && rm -rf /tmp/.cache

RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin screw
USER 10001

# INTERIM (D-01, D-03): SCREW_WORKERS=1 is spur L17's one server process, with the build
# workers (SCREW_BUILD_WORKERS) carrying the parallelism. Not measured for screw; Phase 7
# re-sweeps (OPER-02).
ENV SCREW_HOST=0.0.0.0 \
    SCREW_PORT=8000 \
    SCREW_WORKERS=1
EXPOSE 8000

# INTERIM (D-01, D-03): interval 30s, timeout 2s, start-period 30s, retries 3 are spur's
# healthcheck. spur measured /api/health's under-load p95 at 0.7-2.3 ms across fourteen
# latency runs on spur's gear service, and kept 2 s because the probe is a fresh Python
# process whose floor is interpreter startup, not the ~1 ms request. Not measured for
# screw; Phase 7 re-sweeps (OPER-02). The inner urlopen timeout (1 s) stays below the
# outer --timeout so a hung request fails the check on its own terms rather than via
# Docker's outer kill.
HEALTHCHECK --interval=30s --timeout=2s --start-period=30s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request as u; u.urlopen('http://127.0.0.1:' + os.environ.get('SCREW_PORT', '8000') + '/api/health', timeout=1)"]

CMD ["screw", "serve"]
