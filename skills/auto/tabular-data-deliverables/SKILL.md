---
name: tabular-data-deliverables
description: Use when cleaning order-like CSV data and producing structured summaries or cleaned-data artifacts.
---
1. Read the output requirements first; record each filename, field, type, unit, row rule, and ordering rule.
2. Parse monetary values with decimal arithmetic; convert to integer cents wherever cents are required, and avoid floating-point totals.
3. Count input data rows with duplicates included; deduplicate according to the specified key before computing distinct-order results.
4. Exclude rows with unknown amounts wherever the requirements call for known amounts, and apply the same rule consistently to summaries and cleaned output.
5. Write `answer.json` with a `meta` object containing `source`, `rows_in`, and `rows_used`; use the specified meanings for each field.
6. Write `clean.csv` with header order `order_id,timestamp_utc,region,amount_cents`; include one row per distinct order with a known amount.
7. Format cleaned timestamps as `YYYY-MM-DDTHH:MM:SSZ` in UTC and regions using the required canonical spelling.
8. Validate the generated files by parsing them and checking their schemas, row counts, units, and deduplication rules.
9. Self-check:
   - Are currency values represented in the required unit without float errors?
   - Do metadata and cleaned rows follow the specified counting rules?
   - Do filenames, keys, headers, and formats match exactly?
