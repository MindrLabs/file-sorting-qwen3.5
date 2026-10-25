[English](preregistration.md) · [한국어](preregistration.ko.md) · [中文](preregistration.zh-cn.md)

# Preregistration record

What was fixed before the results in this measurement, and what changed after. The commit hashes and times behind each line are in the folded tables; how to check them is at the end.

## At a glance

For each README claim: was it measured as registered before the results? Read the "no" claims as hypotheses for the next measurement.

| README claim | Measured as registered before the results |
|---|---|
| The other unseen-folder cells: the 8-bit rows (Table 8), 4-bit 2B·4B, 2-bit, the model-made-list cell, the names-only cell, the baselines | Yes |
| Picking and leaving alone (Tables 5 and 9) | Yes |
| The quantization comparisons (Table 10, except the 9B row) | Yes |
| The flow comparison (3.6) | Yes |
| The dev comparison of asking four times (the dev rows of Table 4) | Yes |
| With a given list, 9B 4-bit was usable on 19 of 20 unseen folders (95%) | No |
| Asking four times kept the usable share on the unseen folders and cut lines to fix from 8.3% to 4.3% | No |
| All numbers on the real Downloads folder: only asking four times was usable, careful descriptions got 13 more files right, and with names only or casual descriptions the 0.6B embedding beat 9B asking once | No |
| On a Desktop copy with nothing to organize, even 9B 4-bit tried to move 25 of 30 files | No |
| The draft list was usable as is for only about 4 of 19 projects on the real Downloads folder | No |
| Time and memory on a 16GB Mac, and first plans at 8K matching 65K | No |
| First plans differed between the Mac and the 4090 (2 of 4 for 9B, all 4 for 2B) | No |
| People also fixed 83% of the lines the stand-in reviewer fixed | No |
| Neither grouping notes nor fixing the list rules helped | No |

For the tool agent cells, though, the commit that narrowed the scope came after the runs started. The dev folders were used to build and fix the tool, so their results do not weigh the same as the unseen folders'.

<details>
<summary>Why each "no" claim is exploratory, and where it is in the README</summary>

The README claims below were not measured as registered before the results. Read them as hypotheses for the next measurement.

| README claim | Where | Why it is exploratory |
|---|---|---|
| With a given list, 9B 4-bit was usable on 19 of 20 unseen folders (95%) | First paragraph, Summary 1, Table 1, Table 3, Table 8, Figure 3 | The cell was added after seeing the 9B 8-bit result, and its registering paragraph is in the same commit as the results. The 9B 8-bit cell, registered before the results, also passed with 18 (90%) |
| Asking four times kept the usable share on the unseen folders and cut lines to fix from 8.3% to 4.3% | Summary 3, Method 2, Table 1, Table 4, Figure 2 | Designed after seeing unseen-folder results. The unseen-folder run was not registered on its own |
| All numbers on the real Downloads folder: only asking four times was usable, careful descriptions got 13 more files right, and with names only or casual descriptions the 0.6B embedding beat 9B asking once | Reading these numbers, Summary 2·3·7, Method 1·2, Table 1, Table 4, Table 6, Table 7, Figure 4, 3.4, FAQ | One folder, one run per setting. This folder was used to find and fix defects twice. The two sets of descriptions, asking four times, 9B names only, and the baselines given the same descriptions were added without registration. The descriptions were written from the answer table. Asking once and asking four times ran on different model-compose builds ("Changes") |
| On a Desktop copy with nothing to organize, even 9B 4-bit tried to move 25 of 30 files | Summary 6, 3.3, 4 Recommendations | One folder, one run. The 9B cell was added without registration. The 2B and 4B cells were registered, but their runs started before the registering commit |
| The draft list was usable as is for only about 4 of 19 projects on the real Downloads folder | Quick start, section 5, FAQ | Measured once on one folder. Not registered |
| Time and memory on a 16GB Mac, and first plans at 8K matching 65K | Summary 4, Table 1, Table 2, Table 11, section 2 | The registering paragraph is in the same commit as the results. The Mac used 4 dev folders. The 8K check was done only for asking once |
| First plans differed between the Mac and the 4090 (2 of 4 for 9B, all 4 for 2B) | Sections 1, 2 and 5 | An after-the-fact comparison not in the evaluation document. Checked again with the result files while writing this document |
| People also fixed 83% of the lines the stand-in reviewer fixed | Reading these numbers, Method 3, 1.1, section 5 | An unregistered check. One person, 8 plans |
| Neither grouping notes nor fixing the list rules helped | FAQ | Dev-folder results. The pass criteria of the notes probe are not in git |

