Repeats: mini-run1, mini-run2, mini-run3 (3 per cell). Scores = share of checks passed.

### Mean score over the evaluation tasks, per repeat

| condition | mini-run1 | mini-run2 | mini-run3 | mean | min-max | sd | main run (other model) |
|---|---|---|---|---|---|---|---|
| baseline | 0.06 | 0.06 | 0.14 | 0.09 | 0.06-0.14 | 0.04 | 0.60 |
| subagents | 0.16 | 0.18 | 0.16 | 0.17 | 0.16-0.18 | 0.01 | 0.39 |
| skills-auto | 0.06 | 0.17 | 0.21 | 0.15 | 0.06-0.21 | 0.06 | 0.76 |

### Per task: passed/total in each repeat, and mean score

| task | condition | mini-run1 | mini-run2 | mini-run3 | mean | main run |
|---|---|---|---|---|---|---|
| code-eval | baseline | 1/11 | 2/11 | 1/11 | 0.12 | 7/11 |
| code-eval | subagents | 3/11 | 5/11 | 3/11 | 0.33 | 7/11 |
| code-eval | skills-auto | 1/11 | 1/11 | 2/11 | 0.12 | 9/11 |
| data-eval | baseline | 0/9 | 0/9 | 2/9 | 0.07 | 5/9 |
| data-eval | subagents | 0/9 | 0/9 | 1/9 | 0.04 | 4/9 |
| data-eval | skills-auto | 0/9 | 3/9 | 3/9 | 0.22 | 5/9 |
| logs-eval | baseline | 1/10 | 0/10 | 1/10 | 0.07 | 6/10 |
| logs-eval | subagents | 2/10 | 1/10 | 1/10 | 0.13 | 1/10 |
| logs-eval | skills-auto | 1/10 | 1/10 | 1/10 | 0.10 | 9/10 |

### Cost and behaviour (mean per run)

| condition | tokens (repeats) | tokens (main) | tool calls | subagent calls | runs reading a skill | runs with error |
|---|---|---|---|---|---|---|
| baseline | 75,519 | 40,597 | 10.6 | 0.0 | 0/9 | 1/9 |
| subagents | 139,915 | 134,483 | 10.6 | 0.1 | 0/9 | 1/9 |
| skills-auto | 59,451 | 63,285 | 9.7 | 0.0 | 0/9 | 0/9 |
