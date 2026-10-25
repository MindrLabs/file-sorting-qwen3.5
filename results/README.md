# Results

The per-folder numbers behind every table and summary number in the README, and the scripts that recompute them with 95% intervals and paired tests.

```
python3 scripts/report_tables.py              # every table, the summary, the primary comparisons, sensitivity
python3 scripts/report_tables.py primary 5 7  # chosen sections (summary, primary, folders, 1-9, sections, desktop, sensitivity, undo)
python3 -B tests/test_report_tables.py        # the README's headline numbers, checked against these files
python3 -B tests/test_stats.py                # the statistics, checked against known values
```

Python 3.12 standard library only. Nothing here starts a model.

## What a line file holds

- One file per README line or condition, one row per folder. Every run was made once per folder; on one machine the same input gives the same output.
- Columns, in this order: `line, folder`, then the scalar keys of the benchmark's `quality` record in the order the benchmark stored them, then `gen_sec, peak_mb, first_plan_sha256`. Another tool writes re-measurements in the same format, so a re-run can be compared row by row.
- `folder` is a label only: `v2-01`…`v2-20` for the 20 sealed folders, `dev-01`…`dev-12` for the dev folders, and `downloads` or `desktop` for one aggregate row per run on a real folder. No file name, project name, answer or plan text is published.
- `first_plan_sha256` is the SHA-256 of the first plan's text (the plan before any human edit). Equal hashes mean byte-identical plans; that is how the sensitivity checks below compare machines and context lengths.
- Keys the README uses: `usable` (the first plan could be approved after fixing at most one line in five, moved at least 60% of the labelled files, touched no organized folder and stopped), `wrong_share` (lines to fix ÷ plan lines), `pair_f1` (pairs of same-project files placed together, 0-1), `pair_precision`, `coverage` (labelled files moved), `usable_10` and `usable_30` (the same verdict at 10% and 30%). Baseline files carry the five keys the baseline scorer kept.

## Other files

| File | What it holds |
|---|---|
| `provenance.csv` | One row per line: spec id, machine, flow, menu, model repo, GGUF file and size, checkpoint revision, context, model-compose version and origin (PyPI or a fork, named by folder and commit), compose file hash, scorer, start time, swap before and after (Mac), jobs, runs that did not complete, and the SHA-256 of the benchmark results file the line was exported from |
| `first-plan-breakdown.csv` | Counts computed from each first plan and the private answer key: labelled files, right folder, wrong folder, not moved, files that should stay and how many were moved, and the picking and leaving-alone shares of Table 6. "Right folder" is the folder named exactly as the file's project, so it is filled in only when the person gave the names |
| `undo-check.csv` | Every results file of the project (166): runs, runs whose files were all back in place after undo, and runs that failed before an undo check |

The export that writes these files reads the private benchmark results and answer keys, so it is not shipped. It refuses to write a file that contains any answer-key file name.

## Statistics

- **A share of folders** (usable 19/20) carries a Wilson 95% interval.
- **A mean over folders** and **a difference between two lines on the same folders** carry a folder-bootstrap 95% interval: folders are resampled, 2,000 draws, seed 20261022, the analysis registered before the sealed folders were scored. A pair-F1 difference is *different* when its interval leaves out zero, *equivalent* when the whole interval sits inside ±0.05, and *undecided* otherwise.
- **Usable on the same 20 sealed folders** is compared with an exact McNemar test (two-sided binomial over the folders where the two lines disagree).
- **The primary family** is fixed in `scripts/comparisons.py` (`PRIMARY`) and Holm-corrected together: names + about against the model's own list for 0.8B, 2B, 4B, 9B, 2B Q4_K_M and 4B Q4_K_M; 9B Q4_K_M against TF-IDF; four asks against one ask for 9B Q4_K_M. Everything else is reported as a descriptive comparison. Dev folders were used to tune the flow, so their tests are descriptive.
- **What the intervals cover:** variation across folders like these. They do not cover reruns (none were needed on one machine), another machine, another llama.cpp or model-compose build, or other kinds of folders. A real folder is one folder and one run, so no interval is claimed for it.

## Sensitivity

