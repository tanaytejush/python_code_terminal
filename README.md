# PyTerm: A Python-Based Command Terminal

A safe, modular command terminal written in Python. It was my entry for **Problem Statement 1 (Python-Based Command Terminal)** at the CodeMate Hackathon, which asked for a terminal that reproduces core shell behaviour with efficiency, correctness and extensibility.

PyTerm runs as a classic command-line REPL, and also has a web interface (FastAPI backend + Streamlit frontend) for easy demos and hosting.

## Features

- **Core commands built natively in Python**: `ls`, `cd`, `pwd`, `mkdir`, `rm`, `touch`, `cat`, `echo`, `clear`, `help`
- **System monitoring**: a custom `sysinfo` command shows CPU and memory usage plus top processes
- **External command execution** with timeouts and output truncation
- **Safety first**: sandboxing keeps operations inside the working directory, and destructive commands ask for confirmation
- **Clear error messages**
- **Two interfaces**: CLI REPL and an optional web UI

## Operational safeguards

- Very large output is truncated
- Long-running external commands are terminated automatically
- All commands are sandboxed to the project environment

## Quick start

```bash
git clone https://github.com/tanaytejush/python_code_terminal.git
cd python_code_terminal
```

**Web interface** (creates a virtual environment, installs dependencies, starts the backend on port 8000 and Streamlit on port 8501):

```bash
./run.sh        # Linux/macOS
run.bat         # Windows
```

**CLI only**:

```bash
cd backend
./run_cli.sh    # or run_cli.bat on Windows
```

Other launchers in `backend/`: `run_api` (FastAPI only), `run_streamlit` (UI only) and `run_web`.

## Project structure

```
launcher.py        One-command setup and launch
backend/
  terminal.py      Terminal REPL
  commands.py      Built-in commands
  safety.py        Sandboxing and confirmations
  sysmon.py        sysinfo command
  runner.py        External command execution
  app.py           FastAPI app
frontend/app.py    Streamlit UI
tests/smoke.md     Manual smoke tests
codemate_prompts/  Prompts used during development
```

## Tech stack

Python, FastAPI, Streamlit

## Built with

Built entirely in Python with help from CodeMate Build and the CodeMate Extension. The modular design makes it easy to add command history, auto-completion or natural language command interpretation.

## License

See [LICENSE](LICENSE).
