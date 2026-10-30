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

# SCREW_WORKERS=1 (R24): one server process, the build workers (SCREW_BUILD_WORKERS)
# carrying the parallelism. /api/health's p95 under load at the picked N was
# 0.00935187669999209 s, inside the probe's 1 s urlopen timeout (load run 40909724292).
ENV SCREW_HOST=0.0.0.0 \
    SCREW_PORT=8000 \
    SCREW_WORKERS=1
EXPOSE 8000

# R25, over the 5 load readings at the picked N (load run 40909724292, G18):
# --timeout=2s is ceil(2 x the max wall of this HEALTHCHECK command, 0.7360738640000477 s,
# over 276 walls with no non-zero exit); --start-period=10s is 2 x the max time to the first
# healthy response, 0.9576668719999759 s, rounded up to 10 s. --interval=30s and --retries=3
# are Docker's documented defaults (docs.docker.com, Dockerfile reference, HEALTHCHECK), not
# measured. The probe is a fresh Python process, so its wall is interpreter startup, not the
# request. The inner urlopen timeout (1 s) stays below the outer --timeout so a hung
# request fails the check on its own terms rather than via Docker's outer kill.
HEALTHCHECK --interval=30s --timeout=2s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request as u; u.urlopen('http://127.0.0.1:' + os.environ.get('SCREW_PORT', '8000') + '/api/health', timeout=1)"]

CMD ["screw", "serve"]
