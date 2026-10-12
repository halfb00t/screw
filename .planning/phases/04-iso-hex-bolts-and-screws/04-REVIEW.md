---
phase: 04-iso-hex-bolts-and-screws
reviewed: 2026-10-12T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - src/screw/static/style.css
  - tests/test_parity.py
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
---

# Phase 4: Code Review Report (incremental, G-04-5 gap closure)

**Reviewed:** 2026-10-12
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed the diff `e9a7f8d..HEAD` for `src/screw/static/style.css` (three `#dims` rules and a comment)
and `tests/test_parity.py` (`STYLE_CSS`, `INFO_ROW_RULES`, `_css_rules`, `_css_declarations`,
`_info_row_problems`, two tests). `tests/test_parity.py` passes: 30 passed (`.venv/bin/python -m pytest
tests/test_parity.py -q`). I did not run a browser (L01), so the layout claims in the CSS comment are
unchecked here.

The CSS is sound. The row wraps, the label takes half of it, and the value keeps full precision and
drops whole under its label (L02, D-19). Nothing rounds or clips. The weakness is in the source pin
that guards it. It reads rules by exact selector, so a regression written under a more specific
selector passes the gate. I probed this by appending rules to `STYLE_CSS` and calling
`_info_row_problems`; WR-04 lists the probes that returned `[]`.

Prior findings WR-03 (`tests/test_parity.py`, the "rule 17" link test) and IN-05 to IN-08 are
unchanged by this slice. They stay recorded in `04-REVIEW-DISPOSITION.md` under their existing ids.
The slice neither fixes nor worsens them.

## Warnings

### WR-04: The info-row pin matches selectors exactly, so a more specific selector walks past it

**File:** `tests/test_parity.py:157-178` (`_css_declarations`, `_info_row_problems`)
**Issue:** The test exists so that "a revert to the one-line row, a clip or a deleted rule fails the
gate" (comment at `tests/test_parity.py:125`). `_css_declarations(css, "#dims dd")` merges only rules
whose squashed selector is exactly `#dims dd`. Any other selector that reaches the same element is
ignored, and a selector with an extra ancestor has higher specificity, so it wins in the browser. The
only other guards are a `value == "nowrap"` scan and a three-name clip list (`overflow`, `overflow-x`,
`text-overflow`). Each of these appended rules returned `[]` from `_info_row_problems(STYLE_CSS + rule)`:

- `#dims dl div { display: block; }` (the row stops being a flex row)
- `#dims dl dd { white-space: pre; }` (value pinned to one line, `pre` is not `nowrap`)
- `#dims dl dd { width: 4ch; word-break: keep-all; }` (digits no longer wrap or the cell is crushed)
- `#dims dl div > dd { overflow-wrap: normal; }`
- `dd { white-space: nowrap; }` (no `#dims` in the selector, so neither scan looks at it)

So a re-introduced one-line row, the original G-04-5 defect, can pass `make verify` when it is
written in any of these forms. The "has teeth" test only feeds the check the exact old rules, so it
does not see the gap. The clip guard is also name-based: `max-width`, `contain` and `clip-path` are not
in `CLIPS`.

**Fix:** Catch overrides rather than only exact selectors. Cheapest option: reject any rule outside
the four pinned selectors that has a selector containing `#dims` and also targets `div`, `dt` or `dd`,
or any bare `dt`/`dd`/`div` selector, that sets a layout property.
```python
LAYOUT = {"display", "flex", "flex-wrap", "flex-basis", "flex-shrink", "width", "max-width",
          "white-space", "word-break", "overflow-wrap", "contain", "margin", "float", *CLIPS}

def _info_row_problems(css: str) -> list[str]:
    problems = [s for s, want in INFO_ROW_RULES.items() if _css_declarations(css, s) != want]
    for selector, d in _css_rules(css):
        touches = re.search(r"(^|[\s>+~,])(div|dt|dd)\b", selector) and (
            "#dims" in selector or selector in {"div", "dt", "dd"})
        if touches and selector not in INFO_ROW_RULES and LAYOUT & d.keys():
            problems.append(f"override {selector}")
    return problems
```
Add the five probes above to `test_the_info_row_check_has_teeth` so the new guard is itself shown to
catch what it claims to catch, like `_field_literals` is.

## Info

### IN-09: `gap: .75rem` is also a row gap, so a wrapped value sits 10.5 px below its label

**File:** `src/screw/static/style.css:196-197`
**Issue:** `gap` on a wrapping flex container sets both axes. Before this change the row was one line,
so the gap only separated label and value. Now that the row wraps, the same `.75rem` is also the
vertical space between the label's last line and the value that dropped under it. The comment
describes the wrap but not this gap, and the planner's measurement of "at most 4 label lines" does
not say whether it counts it. `INFO_ROW_RULES` pins `gap: .75rem`, so changing it means touching the
pin too.
**Fix:** Use `column-gap: .75rem` (and `row-gap: 0` is the default), or state in the comment that the
vertical gap is intended. Update `INFO_ROW_RULES["#dims div"]` to match.

### IN-10: The docstring of `_info_row_problems` is garbled, and the pin also freezes `#dims dl`

**File:** `tests/test_parity.py:171` and `tests/test_parity.py:127-139`
**Issue:** The docstring says "the four selectors are never read from `css`". The four selectors come
from the `INFO_ROW_RULES` constant. The check reads their declarations from `css`, so the sentence
says the opposite of what the code does. Separately, `INFO_ROW_RULES` pins `#dims dl` exactly
(`minmax(12.5rem, 1fr)`, gaps, margin), a rule this slice did not touch. That is defensible, since the
track width of 200 to 256 px drives the measurement in the CSS comment, but nothing says so. An
unrelated tweak to the grid will fail with the unexplained message `['#dims dl']`.
**Fix:** Reword to "the four selectors come from `INFO_ROW_RULES`, not from `css`". Add one line to
the comment at `tests/test_parity.py:125` saying `#dims dl` is pinned because the measured widths
assume its track sizes.

---

_Reviewed: 2026-10-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