- **Context 8K vs 65K** (dev folders, RTX 4090): the first plans of 2B, 4B and 9B Q4_K_M are byte-identical in 12 of 12 folders each, so the 8K memory numbers stand for the 65K results.
- **RTX 4090 vs 16GB Mac** (dev-01…04, 8K, same model file and settings; the llama.cpp and model-compose builds differ, and for four asks the compose file revision too): one ask, 9B first plans identical in 2 of 4 folders and 2B in 0 of 4; on the Mac 9B was usable in 4 of 4 and 2B in 1 of 4. Four asks, 9B: identical in 3 of 4 folders, usable 4 of 4 on the Mac. Swap did not grow during the Mac runs (four asks: 0 before and after).
- **model-compose origin:** the real-downloads four-ask run used model-compose 0.4.120 from PyPI; every other line used a fork of 0.4.120 (`provenance.csv`). No PyPI-against-fork comparison of first plans is recorded in this folder.

## Index: which file backs which claim

Codes: T1-T9 = the tables `scripts/report_tables.py` prints (Table 1-9 there; in the README, T1 = table 1, T2 and T3 = tables 2 and 11, T4 = tables 3 and 8, T5 = table 4, T6 = tables 5 and 9, T7 = table 6, T8 = table 7, T9 = table 10), S1-S8 = summary items, 3.1/3.3/3.6 = README sections, P = primary family, X = context sensitivity, M = machine sensitivity, FAQ = the TF-IDF, 2B and agent-list-rule answers.