</details>

## Fixed before the results

"Before the results" asks whether the registering commit came before the run start. "Not confirmed" means it did not, or git cannot tell.

| # | What was fixed | Before the results |
|---|---|---|
| 1 | Usable folder | Yes, but after seeing 9B on the old dev folders |
| 2 | Judging rule | Yes |
| 3 | Pass line | Yes |
| 4 | Paired comparison | Yes |
| 5 | Scoring program, version 8 | Not confirmed |
| 6 | Unseen folders are used once | Yes; 2 settings were added after seeing the results |
| 7 | Tool agent, 6 lines | Partly; the commit that dropped thinking mode came after the run start |
| 8 | Step-by-step cells | Yes |
| 9 | Picking and leaving alone | Yes |
| 10 | Baselines | Yes |
| 11 | Quantization comparison | Yes |
| 12 | 27B reference point | Yes |
| 13 | Predictions before the results | Partly |
| 14 | Light setting | Not confirmed |
| 15 | Dev comparison of asking four times | Yes |
| 16 | Real-folder cells | Not confirmed |
| 17 | Fixing the tool agent's list rules (dev) | Round 1 yes; round 2 started 5 minutes before its registration |
| 18 | Four probes | Not confirmed |

<details>
<summary>Judging rules (1–5): what was fixed, and the commits</summary>

| # | What was fixed | Registered | Order |
|---|---|---|---|
| 1 | **Usable folder.** The first plan can be approved after only small fixes. All four must hold: lines to fix at most 20%, at least 60% of files with an answer moved, folders already organized left untouched, stops at the end | d459fdf · 2026-10-18T13:52:04+09:00 | Confirmed. But it was set after seeing 9B results (60 runs) on the old dev folders. The same commit says so. It comes before the small-model results |
| 2 | **Judging rule.** Write "can be trusted with it" when the lower bound of the 95% confidence interval of the usable share is 0.5 or more. If not, write "none" and do not lower the bar. Judge each flow on its own | d459fdf · 2026-10-18T13:52:04+09:00. Each flow on its own: 71e0968 · 2026-10-18T18:43:16+09:00 | Confirmed |
| 3 | **Pass line.** Judge per folder on 20 unseen folders. At least 15 of 20 (75%) must be usable to pass. With 14 the lower bound is 0.48, so it does not pass | b9f18d8 · 2026-10-19T22:52:21+09:00 | Confirmed. The sentence fitting today's one run per folder (a folder passes if that run is usable) was written in 0cfe9a7 · 2026-10-23T20:20:33+09:00. That commit came after the tool agent's judgment runs had started (2026-10-23T17:54) |
| 4 | **Paired comparison.** Take the pair F1 difference folder by folder and resample folders for a 95% interval. If the interval excludes 0: "different". If it lies within ±0.05: "same". Otherwise: "can't tell" | b9f18d8 · 2026-10-19T22:52:21+09:00. Resampling seed fixed: 87d55a8 · 2026-10-23T10:27:17+09:00 | Confirmed |
| 5 | **Scoring program, version 8.** When counting "stops at the end", steps that run by themselves after the person approves are not counted as model calls. It only touches tool agent scores | 3e5b997 · 2026-10-24T00:00:12+09:00 | Not confirmed. The unseen-folder runs had already finished (last start 2026-10-23T23:29). The evaluation document says this was written before the results were opened. Git cannot confirm that |

</details>

<details>
<summary>Unseen folders (6–13): what was fixed, and the commits</summary>

