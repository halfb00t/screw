# screw -- every command you need to work on this project. `make` lists them.

VENV        ?= .venv
IMAGE       ?= screw:latest
PLATFORM    ?=
PYTEST_ARGS ?=

# cadquery-ocp publishes wheels up to CPython 3.12 and screw supports 3.12 only (L01).
# Choosing the interpreter here instead of a bare `python3` is what stops pip trying to
# build OpenCascade from source against a newer one and failing minutes in.
PYTHON ?= $(shell command -v python3.12 2>/dev/null)

PY    := $(VENV)/bin/python
STAMP := $(VENV)/.installed
# A DOCKER_DEFAULT_PLATFORM in your environment wins unless you set PLATFORM here;
# PLATFORM=linux/arm64 gives a native, much faster image on Apple silicon.
PLATFORM_ARG := $(if $(PLATFORM),--platform $(PLATFORM),)

# requirements.txt is the runtime closure the image installs (L07). Used as a pip
# constraint, a fresh venv gets the same kernel pair as the image and CI. The dev tools
# (ruff, mypy, pytest, ...) are not in it and float (D-17).
CONSTRAINT := $(if $(wildcard requirements.txt),PIP_CONSTRAINT=requirements.txt,)

.DEFAULT_GOAL := help
.PHONY: help venv verify lint typecheck lint-imports no-fake-done test serve lock \
	    check image smoke up down logs vendor vendor-check \
	    worktree.bootstrap worktree.new worktree.land pr.land clean clean-docker

help:  ## list the targets
	@grep -hE '^[a-z][a-z.-]*:.*##' $(MAKEFILE_LIST) | sed 's/:[^#]*##/\t/' | expand -t18

# --- local python ------------------------------------------------------------------

$(STAMP): pyproject.toml $(wildcard requirements.txt)
	@test -n "$(PYTHON)" || { \
	  echo "make: no python3.12 on PATH."; \
	  echo "      cadquery-ocp has no wheels past 3.12 and screw supports 3.12 only (L01)."; \
	  echo "      Install one: brew install python@3.12"; \
	  exit 1; }
	$(PYTHON) -m venv $(VENV)
	$(CONSTRAINT) $(PY) -m pip install --quiet --upgrade pip
	$(CONSTRAINT) $(PY) -m pip install --quiet -e '.[dev]'
	@touch $@

venv: $(STAMP)  ## create .venv with the dev extras, ~1.4 GB of OpenCascade (override with VENV=)

# --- the gate ----------------------------------------------------------------------

# Nothing is done until this passes (L03). Needs no Docker, so it is the one an agent
# runs after every change.
verify: lint typecheck lint-imports no-fake-done test  ## the gate: lint, types, import boundaries, unfinished-work scan, tests

lint: $(STAMP)  ## ruff: correctness rules only, no reformatting (L05)
	$(PY) -m ruff check .

typecheck: $(STAMP)  ## mypy --strict over the package, its tests, the smoke driver and scripts (L04)
	$(PY) -m mypy src tests docker scripts

lint-imports: $(STAMP)  ## the module boundaries declared in pyproject.toml
	$(VENV)/bin/lint-imports

# ':!.../vendor' keeps a future three.js release's own comments from failing our gate:
# the bundle is a build artefact (spur L11), not code we wrote.
#
# -w, not \b: git grep -E on macOS (git 2.54.0, system regex) does not implement \b, so
# a \b-anchored scan matched nothing on the dev host and only CI's Linux git caught
# markers -- proved 2026-10-05 with a staged file containing both TODO and
# NotImplementedError (\b: exit 1 with no output; -w: found). -w is the portable spelling.
#
# The second block: mypy's warn_unused_ignores refuses a stale suppression, but nothing
# refuses a new one. Scoped to src/screw/ so a test may still carry a deliberate,
# code-qualified one.
no-fake-done:  ## refuse unfinished work dressed up as finished
	@if git grep -nwE '(TODO|FIXME|XXX|HACK|NotImplementedError)' \
	     -- '*.py' '*.js' '*.sh' ':!src/screw/static/vendor'; then \
	  echo "make: unfinished-work markers above. Finish it, or file it in docs/tech_debt/."; \
	  exit 1; \
	fi
	@if git grep -nE 'type: ignore' -- 'src/screw/*.py'; then \
	  echo "make: a mypy suppression in src/screw above. Narrow the type, or file it in docs/tech_debt/."; \
	  exit 1; \
	fi

test: $(STAMP)  ## run the test suite
	$(PY) -m pytest $(PYTEST_ARGS)

serve: $(STAMP)  ## run the dev server on http://127.0.0.1:8000
	$(VENV)/bin/screw serve

# --- generated artefacts -----------------------------------------------------------

lock:  ## regenerate requirements.txt, the runtime closure the image installs (resolved in linux/amd64)
	docker/refresh-requirements.sh

check: verify smoke vendor-check  ## everything CI runs, locally (needs Docker)

# --- container ---------------------------------------------------------------------

image:  ## build the container image
	docker build $(PLATFORM_ARG) -t $(IMAGE) .

