# Development Prompts and Documentation

This file contains the original development prompts and requirements used to build the Python Terminal project.

## Original Master Prompt

### Project Overview
Build PS1 "Python Command Terminal" - Create a complete, runnable project named pyterm that implements a safe, Python-based command terminal with system monitoring. Provide a CLI REPL as the primary interface, and (optionally) a minimal web UI for a hosted demo. Use only local execution; no external code execution services.

### Project Layout Required
```
pyterm/
  backend/
    terminal.py        # CLI REPL entrypoint
    commands.py        # built-in commands
    runner.py          # external command runner (subprocess)
    sysmon.py          # CPU/memory/process monitoring
    safety.py          # sandbox, path guards, confirmations
    utils.py           # parsing, formatting, helpers
    app.py             # optional FastAPI API for web UI
    requirements.txt
    run_cli.sh
    run_cli.bat
    run_api.sh
    run_api.bat
  frontend/            # optional web UI for hosted demo
    index.html
    app.js
    styles.css
  tests/
    smoke.md           # quick manual test script
  .gitignore
  README.md
  codemate_prompts/PROMPTS.md
```

### Dependencies (backend/requirements.txt)
Pin minimal packages:
- psutil==6.0.0
- fastapi==0.115.0 (for optional web API)
- uvicorn==0.30.6 (for optional web API)

### Core Features (Must Implement)

#### CLI REPL with prompt: `pyterm:<cwd>$`

#### Built-in commands (Python-native; no subprocess):

- **pwd** → print current directory
- **ls [-a] [-l]** → list directory (support dotfiles, long view: perms/size/mtime)
- **cd <path>** → change directory (relative/absolute)
- **mkdir <dir> [-p]**
- **rmdir <dir>** → remove empty dir
- **rm <file> [-f]** or **rm -r <dir>** with confirmation unless -f
- **touch <file>**
- **cat <file>** → print (limit huge files with a safe max, e.g., first 200KB)
- **echo <text>** → print text (support simple > file and >> file)
- **clear** → clear screen
- **help** → list commands & usage
- **sysinfo** → show CPU %, Memory %, and top 5 processes by CPU
- **exit / quit** → exit REPL

#### External commands:
If not a built-in, run via subprocess.run (no shell=True), pass argv safely, capture stdout/stderr, bounded by timeout (e.g., 10s), show return code.

#### Error handling:
User-friendly messages for FileNotFoundError, PermissionError, bad args, etc.

### Safety Rails (Important)

#### Sandbox root:
On startup, set allowed root to the directory where terminal.py runs; disallow operations that escape root. Normalize & validate paths with Path(path).resolve() and ensure they're under the allowed root. Print "blocked by sandbox" if violation.

#### Destructive ops:
- rm -r and rm without -f must prompt y/N confirmation in CLI.
- Block attempts on root of sandbox (e.g., rm -r . at sandbox root) unless --i-understand special flag (still ask).

#### Resource limits:
- Cap output (e.g., print first 5000 chars; show "[truncated]").
- Timeouts for external commands (10s).
- Disallow background operators &, pipes |, and ; in external mode (we'll implement minimal >/>> redirection only for echo builtin).

### Optional Web UI Features

#### Minimal FastAPI backend:
- POST /api/execute → {"command": "ls"} returns {"output": "...", "return_code": 0}
- GET /api/sysinfo → CPU/mem/processes JSON
- GET / → serve frontend/index.html

#### Frontend features:
- Terminal-like interface (dark theme)
- Input field that sends commands to /api/execute
- Display command history and output
- Show current directory in header
- Optional: mini system monitor widget

### Implementation Notes

1. **Safety first**: All file operations must validate paths, check permissions, and stay within sandbox
2. **No shell injection**: Never use shell=True or pass raw strings to shell
3. **Resource limits**: Prevent runaway processes or massive output
4. **Error handling**: Graceful degradation with helpful error messages
5. **User experience**: Familiar terminal behavior with safety improvements

### Testing Requirements

Create tests/smoke.md with manual test cases for:
- Basic command functionality
- Safety restrictions
- Error conditions
- Web interface (if implemented)

### Documentation Requirements

README.md should include:
- Quick start instructions
- Command reference
- Safety feature explanation
- API documentation (if web interface implemented)
- Installation and setup instructions

## Development Notes

### Key Design Decisions

1. **Pure Python Implementation**: All built-in commands implemented in Python for safety and portability
2. **Sandboxing**: Strict path validation and working directory restrictions
3. **Resource Limits**: Output truncation and command timeouts prevent resource exhaustion
4. **Safety Confirmations**: Dangerous operations require explicit user confirmation
5. **Web Interface**: Optional FastAPI backend provides web access while maintaining security

### Security Considerations

1. **Path Traversal Prevention**: All paths validated and normalized
2. **Command Injection Prevention**: No shell=True usage, argument validation
3. **Resource Protection**: Memory and CPU limits on external processes
4. **File Type Restrictions**: Limited operations on executable files
5. **System Path Protection**: Restricted access to critical system directories

### Performance Considerations

1. **Output Truncation**: Large outputs are limited to prevent memory issues
2. **Command Timeouts**: External commands limited to 10 seconds
3. **Process Sandboxing**: Subprocesses run with resource limits
4. **Efficient File Operations**: Stream processing for large files

### Extensibility

1. **Plugin Architecture**: Commands are easily extensible through class methods
2. **API Endpoints**: Web interface can be extended with new endpoints
3. **Frontend Modularity**: JavaScript organized for easy feature addition
4. **Configuration**: Environment variables for key settings

## Future Enhancement Ideas

1. **Advanced Tab Completion**: Complete file paths and command arguments
2. **Command Aliases**: User-defined command shortcuts
3. **Script Execution**: Safe execution of shell scripts
4. **File Editor**: Built-in text editor for file modification
5. **Network Tools**: Safe network diagnostic commands
6. **Advanced Monitoring**: More detailed system metrics and alerts
7. **Multi-user Support**: Session management for multiple users
8. **Plugin System**: External plugin loading and management
9. **Advanced File Operations**: Copy, move, and advanced file manipulation
10. **Terminal Themes**: Customizable color schemes and layouts

## Known Limitations

1. **Windows Compatibility**: Some Unix-specific features may not work on Windows
2. **Binary Files**: Limited support for binary file operations
3. **Large Files**: Memory usage for very large file operations
4. **Network Commands**: No built-in network diagnostic tools
5. **Advanced Shell Features**: No globbing, complex redirection, or job control
6. **Performance**: Python implementation may be slower than native tools
7. **System Integration**: Limited integration with system package managers

## Testing Strategy

1. **Unit Tests**: Test individual command functions
2. **Integration Tests**: Test command combinations and workflows
3. **Security Tests**: Verify safety restrictions work correctly
4. **Performance Tests**: Ensure resource limits are effective
5. **Web Interface Tests**: Verify API and frontend functionality
6. **Cross-platform Tests**: Test on different operating systems
7. **Error Condition Tests**: Verify graceful error handling
8. **Manual Smoke Tests**: User-driven testing scenarios