| # | What was fixed | Registered | Order |
|---|---|---|---|
| 6 | **Unseen folders are used once.** The 20 old judgment folders were retired. 32 new ones were made the same way and split once at random into 12 dev and 20 judgment folders. Judgment folders are used once, after the flow is fixed | 8285ccd · 2026-10-21T15:21:21+09:00, 7a2318a · 2026-10-21T17:04:30+09:00 | Confirmed. 24 model settings each ran once on the 20 folders. 22 ran on 2026-10-23, and 2 were added after seeing those results (the 2026-10-24 rows under "Changes"). The results of the 2 added later are in 6d168de · 2026-10-24T22:43:50+09:00 |
| 7 | **Tool agent, 6 lines.** 8-bit 2B·4B·9B, 4-bit 2B·4B, 2-bit 4B. Once per folder. The first registration also had lines with thinking mode on | 87d55a8 · 2026-10-23T10:27:17+09:00, 329ed66 · 2026-10-23T14:41:46+09:00. Narrowed scope: 0cfe9a7 · 2026-10-23T20:20:33+09:00 | 87d55a8 and 329ed66 confirmed (run start 2026-10-23T17:54). 0cfe9a7, which dropped the thinking-on lines, was committed after the runs had started |
| 8 | **Step-by-step cells.** Given-list cell (names and descriptions), 7 lines: 8-bit 0.8B·2B·4B·9B, 4-bit 2B·4B, 2-bit 4B. Model-made-list cell, the same 7 lines. Names-only cell, 8-bit 2B·4B | 0cfe9a7 · 2026-10-23T20:20:33+09:00 | Confirmed (run start 2026-10-23T22:49) |
| 9 | **Picking and leaving alone.** Measure separately the share sent to the right given folder and the share of unrelated files left in place. Write "works" when the lower bound is 0.80 or more | 0cfe9a7 · 2026-10-23T20:20:33+09:00 | Confirmed |
| 10 | **Baselines.** Give TF-IDF and the 0.6B embedding the same list as the model. Set the threshold on the 12 dev folders and use it once on the unseen folders. Write "the model adds picking" only when the model is "different (+)" from the baseline on the same folders | 0cfe9a7 · 2026-10-23T20:20:33+09:00 | Confirmed |
| 11 | **Quantization comparison.** Compare 8-bit against 4-bit and 2-bit of the same size, paired. Write "same after shrinking" only where the comparison says "same". Never write "can't tell" as "same". Report memory as measured, not file size. If 2-bit also drops in the step-by-step flow, which calls no tools, write "not only a tool-calling problem" | 329ed66 · 2026-10-23T14:41:46+09:00, 0cfe9a7 · 2026-10-23T20:20:33+09:00 | Confirmed |
| 12 | **27B reference point.** Measure 27B 4-bit with the same tool agent. If a 65K context does not fit on the 24GB GPU, stop without shrinking the context | caafbc0 · 2026-10-23T15:36:16+09:00 | Confirmed. It stopped as registered. It stopped during the first run and was not measured again |
| 13 | **Predictions before the results.** All copied to "Predictions and results" | 0cfe9a7 · 2026-10-23T20:20:33+09:00 | Partly confirmed. The predictions for the tool agent cells were committed while those runs were going |

</details>

<details>
<summary>Light setting, asking four times, real folders, dev comparisons (14–18): what was fixed, and the commits</summary>

| # | What was fixed | Registered | Result | Order |
|---|---|---|---|---|
| 14 | **Light setting.** Add a 9B 4-bit cell (given list) on the unseen folders. Rerun the 12 dev folders with an 8K context; if the first plans match 65K byte for byte, use the memory measured at 8K as that setting's memory. Measure time and memory on a 16GB Mac with 4 dev folders. Predictions were written too | 6773db7 · 2026-10-24T07:05:04+09:00 (same commit as the result) | 6773db7 · 2026-10-24T07:05:04+09:00 | Not confirmed. Runs started at 2026-10-24T00:40, and the registering paragraph was committed together with the results. The evaluation document says it was written before the runs and not edited after |
| 15 | **Dev comparison of asking four times.** Ask about each file four times with the list order changed, and move it only when one project gets 3 or more votes. A malformed answer is an abstention. 3 of 4 was not tuned on data. Compare with asking once on 12 dev folders, 4-bit 2B·4B·9B, 8K context. Predictions and the decision rule were written too | d95ba72 · 2026-10-24T20:20:24+09:00 | f6c2ece · 2026-10-24T20:51:25+09:00 | Confirmed (run start 2026-10-24T20:36). This result file is in git |
| 16 | **Real-folder cells.** Downloads copy: names-only cell, model-made-list step-by-step flow, tool agent (8-bit 2B, 4-bit 4B). Desktop copy: model-made-list step-by-step flow, tool agent. Baselines get names only | 3180eed · 2026-10-23T23:29:03+09:00 | 6773db7 · 2026-10-24T07:05:04+09:00 | Not confirmed. Runs started before the registering commit (2026-10-23T22:22) |
| 17 | **Fixing the tool agent's list rules (dev).** Round 1: reject lists with no new project, narrower merging, and so on. Round 2: only the rule that picks files to leave in place was set back to before the fix. Questions and predictions were written | Tool definition: 0b33c6e · 2026-10-24T12:23:46+09:00. Round 1: 5be2d76 · 2026-10-24T13:29:43+09:00. Round 2: 20df275 · 2026-10-24T18:24:03+09:00 | Round 1: 20df275 · 2026-10-24T18:24:03+09:00. Round 2: 24f7081 · 2026-10-24T20:00:20+09:00 | Round 1 confirmed (run start 2026-10-24T16:56). In round 2 the first run started 5 minutes before the registering commit (18:19) |
| 18 | **Four probes.** Probability scores, grouping by notes, thinking mode, stacking more on top. The evaluation document says the pass criteria were set before running | A plan document outside the repo (not in git) | a25e508 · 2026-10-22T18:10:55+09:00 | Not confirmed. The document with the criteria is not in git |

