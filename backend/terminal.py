#!/usr/bin/env python3
"""Main CLI REPL interface for the Python terminal."""

import os
import sys
import readline
import atexit
from pathlib import Path
from typing import Optional, Dict, Any, List
import traceback

from commands import BuiltinCommands
from runner import CommandRunner
from sysmon import SystemMonitor
from utils import parse_command, colorize_text, format_output
from safety import SafetyGuard


class PythonTerminal:
    """Main terminal interface with REPL functionality."""

    def __init__(self, working_directory: Optional[str] = None):
        # Set up working directory
        if working_directory:
            self.working_directory = Path(working_directory).resolve()
        else:
            self.working_directory = Path.cwd()

        # Initialize components
        self.builtin_commands = BuiltinCommands(str(self.working_directory))
        self.command_runner = CommandRunner(str(self.working_directory))
        self.system_monitor = SystemMonitor()
        self.safety_guard = SafetyGuard()

        # Set up readline history
        self.history_file = Path.home() / '.pyterm_history'
        self._setup_readline()

        # Command history for session
        self.command_history = []

        # Exit flag
        self.should_exit = False

        print(colorize_text("Python Command Terminal (pyterm) v1.0", "green"))
        print(colorize_text("Type 'help' for available commands, 'exit' to quit", "cyan"))
        print()

    def _setup_readline(self):
        """Set up readline for command history and completion."""
        try:
            # Load history
            if self.history_file.exists():
                readline.read_history_file(str(self.history_file))

            # Limit history size
            readline.set_history_length(1000)

            # Save history on exit
            atexit.register(self._save_history)

            # Set up tab completion
            readline.set_completer(self._complete_command)
            readline.parse_and_bind('tab: complete')

        except Exception:
            # readline not available or other error
            pass

    def _save_history(self):
        """Save command history to file."""
        try:
            readline.write_history_file(str(self.history_file))
        except Exception:
            pass

    def _complete_command(self, text: str, state: int) -> Optional[str]:
        """Tab completion for commands."""
        try:
            if state == 0:
                # First call - generate completions
                line = readline.get_line_buffer()
                parts = line.split()

                if not parts or (len(parts) == 1 and not line.endswith(' ')):
                    # Completing command name
                    builtin_commands = list(self.builtin_commands.get_builtin_commands().keys())
                    builtin_commands.extend(['sysinfo', 'exit', 'quit'])

                    self.completions = [
                        cmd for cmd in builtin_commands
                        if cmd.startswith(text)
                    ]
                else:
                    # Completing file/directory names
                    try:
                        if text.startswith('/'):
                            # Absolute path
                            base_dir = Path(text).parent if '/' in text[1:] else Path('/')
                            prefix = Path(text).name
                        elif text.startswith('~'):
                            # Home directory
                            expanded = os.path.expanduser(text)
                            base_dir = Path(expanded).parent if '/' in expanded else Path.home()
                            prefix = Path(expanded).name
                        else:
                            # Relative path
                            base_dir = self.working_directory
                            if '/' in text:
                                base_dir = base_dir / Path(text).parent
                                prefix = Path(text).name
                            else:
                                prefix = text

                        if base_dir.exists() and base_dir.is_dir():
                            self.completions = []
                            try:
                                # Only show items that are within sandbox for safety
                                is_safe, _ = self.builtin_commands.path_guard.validate_file_operation(str(base_dir), 'read')
                                if is_safe:
                                    for item in base_dir.iterdir():
                                        if item.name.startswith(prefix):
                                            # Skip hidden files unless prefix starts with dot
                                            if item.name.startswith('.') and not prefix.startswith('.'):
                                                continue
                                            if item.is_dir():
                                                self.completions.append(item.name + '/')
                                            else:
                                                self.completions.append(item.name)
                            except (PermissionError, OSError):
                                pass  # Skip directories we can't read
                        else:
                            self.completions = []

                    except Exception:
                        self.completions = []

            # Return completion
            if state < len(self.completions):
                return self.completions[state]
            else:
                return None

        except Exception:
            return None

    def _find_common_prefix(self, strings: List[str]) -> str:
        """Find common prefix among a list of strings."""
        if not strings:
            return ''
        if len(strings) == 1:
            return strings[0]

        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ''
        return prefix

    def get_prompt(self) -> str:
        """Generate the command prompt."""
        # Get current directory relative to home if possible
        try:
            cwd = self.builtin_commands.get_cwd()
            home = str(Path.home())

            if cwd.startswith(home):
                display_path = '~' + cwd[len(home):]
            else:
                display_path = cwd

            # Limit path length
            if len(display_path) > 40:
                display_path = '...' + display_path[-37:]

        except Exception:
            display_path = str(self.working_directory)

        return colorize_text(f"pyterm:{display_path}$ ", "blue")

    def execute_command(self, user_input: str) -> str:
        """Execute a command and return the result.

        Args:
            user_input: Raw user input

        Returns:
            Command output or error message
        """
        if not user_input.strip():
            return ""

        # Parse command
        command, args = parse_command(user_input)

        if not command:
            return ""

        # Add to history
        self.command_history.append(user_input.strip())

        try:
            # Handle exit commands
            if command.lower() in ['exit', 'quit']:
                self.should_exit = True
                return colorize_text("Goodbye!", "green")

            # Handle sysinfo command
            if command.lower() == 'sysinfo':
                sysinfo = self.system_monitor.get_sysinfo(top_n=5)

                if 'error' in sysinfo:
                    return colorize_text(f"System info error: {sysinfo['error']}", "red")

                cpu_percent_text = colorize_text(f"{sysinfo['cpu_percent']:.1f}%", "yellow")
                memory_percent_text = colorize_text(f"{sysinfo['mem_percent']:.1f}%", "yellow")

                lines = [
                    colorize_text("=== SYSTEM INFO ===", "blue"),
                    f"CPU Usage: {cpu_percent_text}",
                    f"Memory Usage: {memory_percent_text}",
                    "",
                    colorize_text("Top 5 Processes by CPU:", "green")
                ]

                for proc in sysinfo['top']:
                    lines.append(f"  {proc['pid']:<6} {proc['name']:<20} {proc['cpu_percent']:.1f}%")

                return '\n'.join(lines)

            # Check for built-in commands
            builtin_commands = self.builtin_commands.get_builtin_commands()

            if command in builtin_commands:
                # Execute built-in command
                result = builtin_commands[command](args)

                # Update working directory if it changed
                new_cwd = self.builtin_commands.get_cwd()
                if new_cwd != str(self.working_directory):
                    self.working_directory = Path(new_cwd)
                    self.command_runner.working_directory = self.working_directory

                return result

            else:
                # Execute external command
                return_code, stdout, stderr = self.command_runner.run_external_command(command, args)

                # Format output
                output_parts = []

                if stdout:
                    output_parts.append(stdout.rstrip())

                if stderr:
                    error_output = colorize_text(stderr.rstrip(), "red")
                    output_parts.append(error_output)

                # Show return code if non-zero
                if return_code != 0:
                    return_code_msg = colorize_text(f"[Return code: {return_code}]", "yellow")
                    output_parts.append(return_code_msg)

                return "\n".join(output_parts) if output_parts else ""

        except KeyboardInterrupt:
            return colorize_text("\nCommand interrupted", "yellow")
        except Exception as e:
            error_msg = colorize_text(f"Error executing command: {str(e)}", "red")
            if "--debug" in args:
                error_msg += "\n" + traceback.format_exc()
            return error_msg

    def run_repl(self):
        """Run the main REPL loop."""
        try:
            while not self.should_exit:
                try:
                    # Get user input
                    prompt = self.get_prompt()
                    user_input = input(prompt)

                    # Execute command
                    result = self.execute_command(user_input)

                    # Display result
                    if result:
                        print(result)

                except KeyboardInterrupt:
                    print(colorize_text("\nUse 'exit' or 'quit' to exit", "yellow"))
                    continue

                except EOFError:
                    # Ctrl+D pressed
                    print(colorize_text("\nGoodbye!", "green"))
                    break

        except Exception as e:
            print(colorize_text(f"Terminal error: {str(e)}", "red"))
            sys.exit(1)

    def run_single_command(self, command: str) -> int:
        """Run a single command and exit.

        Args:
            command: Command to execute

        Returns:
            Exit code
        """
        try:
            result = self.execute_command(command)

            if result:
                print(result)

            return 0

        except Exception as e:
            print(colorize_text(f"Error: {str(e)}", "red"), file=sys.stderr)
            return 1

    def show_version(self):
        """Show version information."""
        print("Python Command Terminal (pyterm) v1.0")
        print(f"Python version: {sys.version}")
        print(f"Platform: {sys.platform}")

    def show_help(self):
        """Show help information."""
        help_text = """
Usage: python terminal.py [options] [command]

Options:
  -h, --help     Show this help message
  -v, --version  Show version information
  -c COMMAND     Execute a single command and exit
  -d DIR         Set working directory

Examples:
  python terminal.py                    # Start interactive mode
  python terminal.py -c "ls -la"       # Execute single command
  python terminal.py -d /tmp           # Start with /tmp as working directory

Interactive Commands:
  Type 'help' in the terminal for available commands
  Use Tab for command and file completion
  Use Ctrl+C to interrupt running commands
  Use Ctrl+D or 'exit' to quit
"""
        print(help_text.strip())


