# Tests

Plain Python, no test framework. Each file runs on its own and prints how many tests passed:

```sh
for t in tests/test_*.py; do python3 -B "$t"; done
```

None of them loads a model. `fixtures.py` makes a throwaway folder per test.

| File | What it checks |
|---|---|
| `test_safety.py` | Paths cannot leave the folder; symlinks and the journal are off limits; nothing is overwritten |
| `test_apply_undo.py` | Moving and undoing: only top-level files, failing lines skipped, undo after a failure or a killed run |
| `test_preview.py` | A preview moves nothing, and an approved preview runs exactly its lines |
| `test_plan_contract.py` | The scorer reads every plan line the tool shows the same way the tool does |
| `test_harness_steps.py` | The steps around the model's questions: everything the model names is checked |
| `test_harness_votes.py` | A file moves only when three of four answers agree |
| `test_project_sources.py` | An empty project box lets the model write the list; a filled one replaces it |
| `test_compose_vote.py`, `test_compose_draft.py`, `test_compose_sampling.py` | The workflows in `model-compose.yml`: the vote flow, the draft tab, the sampling settings |
| `test_service_config.py` | `.env.sample` is the measured setting and the web UI opens on the first tab |
| `test_env_report.py` | The re-run report names the machine, packages, settings and compose file |
| `test_measure_*.py` | The `measure` package: rebuilding the dev folders, running, scoring, checking hashes |
| `test_report_tables.py` | The README's headline numbers match `results/` |
| `test_stats.py` | Wilson, McNemar and Holm give the published values |