</details>

## Predictions and results

The README table "Predictions written before the results, and results" shows some of these. All registered predictions are copied here.

**Predictions written in 0cfe9a7 · 2026-10-23T20:20:33+09:00.** Results in 6773db7 · 2026-10-24T07:05:04+09:00.

| Prediction | Result | Right? |
|---|---|---|
| On the unseen folders, none of the 6 tool agent lines passes | 0–2 of 20 | Right |
| In that cell, 9B is highest and at most 4 | 9B 1, 4B 4-bit 2 | At most 4: right. "9B is highest": wrong |
| In the given-list cell, 2B does not pass (8–14) | 11 | Right |
| In that cell, 4B is similar to 2B or lower, because of files to leave in place | 1 | Right |
| In that cell, 9B is borderline | 18, passes | Wrong |
| In that cell, 0.8B gets 0–2 | 2 | Right |
| The model-made-list step-by-step flow: none passes, 9B highest and at most 6 | 9B 6, others 0–1 | Right |
| Names only scores lower than names and descriptions | 2B 3 vs 11, 4B 0 vs 1 | Right |
| With a given list, the picking lower bound of 2B and 4B is 0.80 or more | Both "work" | Right |
| With a given list, the leaving-alone lower bound of 2B and 4B is below 0.80 | 2B 0.89 (lower bound 0.83), 4B 0.50 | 2B wrong, 4B right |
| The baselines' pair F1 is lower than 2B with a given list, but not 0 | TF-IDF higher than 2B (different). Embedding lower than 2B | TF-IDF wrong, embedding right |
| No baseline passes | TF-IDF passes with 16, embedding 6 | TF-IDF wrong, embedding right |
| Tool agent, 4B 4-bit vs 8-bit: can't tell | Can't tell | Right |
| 4B 2-bit vs 8-bit: different (−) in the tool agent | −0.24, different | Right |
| 4B 2-bit vs 8-bit: can't tell in the given-list step-by-step flow | −0.05, different | Wrong |
| The 27B reference point has fewer than half usable folders | Could not be measured | No result |

