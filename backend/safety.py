"""Safety and security features for the terminal."""

import os
import re
import subprocess
import sys
from typing import List, Set, Optional, Tuple
from pathlib import Path
import tempfile
import signal
import time
from utils import validate_path, colorize_text


class SafetyGuard:
    """Provides security controls and confirmations for potentially dangerous operations."""

    def __init__(self):
        # Safety restrictions have been disabled to allow unrestricted usage.
        self.dangerous_commands = set()
        self.restricted_paths = set()
        self.allowed_extensions = None

    def is_command_safe(self, command: str, args: List[str]) -> Tuple[bool, str]:
        """Check if a command is safe to execute.

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        # Always allow commands now that safety guard is disabled.
        return True, ""

    def confirm_dangerous_action(self, action: str, details: str = "") -> bool:
        """Ask user for confirmation of potentially dangerous action.

        Args:
            action: Description of the action
            details: Additional details about the action

        Returns:
            True if user confirms, False otherwise
        """
        warning_msg = colorize_text(f"⚠️  WARNING: {action}", "yellow")
        print(warning_msg)

        if details:
            print(colorize_text(f"Details: {details}", "yellow"))

        while True:
            response = input(colorize_text("Continue? (yes/no): ", "yellow")).strip().lower()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            else:
                print(colorize_text("Please answer 'yes' or 'no'", "red"))

    def sanitize_environment(self) -> dict:
        """Create a sanitized environment for subprocess execution.

        Returns:
            Sanitized environment dictionary
        """
        # Start with minimal safe environment
        safe_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'HOME': os.path.expanduser('~'),
            'USER': os.getenv('USER', 'unknown'),
            'LANG': 'en_US.UTF-8',
            'TERM': 'xterm-256color'
        }

        # Add Python path if in virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            safe_env['VIRTUAL_ENV'] = sys.prefix
            safe_env['PATH'] = f"{sys.prefix}/bin:{safe_env['PATH']}"

        return safe_env


class ProcessSandbox:
    """Provides process isolation and resource limits."""

    def __init__(self, timeout: int = 30, max_memory_mb: int = 512):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.temp_dir = None

    def __enter__(self):
        """Enter sandbox context."""
        # Create temporary directory for sandboxed operations
        self.temp_dir = tempfile.mkdtemp(prefix="pyterm_sandbox_")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context and cleanup."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass  # Best effort cleanup

    def run_sandboxed(self, command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Run a command in a sandboxed environment.

        Args:
            command: Command and arguments as list
            cwd: Working directory (defaults to sandbox temp dir)

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if cwd is None:
            cwd = self.temp_dir

        # Validate working directory
        if cwd and not validate_path(cwd):
            raise ValueError(f"Unsafe working directory: {cwd}")

        # Create safe environment
        safety_guard = SafetyGuard()
        safe_env = safety_guard.sanitize_environment()

        try:
            # Set up process with resource limits
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                env=safe_env,
                preexec_fn=self._set_limits if os.name == 'posix' else None
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                return process.returncode, stdout, stderr
            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                process.kill()
                process.wait()
                return -1, "", f"Process timed out after {self.timeout} seconds"

        except Exception as e:
            return -1, "", f"Error running command: {str(e)}"

    def _set_limits(self):
        """Set resource limits for the process (Unix only)."""
        try:
            import resource

            # Set memory limit
            memory_limit = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

            # Set CPU time limit
            cpu_limit = self.timeout
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))

            # Prevent core dumps
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

        except ImportError:
            pass  # resource module not available


class PathGuard:
    """Guards against dangerous file system operations."""

    def __init__(self, working_directory: str):
        self.working_directory = Path(working_directory).resolve()
        self.sandbox_root = self.working_directory
        self.safety_guard = SafetyGuard()

    def validate_file_operation(self, path: str, operation: str) -> Tuple[bool, str]:
        """Validate if a file operation is safe.

        Args:
            path: File or directory path
            operation: Type of operation (read, write, delete, execute)

        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        try:
            Path(path).resolve()
        except Exception as e:
            return False, f"Invalid path: {str(e)}"

        return True, ""

    def get_safe_path(self, path: str) -> Optional[Path]:
        """Get a safe, resolved path if valid.

        Args:
            path: Input path

        Returns:
            Resolved Path object if safe, None otherwise
        """
        try:
            return Path(path).resolve()
        except Exception:
            return None


def resolve_in_sandbox(path: str, sandbox_root: Path) -> Path:
    """Resolve a path without sandbox enforcement.

    Args:
        path: Path to resolve
        sandbox_root: Sandbox root directory

    Returns:
        Resolved Path object

    Raises:
        OSError: If path cannot be resolved
    """
    try:
        resolved_path = Path(path).resolve()
    except Exception as e:
        raise OSError(f"Cannot resolve path '{path}': {str(e)}")

    return resolved_path


def confirm(prompt: str) -> bool:
    """Ask user for y/N confirmation.

    Args:
        prompt: Confirmation prompt text

    Returns:
        True if user confirms with 'y' or 'yes', False otherwise
    """
    try:
        while True:
            response = input(f"{prompt} (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("Please answer 'y' or 'n'")
    except (EOFError, KeyboardInterrupt):
        print()  # New line after Ctrl+C
        return False
