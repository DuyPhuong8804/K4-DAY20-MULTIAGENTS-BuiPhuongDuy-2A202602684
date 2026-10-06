---
name: typed-package-bugfixes
description: Use when fixing bugs in a typed Python package with repository-level testing and changelog requirements.
---
1. Read the repository instructions and reviewer requirements before editing; turn each into a checklist item.
2. Inspect the affected code and identify each distinct bug before changing behavior.
3. Add type annotations to every parameter and return value of each public function you add or modify.
4. Add `tests/test_regressions.py` with a separate test for each fixed bug; include at least three tests when required.
5. Add a bullet for each fix under `## Unreleased` in `CHANGELOG.md`, using `- fix(<function name>): <short description>`.
6. Run the required tests, including the regression tests, after all edits.
7. Inspect the changed files directly if a preferred diff tool is unavailable.
8. Self-check:
   - Are all public functions fully annotated?
   - Is there a regression test and changelog bullet for every fix?
   - Do the required tests pass?
