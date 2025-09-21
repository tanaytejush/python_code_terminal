"""Built-in commands for the Python terminal."""

import os
import stat
import time
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from utils import (
    parse_flags, human_size, format_mtime, format_perms,
    colorize_text, sanitize_filename, truncate_output
)
from safety import PathGuard, SafetyGuard

IS_MAC = sys.platform == "darwin"

class BuiltinCommands:
    """Handler for built-in terminal commands."""

    def __init__(self, working_directory: str = None):
        self.cwd = Path(working_directory or os.getcwd()).resolve()
        # Set sandbox root to the project root for broader access
        project_root = self.cwd.parent if self.cwd.name == "backend" else self.cwd
        self.path_guard = PathGuard(str(project_root))
        self.safety_guard = SafetyGuard()

    def get_cwd(self) -> str:
        """Get current working directory."""
        return str(self.cwd)

    def pwd(self, args: List[str]) -> str:
        """Print current working directory."""
        return str(self.cwd)

    def cd(self, args: List[str]) -> str:
        """Change directory."""
        if not args:
            # No arguments, stay in current directory (sandbox-safe behavior)
            return f"Current directory: {self.cwd}"
        else:
            path_arg = args[0]
            if path_arg.startswith('/'):
                # Absolute path
                new_path = Path(path_arg)
            else:
                # Relative path
                new_path = self.cwd / path_arg

        try:
            new_path = new_path.resolve()

            # Safety check
            is_safe, reason = self.path_guard.validate_file_operation(str(new_path), 'read')
            if not is_safe:
                return colorize_text(f"Error: {reason}", "red")

            if not new_path.exists():
                return colorize_text(f"Directory not found: {new_path}", "red")

            if not new_path.is_dir():
                return colorize_text(f"Not a directory: {new_path}", "red")

            self.cwd = new_path
            # Keep original sandbox root, don't reset it
            return ""

        except Exception as e:
            return colorize_text(f"Error changing directory: {str(e)}", "red")

    def open_path(self, args: List[str]) -> str:
        """Open a file, directory, or URL using the default macOS handler."""
        if not IS_MAC:
            return colorize_text("The 'open' command is available on macOS only.", "yellow")

        target = args[0] if args else '.'

        if target.startswith(('http://', 'https://')):
            command = ['open', target]
            description = target
        else:
            candidate = Path(target).expanduser()
            if not candidate.is_absolute():
                candidate = (self.cwd / candidate).resolve()

            if not candidate.exists():
                return colorize_text(f"Path not found: {candidate}", "red")

            command = ['open', str(candidate)]
            description = str(candidate)

        try:
            subprocess.Popen(command)
            return colorize_text(f"Opening {description}...", "green")
        except Exception as exc:
            return colorize_text(f"Failed to open: {exc}", "red")

    def pbcopy(self, args: List[str]) -> str:
        """Copy text to the macOS clipboard."""
        if not IS_MAC:
            return colorize_text("The 'pbcopy' command is available on macOS only.", "yellow")

        if not args:
            return colorize_text("Usage: pbcopy <text>", "yellow")

        text = " ".join(args)

        try:
            subprocess.run(['pbcopy'], input=text, text=True, check=True)
            return colorize_text("Copied text to clipboard.", "green")
        except Exception as exc:
            return colorize_text(f"Clipboard copy failed: {exc}", "red")

    def pbpaste(self, args: List[str]) -> str:
        """Paste text from the macOS clipboard."""
        if not IS_MAC:
            return colorize_text("The 'pbpaste' command is available on macOS only.", "yellow")

        try:
            result = subprocess.run(['pbpaste'], capture_output=True, text=True, check=True)
            return result.stdout.rstrip()
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() if exc.stderr else "Clipboard is empty or unavailable."
            return colorize_text(message, "yellow")
        except Exception as exc:
            return colorize_text(f"Clipboard read failed: {exc}", "red")

    def spotlight(self, args: List[str]) -> str:
        """Search files using macOS Spotlight (mdfind)."""
        if not IS_MAC:
            return colorize_text("The 'spotlight' command is available on macOS only.", "yellow")

        if not args:
            return colorize_text("Usage: spotlight <search terms>", "yellow")

        query = " ".join(args)

        try:
            result = subprocess.run(
                ['mdfind', query],
                capture_output=True,
                text=True,
                check=True,
                timeout=15
            )

            output = result.stdout.strip()
            if not output:
                return "No results found."

            return truncate_output(output, max_lines=50, max_chars=4000)

        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() if exc.stderr else "Spotlight search failed."
            return colorize_text(message, "red")
        except Exception as exc:
            return colorize_text(f"Spotlight error: {exc}", "red")

    def say_text(self, args: List[str]) -> str:
        """Speak text aloud using macOS text-to-speech."""
        if not IS_MAC:
            return colorize_text("The 'say' command is available on macOS only.", "yellow")

        if not args:
            return colorize_text("Usage: say <text>", "yellow")

        text = " ".join(args)

        try:
            subprocess.Popen(['say', text])
            return colorize_text("Speaking...", "green")
        except Exception as exc:
            return colorize_text(f"Say command failed: {exc}", "red")

    def ls(self, args: List[str]) -> str:
        """List directory contents."""
        positional, flags = parse_flags(args)

        # Determine target directory
        target_dir = self.cwd
        if positional:
            target_path = positional[0]
            if target_path.startswith('/'):
                target_dir = Path(target_path)
            else:
                target_dir = self.cwd / target_path

        try:
            target_dir = target_dir.resolve()

            # Safety check
            is_safe, reason = self.path_guard.validate_file_operation(str(target_dir), 'read')
            if not is_safe:
                return colorize_text(f"Error: {reason}", "red")

            if not target_dir.exists():
                return colorize_text(f"Directory not found: {target_dir}", "red")

            if not target_dir.is_dir():
                return colorize_text(f"Not a directory: {target_dir}", "red")

            # Get directory contents
            items = []
            try:
                for item in target_dir.iterdir():
                    # Skip hidden files unless -a flag
                    if item.name.startswith('.') and 'a' not in flags:
                        continue
                    items.append(item)
            except PermissionError:
                return colorize_text(f"Permission denied: {target_dir}", "red")

            # Sort items
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

            if not items:
                return "Directory is empty"

            # Format output
            if 'l' in flags:
                # Long format
                lines = []
                for item in items:
                    try:
                        stat_info = item.stat()

                        # File type and permissions
                        mode = stat_info.st_mode
                        perms = format_perms(mode)

                        # Size
                        size = human_size(stat_info.st_size)

                        # Modified time
                        mtime = format_mtime(stat_info.st_mtime)

                        # Name with color coding
                        name = item.name
                        if item.is_dir():
                            name = colorize_text(name, "blue")
                        elif item.is_symlink():
                            name = colorize_text(name, "cyan")
                        elif stat_info.st_mode & stat.S_IXUSR:
                            name = colorize_text(name, "green")
                        elif item.suffix in ['.txt', '.md', '.log']:
                            name = colorize_text(name, "white")
                        elif item.suffix in ['.py', '.js', '.html', '.css']:
                            name = colorize_text(name, "yellow")

                        lines.append(f"{perms} {size:>8} {mtime} {name}")

                    except (OSError, PermissionError):
                        lines.append(f"????????? -------- ---------- {item.name}")

                return "\n".join(lines)
            else:
                # Simple format
                names = []
                for item in items:
                    name = item.name
                    if item.is_dir():
                        name = colorize_text(name, "blue")
                    elif item.is_symlink():
                        name = colorize_text(name, "cyan")
                    elif item.is_file():
                        try:
                            if item.stat().st_mode & stat.S_IXUSR:
                                name = colorize_text(name, "green")
                            elif item.suffix in ['.txt', '.md', '.log']:
                                name = colorize_text(name, "white")
                            elif item.suffix in ['.py', '.js', '.html', '.css']:
                                name = colorize_text(name, "yellow")
                        except OSError:
                            pass
                    names.append(name)

                # Display in columns
                if len(names) <= 10:
                    return "  ".join(names)
                else:
                    # Multi-column display
                    cols = 4
                    rows = (len(names) + cols - 1) // cols
                    result = []
                    for row in range(rows):
                        row_items = []
                        for col in range(cols):
                            idx = row + col * rows
                            if idx < len(names):
                                row_items.append(names[idx].ljust(20))
                        result.append("  ".join(row_items).rstrip())
                    return "\n".join(result)

        except Exception as e:
            return colorize_text(f"Error listing directory: {str(e)}", "red")

    def mkdir(self, args: List[str]) -> str:
        """Create directory."""
        positional, flags = parse_flags(args)

        if not positional:
            return colorize_text("Error: mkdir requires a directory name", "red")

        dir_name = positional[0]

        if dir_name.startswith('/'):
            target_path = Path(dir_name)
        else:
            target_path = self.cwd / dir_name

        try:
            target_path = target_path.resolve()

            # Safety check
            is_safe, reason = self.path_guard.validate_file_operation(str(target_path), 'write')
            if not is_safe:
                return colorize_text(f"Error: {reason}", "red")

            # Create directory
            if 'p' in flags:
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                target_path.mkdir()

            return f"Directory created: {target_path.name}"

        except FileExistsError:
            return colorize_text(f"Directory already exists: {dir_name}", "red")
        except PermissionError:
            return colorize_text(f"Permission denied: {dir_name}", "red")
        except Exception as e:
            return colorize_text(f"Error creating directory: {str(e)}", "red")

    def rmdir(self, args: List[str]) -> str:
        """Remove empty directory."""
        if not args:
            return colorize_text("Error: rmdir requires a directory name", "red")

        dir_name = args[0]

        if dir_name.startswith('/'):
            target_path = Path(dir_name)
        else:
            target_path = self.cwd / dir_name

        try:
            target_path = target_path.resolve()

            # Safety check
            is_safe, reason = self.path_guard.validate_file_operation(str(target_path), 'delete')
            if not is_safe:
                return colorize_text(f"Error: {reason}", "red")

            if not target_path.exists():
                return colorize_text(f"Directory not found: {dir_name}", "red")

            if not target_path.is_dir():
                return colorize_text(f"Not a directory: {dir_name}", "red")

            target_path.rmdir()
            return f"Directory removed: {dir_name}"

        except OSError as e:
            if e.errno == 39:  # Directory not empty
                return colorize_text(f"Directory not empty: {dir_name}", "red")
            return colorize_text(f"Error removing directory: {str(e)}", "red")
        except Exception as e:
            return colorize_text(f"Error removing directory: {str(e)}", "red")

    def rm(self, args: List[str]) -> str:
        """Remove files or directories."""
        positional, flags = parse_flags(args)

        if not positional:
            return colorize_text("Error: rm requires a file or directory name", "red")

        target_name = positional[0]
        force = 'f' in flags
        recursive = 'r' in flags
        i_understand = 'i-understand' in flags

        if target_name.startswith('/'):
            target_path = Path(target_name)
        else:
            target_path = self.cwd / target_name

        try:
            target_path = target_path.resolve()

            # Safety check
            is_safe, reason = self.path_guard.validate_file_operation(str(target_path), 'delete')
            if not is_safe:
                return colorize_text(f"Error: {reason}", "red")

            if not target_path.exists():
                if force:
                    return ""  # Silent success with -f
                return colorize_text(f"File not found: {target_name}", "red")

            # Special protection for sandbox root
            if target_path == self.path_guard.sandbox_root and target_name in ['.', './']:
                if not i_understand:
                    return colorize_text("Error: Blocked attempt to remove sandbox root. Use --i-understand flag if you really mean this.", "red")

            # Confirmation for dangerous operations
            if not force:
                if target_path.is_dir():
                    if not recursive:
                        return colorize_text("Error: Cannot remove directory without -r flag", "red")

                    # Enhanced confirmation for directory removal
                    action_desc = f"Remove directory '{target_name}' and all its contents"
                    if target_path == self.path_guard.sandbox_root:
                        action_desc += " (THIS IS THE SANDBOX ROOT - VERY DANGEROUS)"

                    if not self.safety_guard.confirm_dangerous_action(action_desc):
                        return "Operation cancelled"
                else:
                    if not self.safety_guard.confirm_dangerous_action(
                        f"Remove file '{target_name}'"
                    ):
                        return "Operation cancelled"

            # Perform removal
            if target_path.is_dir():
                if recursive:
                    shutil.rmtree(target_path)
                    return f"Directory removed: {target_name}"
                else:
                    return colorize_text("Error: Cannot remove directory without -r flag", "red")
            else:
                target_path.unlink()
                return f"File removed: {target_name}"

        except PermissionError:
            return colorize_text(f"Permission denied: {target_name}", "red")
        except Exception as e:
            return colorize_text(f"Error removing: {str(e)}", "red")

    def touch(self, args: List[str]) -> str:
        """Create empty file or update timestamp."""
        if not args:
            return colorize_text("Error: touch requires a filename", "red")

        filename = args[0]

        if filename.startswith('/'):
            target_path = Path(filename)
        else:
            target_path = self.cwd / filename

        try:
            target_path = target_path.resolve()

            # Safety check
            is_safe, reason = self.path_guard.validate_file_operation(str(target_path), 'write')
            if not is_safe:
                return colorize_text(f"Error: {reason}", "red")

            target_path.touch()
            return f"File created/updated: {target_path.name}"

        except PermissionError:
            return colorize_text(f"Permission denied: {filename}", "red")
        except Exception as e:
            return colorize_text(f"Error creating file: {str(e)}", "red")

    def cat(self, args: List[str]) -> str:
        """Display file contents."""
        if not args:
            return colorize_text("Error: cat requires a filename", "red")

        filename = args[0]

        if filename.startswith('/'):
            target_path = Path(filename)
        else:
            target_path = self.cwd / filename

        try:
            target_path = target_path.resolve()

            # Safety check
            is_safe, reason = self.path_guard.validate_file_operation(str(target_path), 'read')
            if not is_safe:
                return colorize_text(f"Error: {reason}", "red")

            if not target_path.exists():
                return colorize_text(f"File not found: {filename}", "red")

            if not target_path.is_file():
                return colorize_text(f"Not a file: {filename}", "red")

            # Check file size
            file_size = target_path.stat().st_size
            max_size = 200 * 1024  # 200KB limit

            if file_size > max_size:
                return colorize_text(
                    f"File too large ({format_size(file_size)}). "
                    f"Maximum size for display is {format_size(max_size)}",
                    "red"
                )

            # Read and display file
            try:
                content = target_path.read_text(encoding='utf-8')
                # Truncate very long output
                return truncate_output(content, max_lines=200)
            except UnicodeDecodeError:
                return colorize_text(f"Error: File contains binary data: {filename}", "red")

        except PermissionError:
            return colorize_text(f"Permission denied: {filename}", "red")
        except Exception as e:
            return colorize_text(f"Error reading file: {str(e)}", "red")

    def echo(self, args: List[str]) -> str:
        """Print text to stdout or file."""
        if not args:
            return ""

        # Handle redirection
        output_file = None
        append_mode = False
        text_args = []

        i = 0
        while i < len(args):
            if args[i] == '>':
                if i + 1 < len(args):
                    output_file = args[i + 1]
                    append_mode = False
                    break
                else:
                    return colorize_text("Error: No filename after '>'", "red")
            elif args[i] == '>>':
                if i + 1 < len(args):
                    output_file = args[i + 1]
                    append_mode = True
                    break
                else:
                    return colorize_text("Error: No filename after '>>'", "red")
            else:
                text_args.append(args[i])
            i += 1

        text = ' '.join(text_args)

        if output_file:
            # Write to file
            if output_file.startswith('/'):
                target_path = Path(output_file)
            else:
                target_path = self.cwd / output_file

            try:
                target_path = target_path.resolve()

                # Safety check
                is_safe, reason = self.path_guard.validate_file_operation(str(target_path), 'write')
                if not is_safe:
                    return colorize_text(f"Error: {reason}", "red")

                mode = 'a' if append_mode else 'w'
                target_path.write_text(text + '\n', encoding='utf-8', mode=mode)

                action = "appended to" if append_mode else "written to"
                return f"Text {action}: {output_file}"

            except PermissionError:
                return colorize_text(f"Permission denied: {output_file}", "red")
            except Exception as e:
                return colorize_text(f"Error writing file: {str(e)}", "red")
        else:
            # Print to stdout
            return text

    def clear(self, args: List[str]) -> str:
        """Clear the screen."""
        # ANSI escape sequence to clear screen
        print('\033[2J\033[H', end='')
        return ""

    def help(self, args: List[str]) -> str:
        """Show help for commands."""
        help_lines = [
            colorize_text("Available Commands:", "blue"),
            "",
            colorize_text("Built-in Commands:", "green"),
            f"  {colorize_text('pwd', 'cyan')}                    - Print current working directory",
            f"  {colorize_text('ls', 'cyan')} [-a] [-l] [path]   - List directory contents (-a: show hidden, -l: long format)",
            f"  {colorize_text('cd', 'cyan')} <path>             - Change directory",
            f"  {colorize_text('mkdir', 'cyan')} [-p] <dir>      - Create directory (-p: create parents)",
            f"  {colorize_text('rmdir', 'cyan')} <dir>           - Remove empty directory",
            f"  {colorize_text('rm', 'cyan')} [-f] [-r] <target> - Remove files/directories (-f: force, -r: recursive)",
            f"  {colorize_text('touch', 'cyan')} <file>          - Create empty file or update timestamp",
            f"  {colorize_text('cat', 'cyan')} <file>            - Display file contents",
            f"  {colorize_text('echo', 'cyan')} <text> [> file]  - Print text (optionally to file)",
            f"  {colorize_text('clear', 'cyan')}                 - Clear screen",
            f"  {colorize_text('help', 'cyan')}                  - Show this help",
            f"  {colorize_text('sysinfo', 'cyan')}               - Show system information",
            f"  {colorize_text('exit/quit', 'cyan')}             - Exit terminal",
            "",
            colorize_text("External Commands:", "green"),
            "  Any other command will be executed as an external program with safety checks.",
            "",
            colorize_text("Safety Features:", "yellow"),
            "  - All file operations include sandbox protection",
            "  - Large files are truncated for display",
            "  - Dangerous operations require confirmation",
            "  - Commands are executed with timeouts",
            "",
            colorize_text("Examples:", "magenta"),
            "  " + colorize_text('ls -la', 'white') + "                - List all files in long format",
            "  " + colorize_text('mkdir -p dir1/dir2', 'white') + "    - Create nested directories",
            "  " + colorize_text("echo 'Hello' > file.txt", 'white') + " - Write text to file",
            "  " + colorize_text('cat file.txt', 'white') + "          - Display file contents",
            "",
            colorize_text("Navigation:", "blue"),
            "  ↑/↓ arrows    - Navigate command history",
            "  Tab           - Auto-complete commands and files",
            "  Ctrl+L        - Clear screen",
            "  Ctrl+C        - Interrupt current command",
        ]

        if IS_MAC:
            help_lines.extend([
                "",
                colorize_text("macOS Extras:", "green"),
                f"  {colorize_text('open', 'cyan')} [path|url]       - Open files, folders, or URLs",
                f"  {colorize_text('pbcopy', 'cyan')} <text>         - Copy text to clipboard",
                f"  {colorize_text('pbpaste', 'cyan')}               - Paste clipboard contents",
                f"  {colorize_text('spotlight', 'cyan')} <query>     - Search with Spotlight",
                f"  {colorize_text('say', 'cyan')} <text>           - Speak text aloud",
            ])

        return '\n'.join(help_lines)

    def get_builtin_commands(self) -> Dict[str, callable]:
        """Get dictionary of built-in commands."""
        commands = {
            'pwd': self.pwd,
            'ls': self.ls,
            'cd': self.cd,
            'mkdir': self.mkdir,
            'rmdir': self.rmdir,
            'rm': self.rm,
            'touch': self.touch,
            'cat': self.cat,
            'echo': self.echo,
            'clear': self.clear,
            'help': self.help,
        }

        if IS_MAC:
            commands.update({
                'open': self.open_path,
                'pbcopy': self.pbcopy,
                'pbpaste': self.pbpaste,
                'spotlight': self.spotlight,
                'say': self.say_text,
            })

        return commands