| File | Model | Flow | Menu | Context | Machine | Rows | Backs |
|---|---|---|---|---|---|---|---|
| `sealed-0.8b-q8-model-list.csv` | 0.8B Q8_0 | one ask | model list | 65K | RTX 4090 | 20 | T4, 3.1, P |
| `sealed-2b-q8-model-list.csv` | 2B Q8_0 | one ask | model list | 65K | RTX 4090 | 20 | T4, 3.1, 3.6, P, S1 |
| `sealed-4b-q8-model-list.csv` | 4B Q8_0 | one ask | model list | 65K | RTX 4090 | 20 | T4, 3.1, 3.6, P, S1 |
| `sealed-9b-q8-model-list.csv` | 9B Q8_0 | one ask | model list | 65K | RTX 4090 | 20 | T4, 3.1, 3.6, P, S1 |
| `sealed-2b-q4km-model-list.csv` | 2B Q4_K_M | one ask | model list | 65K | RTX 4090 | 20 | T4, 3.1, P |
| `sealed-4b-q4km-model-list.csv` | 4B Q4_K_M | one ask | model list | 65K | RTX 4090 | 20 | T4, 3.1, P |
| `sealed-4b-q2kxl-model-list.csv` | 4B UD-Q2_K_XL | one ask | model list | 65K | RTX 4090 | 20 | 3.1 |
| `sealed-2b-q8-names.csv` | 2B Q8_0 | one ask | names | 65K | RTX 4090 | 20 | T4, 3.1, S2 |
| `sealed-4b-q8-names.csv` | 4B Q8_0 | one ask | names | 65K | RTX 4090 | 20 | T4, 3.1 |
| `sealed-0.8b-q8-names-about.csv` | 0.8B Q8_0 | one ask | names + about | 65K | RTX 4090 | 20 | T4, T6, 3.1, P |
| `sealed-2b-q8-names-about.csv` | 2B Q8_0 | one ask | names + about | 65K | RTX 4090 | 20 | T4, T6, T9, 3.1, P, S2, FAQ |
| `sealed-4b-q8-names-about.csv` | 4B Q8_0 | one ask | names + about | 65K | RTX 4090 | 20 | T4, T6, T9, 3.1, P, S6, FAQ |
| `sealed-9b-q8-names-about.csv` | 9B Q8_0 | one ask | names + about | 65K | RTX 4090 | 20 | T4, T6, T9, 3.1, P, S6, FAQ |
| `sealed-2b-q4km-names-about.csv` | 2B Q4_K_M | one ask | names + about | 65K | RTX 4090 | 20 | T1, T4, T6, T9, 3.1, P |
| `sealed-4b-q4km-names-about.csv` | 4B Q4_K_M | one ask | names + about | 65K | RTX 4090 | 20 | T4, T9, 3.1, P |
| `sealed-4b-q2kxl-names-about.csv` | 4B UD-Q2_K_XL | one ask | names + about | 65K | RTX 4090 | 20 | T4, T9, 3.1 |
| `sealed-9b-q4km-names-about.csv` | 9B Q4_K_M | one ask | names + about | 65K | RTX 4090 | 20 | T1, T4, T5, T6, T9, P, S1, S3, S7 |
| `sealed-9b-q4km-names-about-vote.csv` | 9B Q4_K_M | four asks | names + about | 65K | RTX 4090 | 20 | T1, T3, T5, P, S3 |
| `sealed-2b-q8-tool-agent.csv` | 2B Q8_0 | tool agent | model list | 65K | RTX 4090 | 20 | T9, 3.6 |
| `sealed-4b-q8-tool-agent.csv` | 4B Q8_0 | tool agent | model list | 65K | RTX 4090 | 20 | T9, 3.6 |
| `sealed-9b-q8-tool-agent.csv` | 9B Q8_0 | tool agent | model list | 65K | RTX 4090 | 20 | 3.6 |
| `sealed-2b-q4km-tool-agent.csv` | 2B Q4_K_M | tool agent | model list | 65K | RTX 4090 | 20 | T9 |
| `sealed-4b-q4km-tool-agent.csv` | 4B Q4_K_M | tool agent | model list | 65K | RTX 4090 | 19 | T9 (v2-03 timed out after 1,800s and has no row) |
| `sealed-4b-q2kxl-tool-agent.csv` | 4B UD-Q2_K_XL | tool agent | model list | 65K | RTX 4090 | 20 | T9 |
| `sealed-tfidf-names.csv` | TF-IDF | baseline | names | — | — | 20 | T4 |
| `sealed-tfidf-names-about.csv` | TF-IDF | baseline | names + about | — | — | 20 | T4, P, S7, FAQ |
| `sealed-embed-names.csv` | Qwen3-Embedding-0.6B Q8_0 | baseline | names | — | — | 20 | T4 |
| `sealed-embed-names-about.csv` | Qwen3-Embedding-0.6B Q8_0 | baseline | names + about | — | — | 20 | T4, FAQ |
| `dev-2b-q4km-names-about.csv` | 2B Q4_K_M | one ask | names + about | 65K | RTX 4090 | 12 | T2, X |
| `dev-4b-q4km-names-about.csv` | 4B Q4_K_M | one ask | names + about | 65K | RTX 4090 | 12 | T2, X |
| `dev-9b-q4km-names-about.csv` | 9B Q4_K_M | one ask | names + about | 65K | RTX 4090 | 12 | T2, X |
| `dev-2b-q4km-names-about-8k.csv` | 2B Q4_K_M | one ask | names + about | 8K | RTX 4090 | 12 | T1, T2, T3, T5, X, M |
| `dev-4b-q4km-names-about-8k.csv` | 4B Q4_K_M | one ask | names + about | 8K | RTX 4090 | 12 | T2, T3, T5, X |
| `dev-9b-q4km-names-about-8k.csv` | 9B Q4_K_M | one ask | names + about | 8K | RTX 4090 | 12 | T1, T2, T3, T5, X, M |
| `dev-2b-q4km-names-about-vote-8k.csv` | 2B Q4_K_M | four asks | names + about | 8K | RTX 4090 | 12 | T3, T5, S3 |
| `dev-4b-q4km-names-about-vote-8k.csv` | 4B Q4_K_M | four asks | names + about | 8K | RTX 4090 | 12 | T3, T5 |
| `dev-9b-q4km-names-about-vote-8k.csv` | 9B Q4_K_M | four asks | names + about | 8K | RTX 4090 | 12 | T1, T3, T5, S3, M |
| `dev-4b-q8-tool-agent-v3.csv` | 4B Q8_0 | tool agent (v3) | model list | 65K | RTX 4090 | 12 | FAQ |
| `dev-4b-q8-tool-agent-v4.csv` | 4B Q8_0 | tool agent (v4 list rules) | model list | 65K | RTX 4090 | 12 | FAQ |
| `dev-9b-q8-tool-agent-v3.csv` | 9B Q8_0 | tool agent (v3) | model list | 65K | RTX 4090 | 12 | FAQ |
| `dev-9b-q8-tool-agent-v4.csv` | 9B Q8_0 | tool agent (v4 list rules) | model list | 65K | RTX 4090 | 12 | FAQ |
| `mac-dev-2b-q4km-names-about-8k.csv` | 2B Q4_K_M | one ask | names + about | 8K | Mac M2 16GB | 4 | T1, T2, T3, M |
| `mac-dev-9b-q4km-names-about-8k.csv` | 9B Q4_K_M | one ask | names + about | 8K | Mac M2 16GB | 4 | T1, T2, T3, S4, M |
| `mac-dev-9b-q4km-names-about-vote-8k.csv` | 9B Q4_K_M | four asks | names + about | 8K | Mac M2 16GB | 4 | T1, T3, M (scored at export because the benchmark file was not yet scored) |
| `downloads-9b-q4km-careful-vote-8k.csv` | 9B Q4_K_M | four asks | names + about (careful) | 8K | Mac M2 16GB | 1 | T1, T5, T7, T8, S3, S4 |
| `downloads-9b-q4km-careful-8k.csv` | 9B Q4_K_M | one ask | names + about (careful) | 8K | Mac M2 16GB | 1 | T1, T5, T7, T8, S2, S3, S4, S7 |
| `downloads-9b-q4km-casual-8k.csv` | 9B Q4_K_M | one ask | names + about (casual) | 8K | Mac M2 16GB | 1 | T7, T8, S2 |
| `downloads-2b-q4km-careful-8k.csv` | 2B Q4_K_M | one ask | names + about (careful) | 8K | Mac M2 16GB | 1 | T1, T7, T8, FAQ |
| `downloads-2b-q4km-casual-8k.csv` | 2B Q4_K_M | one ask | names + about (casual) | 8K | Mac M2 16GB | 1 | T7, T8 |
| `downloads-9b-q4km-names-8k.csv` | 9B Q4_K_M | one ask | names | 8K | Mac M2 16GB | 1 | T8, S2, S7 |
| `downloads-2b-q8-names.csv` | 2B Q8_0 | one ask | names | 65K | Mac M2 16GB | 1 | T8 |
| `downloads-tfidf-names.csv` | TF-IDF | baseline | names | — | recomputed at export | 1 | T8, S7 |
| `downloads-tfidf-careful.csv` | TF-IDF | baseline | names + about (careful) | — | recomputed at export | 1 | T8, S7 |
| `downloads-tfidf-casual.csv` | TF-IDF | baseline | names + about (casual) | — | recomputed at export | 1 | T8 |
| `downloads-embed-names.csv` | Qwen3-Embedding-0.6B Q8_0 | baseline | names | — | recomputed at export | 1 | T8, S7 |
| `downloads-embed-careful.csv` | Qwen3-Embedding-0.6B Q8_0 | baseline | names + about (careful) | — | recomputed at export | 1 | T8, S7 |
| `downloads-embed-casual.csv` | Qwen3-Embedding-0.6B Q8_0 | baseline | names + about (casual) | — | recomputed at export | 1 | T8, S7 |
| `desktop-9b-q4km-model-list-8k.csv` | 9B Q4_K_M | one ask | model list | 8K | Mac M2 16GB | 1 | 3.3, S6 |
| `desktop-2b-q8-model-list.csv` | 2B Q8_0 | one ask | model list | 65K | Mac M2 16GB | 1 | 3.3, S6 |
| `desktop-4b-q4km-model-list.csv` | 4B Q4_K_M | one ask | model list | 65K | Mac M2 16GB | 1 | 3.3, S6 |

Baselines: TF-IDF and the embedding got the same project list as the model, read each file's name and first 2KB, and left a file in place below a threshold picked on the dev folders (TF-IDF 0.02; embedding 0.51 for names, 0.59 with descriptions).

## Not in this folder

- The human review sample (section 1.1), the draft-list check, and the earlier agent versions in the FAQ.