def main():
    """Main entry point for the terminal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Python Command Terminal",
        add_help=False  # We'll handle help ourselves
    )

    parser.add_argument('-h', '--help', action='store_true',
                        help='Show help message')
    parser.add_argument('-v', '--version', action='store_true',
                        help='Show version information')
    parser.add_argument('-c', '--command', type=str,
                        help='Execute a single command and exit')
    parser.add_argument('-d', '--directory', type=str,
                        help='Set working directory')

    args, unknown = parser.parse_known_args()

    # Handle help
    if args.help:
        terminal = PythonTerminal()
        terminal.show_help()
        return 0

    # Handle version
    if args.version:
        terminal = PythonTerminal()
        terminal.show_version()
        return 0

    try:
        # Create terminal instance
        terminal = PythonTerminal(working_directory=args.directory)

        # Handle single command execution
        if args.command:
            return terminal.run_single_command(args.command)

        # Handle remaining arguments as a command
        if unknown:
            command = ' '.join(unknown)
            return terminal.run_single_command(command)

        # Start interactive mode
        terminal.run_repl()
        return 0

    except KeyboardInterrupt:
        print(colorize_text("\nGoodbye!", "green"))
        return 0
    except Exception as e:
        print(colorize_text(f"Fatal error: {str(e)}", "red"), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
