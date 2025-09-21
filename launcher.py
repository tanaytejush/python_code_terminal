#!/usr/bin/env python3
"""
Unified launcher for Python Terminal Web Interface.
Starts both FastAPI backend and Streamlit frontend together.
"""

import os
import sys
import time
import signal
import shutil
import subprocess
from urllib import request as urllib_request
from urllib.error import URLError
from pathlib import Path


class TerminalLauncher:
    """Manages startup and coordination of frontend and backend services."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.api_process = None
        self.streamlit_process = None
        self.should_exit = False

    def setup_environment(self):
        """Set up virtual environment and dependencies."""
        venv_dir = self.backend_dir / ".venv"

        print("🔧 Setting up environment...")

        # Create virtual environment if it doesn't exist
        needs_rebuild = False

        if venv_dir.exists():
            bin_dir = venv_dir / ("Scripts" if os.name == 'nt' else "bin")
            pip_candidate = bin_dir / "pip"
            expected_python = bin_dir / ("python.exe" if os.name == 'nt' else "python")
            try:
                first_line = pip_candidate.read_text().splitlines()[0]
                if not first_line.startswith("#!" + str(expected_python)):
                    needs_rebuild = True
            except Exception:
                needs_rebuild = True
        else:
            needs_rebuild = True

        if needs_rebuild:
            if venv_dir.exists():
                print("Refreshing virtual environment...")
                shutil.rmtree(venv_dir)
            else:
                print("Creating virtual environment...")

            subprocess.run([
                sys.executable, "-m", "venv", str(venv_dir)
            ], check=True)

        # Get pip executable path
        if os.name == 'nt':
            pip_path = venv_dir / "Scripts" / "pip.exe"
            python_path = venv_dir / "Scripts" / "python.exe"
        else:
            pip_path = venv_dir / "bin" / "pip"
            python_path = venv_dir / "bin" / "python"

        if not pip_path.exists():
            print("Bootstrapping pip inside virtual environment...")
            subprocess.run([str(python_path), "-m", "ensurepip", "--upgrade"], check=True)

        # Install dependencies
        print("Installing dependencies...")
        install_cmd = [
            str(pip_path),
            "install",
            "--timeout",
            "5",
            "--retries",
            "1",
            "-r",
            str(self.backend_dir / "requirements.txt")
        ]

        try:
            subprocess.run(install_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="ignore").strip()
            if stderr:
                print(f"⚠️  Dependency install failed (continuing anyway): {stderr.splitlines()[-1]}")
            else:
                print("⚠️  Dependency install failed (continuing anyway).")

        return python_path

    def wait_for_api(self, timeout=30):
        """Wait for API to be ready."""
        print("⏳ Waiting for backend to start...")

        for i in range(timeout):
            try:
                with urllib_request.urlopen("http://localhost:8000/health", timeout=2) as response:
                    if response.status == 200:
                        print("✅ Backend ready!")
                        return True
            except URLError:
                pass

            if self.api_process and self.api_process.poll() is not None:
                print("❌ Backend process exited early. Check dependency installation.")
                return False

            time.sleep(1)

        print("❌ Backend failed to start within timeout")
        return False

    def start_api(self, python_path):
        """Start FastAPI backend."""
        print("📡 Starting FastAPI backend (http://localhost:8000)...")

        api_cmd = [
            str(python_path), "-m", "uvicorn",
            "app:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "warning"
        ]

        self.api_process = subprocess.Popen(
            api_cmd,
            cwd=str(self.backend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def start_streamlit(self, python_path):
        """Start Streamlit frontend."""
        print("🖥️  Starting Streamlit frontend (http://localhost:8501)...")

        streamlit_cmd = [
            str(python_path), "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.serverAddress", "localhost",
            "--browser.gatherUsageStats", "false"
        ]

        try:
            self.streamlit_process = subprocess.Popen(
                streamlit_cmd,
                cwd=str(self.frontend_dir)
            )
        except FileNotFoundError:
            print("❌ Streamlit executable not found. Ensure dependencies are installed.")
            self.streamlit_process = None

    def cleanup(self):
        """Stop all services."""
        print("\n🛑 Stopping all services...")

        if self.streamlit_process:
            self.streamlit_process.terminate()
            try:
                self.streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()

        if self.api_process:
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()

        print("All services stopped. Goodbye! 👋")

    def signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.should_exit = True
        self.cleanup()
        sys.exit(0)

    def run(self):
        """Main run method."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            print("🐍 Python Terminal Web Interface")
            print("=" * 35)
            print("Starting integrated frontend and backend...\n")

            # Setup environment
            python_path = self.setup_environment()

            # Start API backend
            self.start_api(python_path)

            # Wait for API to be ready
            if not self.wait_for_api():
                self.cleanup()
                return 1

            # Start Streamlit frontend
            self.start_streamlit(python_path)

            if not self.streamlit_process or self.streamlit_process.poll() is not None:
                print("❌ Frontend process exited early. Ensure Streamlit is installed.")
                self.cleanup()
                return 1

            print("\n🎉 Both services are running!")
            print("   Frontend: http://localhost:8501")
            print("   Backend:  http://localhost:8000")
            print("\n💡 The frontend will open in your browser automatically")
            print("🛑 Press Ctrl+C to stop both services\n")

            # Wait for Streamlit to exit
            try:
                self.streamlit_process.wait()
            except KeyboardInterrupt:
                pass

            self.cleanup()
            return 0

        except Exception as e:
            print(f"❌ Error: {e}")
            self.cleanup()
            return 1


def main():
    """Main entry point."""
    launcher = TerminalLauncher()
    return launcher.run()


if __name__ == "__main__":
    sys.exit(main())
