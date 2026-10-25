# Scripts

Recompute every table and summary number in the README from the files in `results/`, with 95% intervals and paired tests. They need only Python 3.12 and read nothing outside `results/`.

```sh
python3 scripts/report_tables.py          # everything
python3 scripts/report_tables.py 4 sensitivity   # chosen sections
```

| File | What it does |
|---|---|
| `report_tables.py` | The entry point: prints the chosen sections |
| `results_data.py` | Reads `results/*.csv` |
| `stats.py` | Wilson intervals, exact McNemar, Holm, folder bootstrap |
| `comparisons.py` | The comparisons the README rests on, defined once |
| `report_format.py` | How a number, interval or difference is printed |
| `summary.py` | The README summary, item by item |
| `tables_device.py` | Settings, memory and time (README section 2) |
| `tables_features.py` | The 20 unseen folders: usable counts, asking four times, picking and leaving alone, quantization |
| `tables_real.py` | The real Downloads and Desktop copies, and the undo check |
| `sensitivity.py` | Whether a first plan changes with the machine or the context length |

The table numbers these scripts print are their own; `results/README.md` maps them to the README's table numbers.
