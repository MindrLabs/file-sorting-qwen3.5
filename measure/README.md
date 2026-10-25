# Re-measuring the organizer

`measure` rebuilds the twelve synthetic dev folders, runs this folder's organizer on them through a
running `model-compose up`, and scores every run the way the published numbers were scored. Its
first-plan hashes tell you whether your machine showed the person the same plan, byte for byte.

Run the commands from the folder that holds `model-compose.yml`. They need Python 3.12 and nothing else.

## 1. Rebuild the dev folders

```sh
python3 -m measure rebuild /tmp/dev-folders            # or --folders dev-01,dev-02
```

Each folder is built from `measure/designs/dev-NN/` (the design, its seed and its labels) as
`<out_dir>/dev-NN/files`, and every file is checked against its recorded sha256. `run` builds the folders
itself; this command is for looking at them.

## 2. Run the organizer on them

Start the server with `ORGANIZE_ROOT` set to an empty folder and the model settings of the line you want
to reproduce (see [Lines](#lines)), then:

```sh
python3 -m measure run --root ./measure-root --workflow organize \
  --line dev-9b-q4km-names-about-vote-8k --folders dev-01,dev-02 --out results.csv
```

For each folder, `run`:

1. empties `--root` and builds the folder there. It refuses a folder holding files it did not put there.
2. starts the workflow with the folder's projects in the `projects` box, one `name: about` line each.
3. answers every approval stop as a stand-in reviewer. A plan with no wrong line is approved as is;
   otherwise the plan goes back with the wrong lines fixed or removed (`--mode reject` names them instead).
4. runs `undo` for every applied plan and checks that the folder came back.
5. scores the run and writes its row to `results.csv`.

`results.json` and `results-runs/` (each run's plans, answers and undo journal) go next to the table.
The server address defaults to `http://localhost:8080/api`; change it with `--api`.
A stopped run picks up where it left off with `--resume`: folders already in `--out` from the same line,
workflow and mode are kept and not run again. Without it, `--out` is written anew.

## 3. Check the first plans

```sh
python3 -m measure check results.csv measure/first-plans/dev-9b-q4km-names-about-vote-8k.sha256
```

`same` means the model showed the same first plan as the published run. The same settings can give a
different plan on another kind of machine (an Apple M2 and an RTX 4090 differed on some folders), so
compare with the line measured on hardware like yours.

## 4. Score runs again

```sh
python3 -m measure score results.json --out rescored.csv
```

Scores every run in a run file without a model and compares each key with what the file recorded.

## Lines

| line | workflow | model file (`LLM_GGUF`) | `LLM_N_CTX` | measured on | folders |
|---|---|---|---|---|---|
| `dev-{9b,4b,2b}-q4km-names-about-vote-8k` | `organize` | `Qwen3.5-{9B,4B,2B}-Q4_K_M.gguf` | 8192 | RTX 4090 | all 12 |
| `dev-{9b,4b,2b}-q4km-names-about-8k` | `organize-quick` | `Qwen3.5-{9B,4B,2B}-Q4_K_M.gguf` | 8192 | RTX 4090 | all 12 |
| `dev-{9b,4b,2b}-q4km-names-about` | `organize-quick` | `Qwen3.5-{9B,4B,2B}-Q4_K_M.gguf` | 65536 | RTX 4090 | all 12 |
| `mac-dev-9b-q4km-names-about-vote-8k` | `organize` | `Qwen3.5-9B-Q4_K_M.gguf` | 8192 | Apple M2, 16GB | dev-01 to dev-04 |
| `mac-dev-{9b,2b}-q4km-names-about-8k` | `organize-quick` | `Qwen3.5-{9B,2B}-Q4_K_M.gguf` | 8192 | Apple M2, 16GB | dev-01 to dev-04 |

`LLM_REPO` is `unsloth/Qwen3.5-9B-GGUF` (or 4B, 2B), with `LLM_PRESENCE_PENALTY=1.5` and `LLM_MIN_P=0`.
The `#` lines of each `.sha256` file give the server settings, model revision and machine of that line.

## The table

One row per line and folder: `line,folder`, the published quality keys in the published order, then
`gen_sec,peak_mb,first_plan_sha256`. `first_plan_sha256` is the sha256 of the plan text shown at the first
approval stop (UTF-8). `gen_sec` runs from the start of the run to its end, polled every 2 seconds as in the
published runs.

Values nobody measured are blank. `run` does not measure memory (`peak_mb`), and the organizer keeps no
log of its tool calls, so `step1_tool`, `step7_stops`, `calls_after_done` and `empty_plans` stay blank.
The `usable` columns read `step7_stops`: they are 0 when the plan fails another test and blank when it
passes every other one.
