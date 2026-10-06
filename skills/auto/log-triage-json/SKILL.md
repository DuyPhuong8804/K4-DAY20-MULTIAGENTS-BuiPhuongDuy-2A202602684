---
name: log-triage-json
description: Use when parsing application logs into structured JSON error-triage reports.
---
1. Read the required JSON schema and normalization, ordering, and counting rules before parsing logs.
2. Parse each log event and its continuation lines deliberately; preserve exception details and account for repeated-message markers as specified.
3. Normalize service names to lowercase and replace hyphens with underscores.
4. Sort `errors` by service, then by `timestamp_utc`, both ascending.
5. Set the top-level `schema_version` to `2` and `generated_by` to `log-triage`.
6. Validate the output by loading the JSON and checking required fields, normalized names, sort order, and repeat-count totals.
7. Self-check:
   - Are multiline details and repeat counts handled correctly?
   - Are service names normalized and errors sorted by the required keys?
   - Are the required top-level schema fields present with exact values?
=== END===