<details>
<summary>The other predictions (light setting, asking four times, the tool agent's list rules)</summary>

**Predictions written in 6773db7 · 2026-10-24T07:05:04+09:00.** Same commit as the results, so git cannot confirm the order.

| Prediction | Result | Right? |
|---|---|---|
| On the unseen folders, 9B 4-bit (given list) gets 16–18 | 19 | Wrong |
| 9B 4-bit vs 8-bit is "same" or "can't tell" | +0.003, same | Right |
| First plans at 8K context match 65K | All match for 4-bit 2B·4B·9B on 12 dev folders | Right |
| 9B 4-bit at 8K uses 6–7GB, and 1–3 minutes per folder on a Mac | 4090 6.0GB, Mac 6.5GB, Mac median 120 seconds | Right |

**Predictions written in d95ba72 · 2026-10-24T20:20:24+09:00 (dev comparison of asking four times).** Results in f6c2ece · 2026-10-24T20:51:25+09:00.

| Prediction | Result | Right? |
|---|---|---|
| The number of files 2B moves that should stay drops from 41 to half or less | 41 → 3 | Right |
| 2B's usable folders rise above 6 | 6 → 6 | Wrong |
| Risk: fewer files moved, so some folders may fall under the 60% bar | 2B share moved 0.76 → 0.60 | The risk happened |
| 9B stays the same or drops slightly | 12 → 12 | Right |
| 4B may change the most, direction unknown | 2 → 7 | No direction predicted |

**Predictions written in 5be2d76 · 2026-10-24T13:29:43+09:00 (round 1) and 20df275 · 2026-10-24T18:24:03+09:00 (round 2) (the tool agent's list rules).** Results in 20df275 (round 1) and 24f7081 · 2026-10-24T20:00:20+09:00 (round 2).

| Prediction | Result | Right? |
|---|---|---|
| Round 1: folders ending with a list with no new project go to 0 | 9B·4B·2B 2·5·5 → 0 | Right |
| Round 1: 9B pair F1 rises slightly or stays | 0.448 → 0.289 | Wrong |
| Round 1: 2B may get more folders that loop after a rejection and never reach approval | 4 → 5 | One folder apart, not judged |
| Round 1: the number of files moved may change, direction unknown | Rose a lot | No direction predicted |
| Round 2: the share of files moved that should stay, and pair precision, return to the level before the fix | They returned | Right |
| Round 2: folders ending with a list with no new project stay at 0 | 0 | Right |
| Round 2: 4B's rise in folders reaching approval remains | 9 → 10 | Right (one folder apart) |
| Round 2: unknown whether pair F1 beats the level before the fix | 9B +0.003, 4B +0.015 | No direction predicted |

</details>

## Changes

| Commit | What changed |
|---|---|
| d459fdf | Number definitions and the judging rule were set, after seeing 9B results (60 runs) on the old dev folders |
| f8c4ec1 | Ambiguous files that make sense in either of two projects are left out of scoring |
| 7f198d9, d000f1c | All flows moved to the model card's recommended values |
| b9f18d8 | Judging moved from the old dev folders (per run) to 20 unseen folders (per folder, 15 of 20) |
| 8285ccd, 7a2318a | The 20 old judgment folders were retired |
| fd2a72a, caafbc0, 3e5b997 | The way "stops at the end" is counted was fixed three times (scoring program versions 6, 7 and 8) |
| 0cfe9a7 | The scope was cut |
| 3180eed | The results of the registered person checks (9 person-reviewed runs on the old folders, a hands-on trial on a real folder) are not in the evaluation document |
| 6773db7 | The report's question was narrowed to "the lightest setting I can use on my laptop today" |
| 6773db7 | The 27B reference run stopped during its first run |
| fbd582c | Found after the runs |
| d95ba72 → 6d168de | Asking four times was built |
| 6fedf2a | A defect that cut a person's list at 8 lines was fixed |
| f6c2ece, 6d168de | On the real Downloads folder, cells with names and descriptions (careful and casual), asking four times, and the draft list were measured |
| b836200 | Measurement and release use different model-compose builds |
| 67175a1 → 1bc0bc5 | The release was split from the measurement code |
| 59e0a3d → 5c0790d | The release's structure changed |
| 2026-10-25, not yet committed | After a README reader review, three more real-folder cells were measured |

<details>
<summary>Each change: why, and its effect on the results</summary>

| Commit | What changed | Why | Effect on the results |
|---|---|---|---|
| d459fdf · 2026-10-18T13:52:04+09:00 | Number definitions and the judging rule were set, after seeing 9B results (60 runs) on the old dev folders. One mistake being penalized at several steps was fixed, and pair F1, the share of lines to fix and the usable bar were added | The 9B results showed double penalties in scoring | Comes before the small-model results. 9B was already seen when the bar was set |
| f8c4ec1 · 2026-10-18T18:56:17+09:00 | Ambiguous files that make sense in either of two projects are left out of scoring. It started with 2 files in the old dev folders | Rechecking 16 often-missed files showed 2 made sense in both places | A correction after seeing results. The verdicts did not change, and the numbers before and after were recorded. The README's share of lines to fix follows this rule |
| 7f198d9 · 2026-10-19T14:59:06+09:00, d000f1c · 2026-10-19T15:18:33+09:00 | All flows moved to the model card's recommended values: context 16K → 65K, output cap of long-answer flows 2,048 → 16,384, presence_penalty 0 → 1.5, min_p 0.05 → 0. The step-by-step flow's short answer cap and temperature 0.2 stayed | Long-answer flows were cut off or ran past the context | Step-by-step runs use these values from then on. So do the unseen-folder results. The light setting changes only the context, to 8K |
| b9f18d8 · 2026-10-19T22:52:21+09:00 | Judging moved from the old dev folders (per run) to 20 unseen folders (per folder, 15 of 20) | The old folders were used to fix and choose tools. With only three test folders, the per-folder lower bound is 0.44 even if all pass, so no verdict is possible | Verdicts on the old folders are not used in the report |
| 8285ccd · 2026-10-21T15:21:21+09:00, 7a2318a · 2026-10-21T17:04:30+09:00 | The 20 old judgment folders were retired. 32 new ones were made the same way and split into 12 dev and 20 judgment folders | After using the old judgment folders once, diagnostic totals were seen. The decision to redesign the flow also came after that | The old judgment results are not used in the report, and their numbers are not in the evaluation document. The README's unseen folders are the new 20 |
| fd2a72a · 2026-10-21T15:35:01+09:00, caafbc0 · 2026-10-23T15:36:16+09:00, 3e5b997 · 2026-10-24T00:00:12+09:00 | The way "stops at the end" is counted was fixed three times (scoring program versions 6, 7 and 8) | Cases where stopping was miscounted in agent flows were found | Only agent-flow scores are touched. Other flows scored the same when rescored (versions 6 and 7). Version 8 is item 5 under "Fixed before the results" |
| 0cfe9a7 · 2026-10-23T20:20:33+09:00 | The scope was cut: thinking-on lines dropped, and tool agent runs on the unseen folders cut from 240 to 120. The report's questions were reorganized into three chapters (flow, picking, quantization), and the given-list cell was added on the unseen folders | Deadline (author's decision). On the old dev folders, 2B passed the bar only when given answer names and descriptions (54 of 60 runs) | The thinking-mode comparison remains only as dev results from before the fix. This commit came after the dev re-runs (started 2026-10-23T15:40) and the tool agent's unseen-folder runs (started 17:54). The evaluation document says the cut was decided before those results and that only progress logs of the unseen folders were seen. Git cannot confirm this. The first registered question ("the smallest Qwen you can trust with it") and its verdict are kept |
| 3180eed · 2026-10-23T23:29:03+09:00 | The results of the registered person checks (9 person-reviewed runs on the old folders, a hands-on trial on a real folder) are not in the evaluation document. The person check that was recorded is the author fixing 8 plans (166 lines) without seeing the stand-in reviewer's calls | The evaluation document gives no reason | The person check is one person and 8 plans |
| 6773db7 · 2026-10-24T07:05:04+09:00 | The report's question was narrowed to "the lightest setting I can use on my laptop today". A 9B 4-bit cell was added on the unseen folders, and the 8K context was checked. The release default is 9B 4-bit with an 8K context (03dc19b · 2026-10-24T23:24:41+09:00) | Author's decision. It came after seeing the 9B 8-bit result (18) | The 9B 4-bit cell (19) was added after seeing results, and its registering paragraph is in the same commit as the results. First plans at 8K matched 65K byte for byte for 4-bit 2B·4B·9B on 12 dev folders. This was checked only for asking once. The unseen-folder numbers were measured at 65K |
| 6773db7 · 2026-10-24T07:05:04+09:00 | The 27B reference run stopped during its first run | It did not fit on the 24GB GPU with a 65K context | As registered, it was not rerun with a smaller context. There is no comparison with a large model |
| fbd582c · 2026-10-24T11:25:58+09:00 | Found after the runs: the shared words the tool agent attaches to each group varied from run to run | Found while replaying recorded tool calls | The groups were the same; small differences crept into the text the model reads. The measured code was left as is, for reproduction |
| d95ba72 · 2026-10-24T20:20:24+09:00 → 6d168de · 2026-10-24T22:43:50+09:00 | Asking four times was built. It was measured after registering the dev comparison, then measured with 9B 4-bit on the unseen folders and the real Downloads folder. It became the first tab of the web UI (e801a78 · 2026-10-24T22:57:22+09:00) | On the unseen folders, 2B 4-bit got 9. On the dev folders, more than half of 2B's wrong lines (41 of 72) moved files that should stay | It was designed after seeing unseen-folder results, so its unseen-folder result is exploratory. That run (started 2026-10-24T21:54) was not registered on its own. Of the registered condition ("propose an unseen-folder run if 2B rises clearly and 9B holds"), the 2B part was not met (6 → 6) |
| 6fedf2a · 2026-10-24T20:26:11+09:00 | A defect that cut a person's list at 8 lines was fixed | Found in the first run on the real Downloads folder (19 projects) | Synthetic folders have 6 projects or fewer, so their results do not change. The real Downloads folder was also used to find and fix a defect on 2026-10-19 (9a59b3f · 2026-10-19T14:59:06+09:00). So results on this folder are exploratory. The cut first run is not used in the report |
| f6c2ece · 2026-10-24T20:51:25+09:00, 6d168de · 2026-10-24T22:43:50+09:00 | On the real Downloads folder, cells with names and descriptions (careful and casual), asking four times, and the draft list were measured | To see the reader's flow (given-list step-by-step) on a real folder | Added without registration. One run per setting, one folder. The descriptions were written from the answer table, not by the folder's owner |
| b836200 · 2026-10-24T20:59:00+09:00 | Measurement and release use different model-compose builds. The 4090 runs behind the README numbers used fork 9a334ca6: the PyPI 0.4.120 release commit plus 2 upstream commits and 2 fork commits. The Mac runs used the same fork line. Runs whose result file records a commit show 11824e3b (the commit just before 9a334ca6, including ② below); the others record no commit. The release runs on PyPI 0.4.120. This commit is the first that changed settings so it starts on PyPI 0.4.120 | So readers can install the PyPI build | Of the three things only in the fork, the two sampling values reach the release's results (see "Fork vs PyPI 0.4.120" under the table) |
| 67175a1 · 2026-10-24T23:21:45+09:00 → 1bc0bc5 · 2026-10-25T01:08:30+09:00 | The release was split from the measurement code. Only the reader's four flows were moved (67175a1, 03dc19b), names were changed and code tidied (5f1bae7, 91e490d, 45ee550), and text shown to people was changed to English (1bc0bc5) | Public release | Two checks are written in the commit messages. The kept steps, instructions and sampling equal the measured settings down to the YAML values (03dc19b). With the same inputs, 2,432 steps of command-line output were compared, with 0 differences (91e490d, 45ee550, 1bc0bc5). Text shown to people, such as tab names, approval guidance and the move report, changed (45ee550, 1bc0bc5). There is no record in git of a byte comparison of first plans between the release and the measurement code |
| 59e0a3d · 2026-10-25T02:16:11+09:00 → 5c0790d · 2026-10-25T03:22:16+09:00 | The release's structure changed. State between steps is passed as values instead of hidden files (59e0a3d). Approval and re-asking after a rejection, which called each other, became one loop step (df8b727 · 2026-10-25T03:21:35+09:00). The measured versions (model-compose 0.4.120, llama-cpp-python 0.3.36, torch 2.14.1) and the 9B model file revision 3885219b6810b007914f3a7950a8d1b469d598a5 were pinned (5c0790d) | To make the release easier to read and to rerun | Checks written in the commit messages: the model instructions are identical byte for byte. A flow simulator found 36 runs and 3,740 events the same as 1bc0bc5, rejection paths included (59e0a3d). The message of df8b727 only says "the step order and instructions are unchanged". The pinned model-compose is PyPI 0.4.120, so ② in the row above (the two sampling values) still differs from the measurement |
| 2026-10-25, not yet committed | After a README reader review, three more real-folder cells were measured: baselines given the same descriptions as the model, 9B names only, and 9B on the Desktop copy. The baseline calculation was corrected once the same day | The review said "the baselines got names only while the model got descriptions" and "the 9B cells were empty" | Exploratory. In the first calculation the baselines also got descriptions of folders that already existed, so they had more information than the model. README Table 7 shows the corrected values. This record is not committed in the private repo yet, so it has no hash |

</details>

<details>
<summary>Fork vs PyPI 0.4.120 (the b836200 row)</summary>

- ① The xml tool-call format: the release flows call no tools.
- ② Passing presence_penalty and min_p to llama.cpp: PyPI 0.4.120 does not pass these two (checked in the package code). So in the release these two values run at llama.cpp defaults (0, 0.05).
- ③ Answer scoring and the thinking-mode option: for the tool agent.
- Check: on a Mac, the 8 first plans of 4 dev folders × 4-bit 2B·9B, 8K context, asking once, matched byte for byte between PyPI and the fork. This check is not in git or the evaluation document; it is only in the author's work notes (outside the repo). While writing this document, the remaining result files were compared again and all 8 matched.
- The unseen folders and asking four times were not rerun on PyPI. On the real Downloads folder, asking once was measured with the fork and asking four times with PyPI 0.4.120.

</details>

<details>
<summary>Registrations not used for the report's numbers</summary>

The README's numbers do not rest on these. They cover the 4 old dev folders, the old judgment folders and the tool agent's dev runs.

| Registered | What | Result |
|---|---|---|
| d459fdf · 2026-10-18T13:52:04+09:00 | The first question, three rule baselines (move nothing, by file type, by name word), 9 runs reviewed by a person | The results of the 9 person-reviewed runs are not in the evaluation document |
| c6d502c · 2026-10-18T17:12:06+09:00 | The step-by-step condition | f8c4ec1 · 2026-10-18T18:56:17+09:00 |
| 71e0968 · 2026-10-18T18:43:16+09:00 | The condition for a flow that asks about the whole folder at once, and changing only the sampling temperature | 4189e65 · 2026-10-19T10:47:52+09:00 |
| 92a9469 · 2026-10-18T18:44:27+09:00 | Judge with the step-by-step instructions minus the example words that overlapped answer names | 4189e65 · 2026-10-19T10:47:52+09:00 |
| bc60df2 · 2026-10-18T20:31:25+09:00 | A twin folder with only the language changed, a large realistic synthetic folder, a hands-on trial on a real folder | 4189e65 · 2026-10-19T10:47:52+09:00. The hands-on trial's results are not in the evaluation document |
| 11e7308 · 2026-10-18T22:54:03+09:00 | Give the old agent the same file information as the step-by-step flow and tune it the same way | 687dfc1 · 2026-10-19T10:47:52+09:00 (tuning), 7f198d9 · 2026-10-19T14:59:06+09:00 (trial) |
| d000f1c · 2026-10-19T15:18:33+09:00 | Measure again with the model card's recommended settings | 769500b · 2026-10-19T18:43:23+09:00 |
| b9f18d8 · 2026-10-19T22:52:21+09:00 | Main runs and diagnostic runs on the 20 old judgment folders | The old judgment results are not in the evaluation document (retired). The diagnostic cell with answer names only was reread as one cell of the 2×2 in cbade9b |
| 6b1d2d1 · 2026-10-20T11:27:03+09:00 | 2×2 that gives answer names and descriptions separately | cbade9b · 2026-10-21T15:21:14+09:00 |
| 87d55a8 · 2026-10-23T10:27:17+09:00 | The tool agent's dev runs | caafbc0 · 2026-10-23T15:36:16+09:00 |
| caafbc0 · 2026-10-23T15:36:16+09:00 | What to fix in the tool agent (at most 3 changes) and what to measure again | No section of its own. Some numbers appear as comparison points in 5be2d76 and 20df275 |

</details>

## How to check

- The commits are in the author's private repo, not in this repo. Ask with a hash and the author can show you that commit.
- Everything was recorded in one evaluation document in the private repo (`EVAL.md`). **Registered** is the commit that first wrote a rule or prediction into that document. **Result** is the commit that first wrote the result into the same document.
- Times are commit times in Korea time (UTC+9). They come from the clock of the author's computer. The hashes were not posted anywhere public at the time, so the times cannot be proven from outside.
- **Run start** is the start time of the first run, as stored in the result file. Result files for the unseen folders and the real folders are kept outside git. So these times cannot be checked with git.
- Every item under judging rules (1–5) and unseen folders (6–13) first had its result written in 6773db7 · 2026-10-24T07:05:04+09:00, so those two tables have no result column.
- In the **Order** column, "Confirmed" means the registering commit came before the run start. "Not confirmed" means it did not, or git cannot tell; the reason is given.
- For the unseen folders (the 20 synthetic judgment folders) and the real folders, no contents, file names or answers are shown. Only totals.
- Written on 2026-10-25. Release commits are covered up to 5c0790d (2026-10-25T03:22:16+09:00).
