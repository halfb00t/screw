# `solid.build` hands a CadQuery solid to bench and tests

Severity: nice
Status: active
Date: 2026-11-03
Source: v1.0 milestone audit (INT-04); 08-CONTEXT.md Deferred Ideas
Related files:
- src/screw/solid/__init__.py:288-291

## Context
`solid.build` returns a `cq.Solid` outside `screw.solid`, which breaks the rule that vendor types
stop at their boundary (CLAUDE.md). Its docstring limits it to tests and `bench/`, and the app, the
CLI and the pool never call it. No import contract checks a return type, so nothing holds the
docstring.

## Why it matters
A caller outside `bench/` and `tests/` would take a kernel object across the boundary without any
check failing.

## Next step
A kernel-free handle, or an import-linter or test rule that only `bench/` and `tests/` call it.
Revisit when a caller appears outside `bench/` and `tests/`, or at the next change to the import
contracts. Not fixed in Phase 8.
