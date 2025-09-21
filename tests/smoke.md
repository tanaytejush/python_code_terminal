# Smoke Test Script for Python Terminal

This document provides a quick manual test script to verify the basic functionality of the Python Terminal.

## Essential CLI Tests

### 1. Basic Startup & Navigation
```bash
cd backend
./run_cli.sh
```

**Expected**: Terminal starts with welcome message and `pyterm:<cwd>$` prompt

### 2. Core File Operations
```
pwd
ls
cd
mkdir test
touch test/a.txt
echo "hi" > test/a.txt
cat test/a.txt
```

**Expected**:
- `pwd` shows current directory
- `ls` lists contents
- `mkdir test` creates directory
- `touch test/a.txt` creates empty file
- `echo "hi" > test/a.txt` writes content
- `cat test/a.txt` displays "hi"

### 3. Error Cases
```
cat nope.txt
cd nope
rm
```

**Expected**:
- `cat nope.txt` → "File not found" error
- `cd nope` → "Directory not found" error
- `rm` → "rm requires a file or directory name" error

### 4. Safety: Sandbox Escape Prevention
```
cd ..
cd ../../
cd /etc
```

**Expected**: All attempts should be **blocked by sandbox** with message like "blocked by sandbox: path outside allowed root"

### 5. System Information
```
sysinfo
```

**Expected**: Shows:
- CPU and memory usage percentages.
- Top 5 processes with PID, name, and CPU% (list is empty when `psutil` is unavailable/offline).

### 6. External Command Test
**Linux/macOS:**
```
python --version
whoami
```

**Windows:**
```
python --version
dir
```

**Expected**: External commands execute and show:
- Python version output
- Current username or directory listing
- Return code displayed if non-zero

## Streamlit Web Interface Tests (Recommended)

### 1. Start Web Interface

**Option A - From project root (easiest):**
```bash
./run.sh          # Unix/Linux/macOS
run.bat           # Windows
```

**Option B - From backend directory:**
```bash
cd backend
./run_web.sh       # Unix/Linux/macOS
run_web.bat        # Windows
```

**Option C - Using Python launcher:**
```bash
python launcher.py
```

**Expected**:
- 🔧 Environment setup runs automatically
- 📦 Dependencies installed if needed
- 📡 FastAPI backend starts on http://localhost:8000
- 🖥️ Streamlit frontend starts on http://localhost:8501
- 🌐 Browser opens automatically to http://localhost:8501
- ✅ Both services are connected and ready

### 2. Streamlit Frontend Access
- Open browser to http://localhost:8501
- **Expected**: Modern Streamlit interface loads with:
  - Terminal command input area
  - System monitoring sidebar with CPU/Memory gauges
  - Quick command buttons
  - Top processes display

### 3. Streamlit Functionality Test
- Type `ls` in the command input and press Enter or click Execute
- Click the "📁 List Files" quick command button
- Click the "🖥️ System Info" button
- **Expected**:
  - Commands execute and show output in terminal display
  - Quick commands work immediately
  - System monitoring shows real-time data with gauge charts

### 4. Streamlit System Monitor
- Observe the sidebar CPU and Memory gauge charts
- Check the "Top Processes" section
- **Expected**:
  - Gauges show current CPU/Memory percentages
  - Color coding: Green (0-50%), Yellow (50-80%), Red (80-100%)
  - Top 5 processes listed with names and CPU usage

## Legacy Web API Tests (Alternative)

### 1. Start API Server
```bash
cd backend
./run_api.sh
```

**Expected**: Server starts and shows "Starting Python Terminal API on http://0.0.0.0:8000"

### 2. Frontend Access
- Open browser to http://localhost:8000
- **Expected**: Web terminal interface loads with terminal input, output pane, and Sysinfo button

### 3. API Endpoint Tests

#### Test POST /exec
Open browser developer tools and run:
```javascript
fetch('/exec', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({cmd: 'ls'})
}).then(r => r.json()).then(console.log)
```

**Expected**: Response like:
```json
{
  "stdout": "a.txt\ntest/\n",
  "stderr": "",
  "rc": 0,
  "cwd": "/path/to/project/backend"
}
```

#### Test GET /sysinfo
Open: http://localhost:8000/sysinfo

**Expected**: JSON response like:
```json
{
  "cpu_percent": 12.5,
  "mem_percent": 67.2,
  "top": [
    {"pid": 1234, "name": "python", "cpu_percent": 5.2},
    ...
  ]
}
```

### 4. Frontend Integration
- Type `ls` in web terminal input and press Enter
- Click the "Sysinfo" button
- **Expected**:
  - `ls` command executes and shows output in terminal pane
  - Sysinfo button shows system information
  - Current working directory is displayed in header

## Quick Verification Checklist

### Core Functionality
- [ ] Terminal starts with proper prompt
- [ ] `pwd` shows current directory
- [ ] `ls` lists files
- [ ] `mkdir test` creates directory
- [ ] `touch test/a.txt` creates file
- [ ] `echo "hi" > test/a.txt` writes content
- [ ] `cat test/a.txt` shows "hi"

### Error Handling
- [ ] `cat nope.txt` shows file not found error
- [ ] `cd nope` shows directory not found error
- [ ] `rm` shows missing argument error

### Security
- [ ] `cd ..` blocked by sandbox
- [ ] `cd ../../` blocked by sandbox
- [ ] `cd /etc` blocked by sandbox

### System Info
- [ ] `sysinfo` shows CPU percentage
- [ ] `sysinfo` shows memory percentage
- [ ] `sysinfo` shows at least 1 process

### External Commands
- [ ] `python --version` works (or equivalent)
- [ ] `whoami`/`dir` works depending on OS

### Streamlit Web Interface (if tested)
- [ ] Streamlit app starts on port 8501
- [ ] FastAPI backend starts on port 8000
- [ ] Streamlit interface loads properly
- [ ] Command input and execution works
- [ ] Quick command buttons work
- [ ] System monitoring gauges display correctly
- [ ] Top processes list updates
- [ ] Command history is preserved

### Legacy Web API (if tested)
- [ ] Server starts on port 8000
- [ ] Frontend loads at localhost:8000
- [ ] POST /exec with `ls` returns proper JSON
- [ ] GET /sysinfo returns system data
- [ ] Web terminal executes commands
- [ ] Sysinfo button works

## Cleanup
```
rm -rf test
exit
```

## Notes

**Pass Criteria**: All core functionality tests must pass. Security tests are critical - any sandbox escape is a failure.

**Common Issues**:
- On Windows, external commands may need different syntax
- File permissions may cause some operations to fail
- Virtual environment setup may be needed for dependencies

**Debug**: If tests fail, check:
1. Python dependencies installed (`pip install -r requirements.txt`)
2. Working directory is correct (`backend/`)
3. File permissions on shell scripts (`chmod +x *.sh` on Unix)