smoke: image  ## exercise the kernel, both exporters and the ASGI app inside the image
	docker run --rm $(PLATFORM_ARG) --entrypoint python $(IMAGE) docker/smoke.py

up:  ## build, start and wait for the service on http://localhost:8000
	docker compose up -d --build
	@printf 'waiting for the container to report healthy'
	@n=0; until [ "$$(docker compose ps --format '{{.Health}}')" = healthy ]; do \
	   n=$$((n+1)); \
	   if [ $$n -gt 60 ]; then echo ' gave up'; docker compose logs --tail=20; exit 1; fi; \
	   printf '.'; sleep 2; \
	 done
	@echo ' -> http://localhost:8000'

down:  ## stop and remove the service
	docker compose down

logs:  ## follow the service log
	docker compose logs -f

# The committed three.js bundle is a build artefact; these two make it reproducible from
# web/ (spur L11). They need node 22; the gate does not, CI's vendor-bundle job runs the check.
vendor:  ## rebuild the vendored three.js bundle (needs node)
	cd web && npm ci && npm run build

vendor-check:  ## fail if the committed bundle no longer matches web/
	cd web && npm ci --silent && npm run build
	git diff --exit-code -- src/screw/static/vendor

# --- worktrees: isolated, parallel agent work ---------------------------------------

worktree.bootstrap:  ## once per clone: let each worktree keep its own config
	git config extensions.worktreeConfig true

worktree.new:  ## SLUG=<slug> : branch agent/<slug> off HEAD into .claude/worktrees/<slug>
	@test -n "$(SLUG)" || { echo "SLUG= required"; exit 1; }
	@echo "$(SLUG)" | grep -qE '^[a-zA-Z0-9_-]+$$' || { echo "Bad SLUG (alnum/_/- only)"; exit 1; }
	@BASE=$$(git symbolic-ref --short HEAD); \
	git worktree add .claude/worktrees/$(SLUG) -b agent/$(SLUG) $$BASE; \
	git -C .claude/worktrees/$(SLUG) config --worktree worktree.base $$BASE; \
	echo "worktree .claude/worktrees/$(SLUG) on agent/$(SLUG) (base $$BASE)"; \
	echo "run 'make venv' inside it -- do NOT share the main .venv: its editable install"; \
	echo "resolves 'import screw' back to the main checkout, so the suite would silently"; \
	echo "test unmodified code."

worktree.land:  ## SLUG=<slug> MSG="<commit>" : verify, squash-merge, remove the worktree
	@test -n "$(SLUG)" || { echo "SLUG= required"; exit 1; }
	@test -n "$(MSG)" || { echo 'MSG= required'; exit 1; }
	@WT=$$(git rev-parse --show-toplevel)/.claude/worktrees/$(SLUG); \
	test -d "$$WT" || { echo "No worktree at $$WT"; exit 1; }; \
	BASE=$$(git -C $$WT config worktree.base); \
	test -n "$$BASE" || { echo "worktree.base unset; run worktree.bootstrap, then recreate"; exit 1; }; \
	git -C $$WT diff --quiet && git -C $$WT diff --cached --quiet || { echo "Dirty worktree; commit or reset first"; exit 1; }; \
	test "$$(git symbolic-ref --short HEAD)" = "$$BASE" || { echo "Switch the main checkout to $$BASE first"; exit 1; }; \
	LOCK=$$(git rev-parse --git-dir)/worktree-land.lock; \
	until mkdir "$$LOCK" 2>/dev/null; do echo "another land in progress on $$BASE; waiting..."; sleep 1; done; \
	trap 'rmdir "$$LOCK" 2>/dev/null' EXIT; \
	git diff --quiet && git diff --cached --quiet || { echo "Dirty $$BASE; commit or reset first"; exit 1; }; \
	: "reset --hard HEAD is safe here: the base was just verified clean under the lock, so it only discards the failed squash (which leaves no MERGE_HEAD to abort)"; \
	git merge --squash agent/$(SLUG) || { git reset --hard HEAD; echo "CONFLICT - resolve in the worktree, then retry"; exit 1; }; \
	$(MAKE) verify || { git reset --hard HEAD; echo "verify failed on the merged result; not landing"; exit 1; }; \
	git commit -m "$(MSG)"; \
	git worktree remove --force $$WT; \
	git branch -D agent/$(SLUG); \
	echo "landed agent/$(SLUG) on $$BASE"

# --- landing on main: the merge gate (L08) ------------------------------------------

pr.land: $(STAMP)  ## PR=<n> : squash-merge a PR only if its head is green and current with main
	@test -n "$(PR)" || { echo "PR= required"; exit 1; }
	$(PY) -m scripts.pr_land $(PR)

# --- cleanup -----------------------------------------------------------------------

clean:  ## remove the venvs, caches and exported models
	rm -rf $(VENV) .pytest_cache .ruff_cache .mypy_cache .import_linter_cache build dist
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.egg-info' -type d -prune -exec rm -rf {} +
	rm -f *.stl *.step *.stp

clean-docker:  ## remove this project's container and image
	-docker compose down --remove-orphans
	-docker image rm $(IMAGE)
