# Tools

The code steps the web UI's workflows call. `model-compose.yml` runs `python3 tools/organizer.py <command> <folder> [args]` with plain arguments, never through a shell. Only these files read or move anything on disk, and every path goes through `safe_paths.py` first.

| File | What it does |
|---|---|
| `organizer.py` | The entry point: turns the command and its arguments into a call to one of the steps below |
| `safe_paths.py` | Keeps every path inside the chosen folder; refuses symlinks and the undo journal; moves a file without overwriting |
| `reading.py` | Reads the first part of a text file for the model; never writes |
| `project_sources.py` | Reads the project list you type (`name: about`, one per line) |
| `project_menu.py` | Turns the project list into the numbered menu the model picks from |
| `harness_state.py` | The values one run carries from step to step |
| `harness_steps.py` | The steps between the model's two questions: which projects, then which project each file belongs to |
| `harness_votes.py` | Asks about each file with the list in four orders and keeps a project only when three answers agree |
| `vote_log.py` | Writes each file's four answers to `.organizer/votes/`, so you can see why a file moved or stayed |
| `plan.py` | Reads and writes the plan as `file => project` lines |
| `preview.py` | Shows what a plan would do without moving anything |
| `shown_plan.py` | Names the files you removed from the plan before approving |
| `moving.py` | Carries out an approved plan: only top-level files, nothing deleted or overwritten, a failing line skipped |
| `journal.py` | Records each approved run before every move, and undoes the latest run |
| `workspace_lock.py` | Lets only one command change the folder at a time |
| `env_report.py` | Prints the machine, package versions and model file to attach when you share a re-run |
