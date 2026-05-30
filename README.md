# abqjobpilot

`abqjobpilot` is a lightweight desktop queue runner and monitor for Abaqus
`.inp` jobs. It provides a Tkinter GUI for adding Abaqus input files to a
queue, running `datacheck` and full analyses in sequence, monitoring `.sta`
and console logs, and recording live status/report files.

The project was created as a clean standalone tool inspired by an older local
Abaqus runner script. The old script is not modified by this repository.

## Features

- Standalone Tkinter GUI.
- Add one `.inp` file or scan one folder for `.inp` files.
- Queue persistence with JSON.
- Sequential Abaqus execution:
  - optional `datacheck`
  - optional full run
  - stop after current job
  - skip selected queued job
- Real-time status panel:
  - current job
  - strategy and batch
  - phase
  - step and increment
  - analysis time
  - ODB size
  - elapsed time
- `.sta` tail and console log tail.
- Result table with warning/failure status coloring.
- Agent Command Console:
  - internal command parser
  - multiline command paste
  - AI prompt copy helper
  - no arbitrary shell execution
- Basic settings:
  - Abaqus command path
  - default CPU count
  - optional GPU count
  - datacheck/full-run defaults
- Resource panel:
  - CPU
  - memory
  - NVIDIA GPU utilization when `nvidia-smi` is available
- Chinese/English UI toggle.
- Copy current diagnostic text for AI-assisted log analysis.

## Screenshot

Screenshots and packaged icon assets will be added later.

## Requirements

- Windows
- Python 3.9+
- Abaqus installed locally
- No required third-party Python packages for the core GUI

Optional:

- NVIDIA driver tools (`nvidia-smi`) for GPU utilization display.

## Installation

Clone the repository:

```powershell
git clone https://github.com/BrunelXian/abq_job_pilot.git
cd abq_job_pilot
```

Create and activate a virtual environment if desired:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install requirements:

```powershell
pip install -r requirements.txt
```

The current MVP uses the Python standard library only.

## Start the GUI

```powershell
python run_gui.py
```

## Configure Abaqus

Open `Settings` in the GUI and set your local Abaqus command path, for example:

```text
D:\ABAQUS2024\Commands\abq2024.bat
```

Each user's machine may have a different Abaqus installation path. The path
must point to that user's own Abaqus command script.

You can also set:

- default CPU count, such as `12` or `14`
- GPU count, such as `1`
- whether to run `datacheck`
- whether to run the full analysis after datacheck

## How Jobs Are Run

For each queued job, `abqjobpilot` uses the `.inp` file directory as the Abaqus
working directory.

That means Abaqus output files such as:

```text
*.odb
*.sta
*.msg
*.dat
*.log
```

are written next to the source `.inp` file.

The tool's own runtime metadata is written under:

```text
runtime/
```

## Agent Command Console

The Agent Command Console is not a system shell. It only accepts a small set of
internal commands parsed by `abqjobpilot`.

Supported commands:

```text
enqueue --inp "D:\path\Job_xxx.inp" --cpus 14 --gpus 1
enqueue-folder --folder "D:\path\strategy_folder" --pattern "*.inp" --cpus 14 --gpus 1
list
help
clear
```

Examples:

```text
enqueue --inp "D:\Projects\models\batch_a\strategy_01\Job_test.inp" --batch batch_a --strategy strategy_01
enqueue --inp "D:\Projects\models\batch_b\strategy_02\Job_test.inp" --cpus 12 --gpus 1
enqueue-folder --folder "D:\Projects\models\batch_c\strategy_03" --pattern "*.inp"
list
```

If `--cpus` or `--gpus` is omitted, the GUI settings are used.

## Runtime Files

Generated runtime files are intentionally ignored by git:

```text
runtime/queue.json
runtime/live_status.json
runtime/settings.json
runtime/logs/
runtime/reports/
```

The application creates them automatically when needed.

## Safety Notes

- The Agent Command Console does not call arbitrary shell commands.
- The runner calls Abaqus through an argument list and avoids `shell=True`.
- `Start Queue` is the action that actually submits Abaqus jobs.
- Make sure the queue and settings are correct before starting a run.

## Project Layout

```text
abqjobpilot/
  __init__.py
  command_console.py
  command_parser.py
  config.py
  gui_app.py
  monitor.py
  parsers.py
  queue_store.py
  runner_core.py
  settings_store.py
  utils.py
runtime/
  logs/
  reports/
tests/
  fixtures/
  test_command_parser.py
  test_parsers.py
  test_runner_core.py
run_gui.py
requirements.txt
```

## Tests

Run offline tests:

```powershell
python -m unittest discover -s tests -v
```

The tests do not submit Abaqus jobs.

## Status

Current stage: usable MVP for local Abaqus queue execution and monitoring.

Planned improvements:

- More precise failure categories: license, input, numerical, interrupted.
- Explicit rerun and resume controls.
- Structured `.sta` table parsing.
- Markdown reports in addition to JSON reports.
- Optional SQLite queue backend.
- Packaged Windows release.

## License

No license has been selected yet.
