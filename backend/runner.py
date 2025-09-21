"""External command runner with subprocess management."""

import subprocess
import signal
import os
import sys
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from safety import ProcessSandbox, SafetyGuard
from utils import colorize_text, truncate_output


class CommandRunner:
    """Handles execution of external commands via subprocess."""

    def __init__(self, working_directory: str, timeout: int = 10):
        self.working_directory = Path(working_directory)
        self.timeout = timeout
        self.safety_guard = SafetyGuard()

    def run_external(self, argv: List[str], cwd: Path, timeout: int = 10) -> Tuple[int, str, str]:
        """Run an external command safely.

        Args:
            argv: Command and arguments as list
            cwd: Working directory
            timeout: Command timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if not argv:
            return 1, "", "No command provided"

        command = argv[0]
        args = argv[1:]

        # Safety check
        is_safe, reason = self.safety_guard.is_command_safe(command, args)
        if not is_safe:
            error_msg = colorize_text(f"Blocked unsafe command: {reason}", "red")
            return 1, "", error_msg

        try:
            # Use ProcessSandbox for additional safety
            with ProcessSandbox(timeout=timeout) as sandbox:
                return_code, stdout, stderr = sandbox.run_sandboxed(
                    argv,
                    cwd=str(cwd)
                )

                # Truncate output if too long
                stdout = truncate_output(stdout, max_lines=100)
                stderr = truncate_output(stderr, max_lines=50)

                return return_code, stdout, stderr

        except FileNotFoundError:
            error_msg = colorize_text(f"Command not found: {command}", "red")
            return 127, "", error_msg
        except PermissionError:
            error_msg = colorize_text(f"Permission denied: {command}", "red")
            return 126, "", error_msg
        except Exception as e:
            error_msg = colorize_text(f"Error executing command: {str(e)}", "red")
            return 1, "", error_msg

    def run_external_command(self, command: str, args: List[str]) -> Tuple[int, str, str]:
        """Legacy wrapper for run_external.

        Args:
            command: Command name/path
            args: Command arguments

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        argv = [command] + args
        return self.run_external(argv, self.working_directory, self.timeout)

    def run_command_with_input(self, command: str, args: List[str],
                              input_data: str = None) -> Tuple[int, str, str]:
        """Run a command with stdin input.

        Args:
            command: Command name/path
            args: Command arguments
            input_data: Data to send to stdin

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        # Safety check
        is_safe, reason = self.safety_guard.is_command_safe(command, args)
        if not is_safe:
            error_msg = colorize_text(f"Blocked unsafe command: {reason}", "red")
            return 1, "", error_msg

        cmd_list = [command] + args

        try:
            # Create safe environment
            safe_env = self.safety_guard.sanitize_environment()

            # Run with input
            process = subprocess.Popen(
                cmd_list,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.working_directory),
                env=safe_env
            )

            try:
                stdout, stderr = process.communicate(
                    input=input_data,
                    timeout=self.timeout
                )

                # Truncate output
                stdout = truncate_output(stdout, max_lines=100)
                stderr = truncate_output(stderr, max_lines=50)

                return process.returncode, stdout, stderr

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                error_msg = colorize_text(f"Command timed out after {self.timeout} seconds", "red")
                return -1, "", error_msg

        except FileNotFoundError:
            error_msg = colorize_text(f"Command not found: {command}", "red")
            return 127, "", error_msg
        except Exception as e:
            error_msg = colorize_text(f"Error executing command: {str(e)}", "red")
            return 1, "", error_msg

    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH.

        Args:
            command: Command name to check

        Returns:
            True if command exists and is executable
        """
        try:
            # Use 'which' on Unix-like systems or 'where' on Windows
            if os.name == 'nt':
                check_cmd = ['where', command]
            else:
                check_cmd = ['which', command]

            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            return result.returncode == 0

        except Exception:
            return False

    def get_command_help(self, command: str) -> str:
        """Get help text for a command.

        Args:
            command: Command name

        Returns:
            Help text or error message
        """
        if not self.check_command_exists(command):
            return colorize_text(f"Command not found: {command}", "red")

        # Try common help flags
        help_flags = ['--help', '-h', '-?']

        for flag in help_flags:
            try:
                return_code, stdout, stderr = self.run_external_command(command, [flag])

                if return_code == 0 and stdout.strip():
                    return stdout
                elif stderr.strip():
                    return stderr

            except Exception:
                continue

        # Try 'man' command on Unix systems
        if os.name != 'nt':
            try:
                return_code, stdout, stderr = self.run_external_command('man', [command])
                if return_code == 0 and stdout.strip():
                    return stdout
            except Exception:
                pass

        return colorize_text(f"No help available for command: {command}", "yellow")

    def list_available_commands(self) -> List[str]:
        """List available commands in PATH.

        Returns:
            List of available command names
        """
        commands = set()

        try:
            # Get PATH directories
            path_env = os.environ.get('PATH', '')
            path_dirs = path_env.split(os.pathsep)

            for path_dir in path_dirs:
                try:
                    path_obj = Path(path_dir)
                    if path_obj.exists() and path_obj.is_dir():
                        for item in path_obj.iterdir():
                            if item.is_file() and os.access(item, os.X_OK):
                                commands.add(item.name)
                except Exception:
                    continue

        except Exception:
            pass

        return sorted(list(commands))

    def run_python_script(self, script_path: str, args: List[str] = None) -> Tuple[int, str, str]:
        """Run a Python script safely.

        Args:
            script_path: Path to Python script
            args: Arguments to pass to script

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if args is None:
            args = []

        script_path_obj = Path(script_path)

        # Validate script path
        if not script_path_obj.exists():
            error_msg = colorize_text(f"Script not found: {script_path}", "red")
            return 1, "", error_msg

        if not script_path_obj.is_file():
            error_msg = colorize_text(f"Not a file: {script_path}", "red")
            return 1, "", error_msg

        if script_path_obj.suffix != '.py':
            error_msg = colorize_text(f"Not a Python file: {script_path}", "red")
            return 1, "", error_msg

        # Use current Python interpreter
        python_cmd = sys.executable
        cmd_args = [str(script_path_obj)] + args

        return self.run_external_command(python_cmd, cmd_args)

    def run_shell_builtin(self, builtin: str, args: List[str]) -> Tuple[int, str, str]:
        """Run shell built-in commands (limited set).

        Args:
            builtin: Built-in command name
            args: Command arguments

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        # Only allow safe shell builtins
        safe_builtins = {
            'echo': self._builtin_echo,
            'env': self._builtin_env,
            'export': self._builtin_export,
            'unset': self._builtin_unset,
            'type': self._builtin_type,
        }

        if builtin not in safe_builtins:
            error_msg = colorize_text(f"Shell builtin not supported: {builtin}", "red")
            return 1, "", error_msg

        try:
            return safe_builtins[builtin](args)
        except Exception as e:
            error_msg = colorize_text(f"Error in builtin {builtin}: {str(e)}", "red")
            return 1, "", error_msg

    def _builtin_echo(self, args: List[str]) -> Tuple[int, str, str]:
        """Echo builtin implementation."""
        output = ' '.join(args) + '\n'
        return 0, output, ""

    def _builtin_env(self, args: List[str]) -> Tuple[int, str, str]:
        """Env builtin implementation."""
        env_vars = []
        for key, value in sorted(os.environ.items()):
            env_vars.append(f"{key}={value}")
        return 0, '\n'.join(env_vars) + '\n', ""

    def _builtin_export(self, args: List[str]) -> Tuple[int, str, str]:
        """Export builtin implementation (read-only for safety)."""
        if not args:
            return self._builtin_env([])

        # For safety, don't actually modify environment
        return 0, f"Export (read-only): {' '.join(args)}\n", ""

    def _builtin_unset(self, args: List[str]) -> Tuple[int, str, str]:
        """Unset builtin implementation (read-only for safety)."""
        # For safety, don't actually modify environment
        return 0, f"Unset (read-only): {' '.join(args)}\n", ""

    def _builtin_type(self, args: List[str]) -> Tuple[int, str, str]:
        """Type builtin implementation."""
        if not args:
            return 1, "", "type: missing argument\n"

        command = args[0]

        if self.check_command_exists(command):
            return 0, f"{command} is a command\n", ""
        else:
            return 1, "", f"type: {command}: not found\n"