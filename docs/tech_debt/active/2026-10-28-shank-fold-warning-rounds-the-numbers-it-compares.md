# The shank-fold warning prints its numbers with :g, so a value near the 0.0001 mm line can read as the wrong side of it

Severity: nice
Status: active
Date: 2026-10-28
Source: plan 07-07 Task 2, found while moving the shank-fold test to `MIN_TAIL_MM` 1e-4
Related files:
- src/screw/calc/__init__.py:203
- src/screw/calc/__init__.py:206
- tests/test_calc.py (`test_a_shank_too_short_to_model_is_folded_into_the_thread_and_warned`)

## Context
The warning that a plain shank is shorter than `MIN_TAIL_MM` formats `thread_length` and the
shank with `:g`, which keeps 6 significant figures. `thread_length` 19.99995 with `length` 20 prints
as 19.9999 or 20 depending on the float, so the text can name a thread_length that does not leave the
shank it quotes. The test avoids it with `length` 5, `thread_length` 4.99995.

## Why it matters
A number the tool prints is a number someone will cut metal to (L02). The warning is about a
sub-micron shank, so the harm is small: the part is built to the full length either way.

## Next step
Print the shank with enough digits to round-trip (`repr`) or name the two inputs and drop the
derived number. Revisit when the warning texts are next touched.
