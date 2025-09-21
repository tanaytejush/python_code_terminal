"""System monitoring functionality for CPU, memory, and process information."""

import time
from typing import List, Dict, Any, Tuple
from datetime import datetime
from utils import format_size, colorize_text

try:  # pragma: no cover - fallback when psutil is unavailable
    import psutil  # type: ignore
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


class SystemMonitor:
    """Provides system monitoring and process information."""

    def __init__(self):
        self.last_cpu_times = None
        self.last_cpu_check = None

    def get_cpu_percent(self, interval: float = 1.0) -> float:
        """Get current CPU usage percentage.

        Args:
            interval: Time interval for measurement in seconds

        Returns:
            CPU usage percentage
        """
        if not PSUTIL_AVAILABLE:
            return 0.0

        try:
            # Use non-blocking call if we have recent data
            if (self.last_cpu_check and
                time.time() - self.last_cpu_check < 2.0):
                return psutil.cpu_percent(interval=None)
            else:
                # First call or stale data, use blocking call
                cpu_percent = psutil.cpu_percent(interval=interval)
                self.last_cpu_check = time.time()
                return cpu_percent
        except Exception:
            return 0.0

    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage information.

        Returns:
            Dictionary with memory statistics
        """
        if not PSUTIL_AVAILABLE:
            return {
                'total': 0,
                'available': 0,
                'used': 0,
                'percent': 0.0,
                'free': 0,
                'swap_total': 0,
                'swap_used': 0,
                'swap_percent': 0.0,
                'swap_free': 0
            }

        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'free': memory.free,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent,
                'swap_free': swap.free
            }
        except Exception:
            return {
                'total': 0,
                'available': 0,
                'used': 0,
                'percent': 0.0,
                'free': 0,
                'swap_total': 0,
                'swap_used': 0,
                'swap_percent': 0.0,
                'swap_free': 0
            }

    def get_disk_info(self, path: str = '/') -> Dict[str, Any]:
        """Get disk usage information for a path.

        Args:
            path: Path to check disk usage for

        Returns:
            Dictionary with disk statistics
        """
        if not PSUTIL_AVAILABLE:
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0.0
            }

        try:
            usage = psutil.disk_usage(path)
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': (usage.used / usage.total) * 100 if usage.total > 0 else 0.0
            }
        except Exception:
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0.0
            }

    def get_top_processes(self, limit: int = 5, sort_by: str = 'cpu') -> List[Dict[str, Any]]:
        """Get top processes by CPU or memory usage.

        Args:
            limit: Number of processes to return
            sort_by: Sort criteria ('cpu' or 'memory')

        Returns:
            List of process dictionaries
        """
        if not PSUTIL_AVAILABLE:
            return []

        try:
            processes = []

            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    proc_info = proc.info

                    # Get CPU percent (might be None on first call)
                    cpu_percent = proc_info.get('cpu_percent', 0.0)
                    if cpu_percent is None:
                        cpu_percent = 0.0

                    # Get memory info
                    memory_percent = proc_info.get('memory_percent', 0.0)
                    memory_info = proc_info.get('memory_info')
                    memory_mb = 0.0
                    if memory_info:
                        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB

                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'][:20],  # Truncate long names
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_percent,
                        'memory_mb': memory_mb
                    })

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process disappeared or access denied
                    continue

            # Sort processes
            if sort_by == 'memory':
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            else:  # Default to CPU
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            return processes[:limit]

        except Exception:
            return []

    def get_network_info(self) -> Dict[str, Any]:
        """Get network interface information.

        Returns:
            Dictionary with network statistics
        """
        if not PSUTIL_AVAILABLE:
            return {}

        try:
            stats = psutil.net_io_counters()
            if stats:
                return {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errors_in': stats.errin,
                    'errors_out': stats.errout,
                    'drop_in': stats.dropin,
                    'drop_out': stats.dropout
                }
            else:
                return {}
        except Exception:
            return {}

    def get_boot_time(self) -> str:
        """Get system boot time.

        Returns:
            Formatted boot time string
        """
        if not PSUTIL_AVAILABLE:
            return "Unknown"

        try:
            boot_timestamp = psutil.boot_time()
            boot_time = datetime.fromtimestamp(boot_timestamp)
            return boot_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "Unknown"

    def get_sysinfo(self, top_n: int = 5) -> Dict[str, Any]:
        """Get system information in structured format.

        Args:
            top_n: Number of top processes to include

        Returns:
            Dictionary with system information
        """
        try:
            cpu_percent = self.get_cpu_percent(interval=0.1)
            memory_info = self.get_memory_info()
            top_processes = self.get_top_processes(limit=top_n, sort_by='cpu')

            top = []
            for proc in top_processes:
                top.append({
                    'pid': proc['pid'],
                    'name': proc['name'],
                    'cpu_percent': proc['cpu_percent']
                })

            return {
                'cpu_percent': cpu_percent,
                'mem_percent': memory_info.get('percent', 0.0),
                'memory': memory_info,
                'top': top,
                'psutil_available': PSUTIL_AVAILABLE
            }

        except Exception as exc:
            return {
                'cpu_percent': 0.0,
                'mem_percent': 0.0,
                'memory': {},
                'top': [],
                'psutil_available': PSUTIL_AVAILABLE,
                'error': str(exc)
            }

    def get_system_info(self) -> str:
        """Get comprehensive system information.

        Returns:
            Formatted system information string
        """
        if not PSUTIL_AVAILABLE:
            return colorize_text(
                "System monitoring unavailable: psutil is not installed.",
                "yellow"
            )

        try:
            # Get CPU info
            cpu_percent = self.get_cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()

            # Get memory info
            memory_info = self.get_memory_info()

            # Get disk info
            disk_info = self.get_disk_info()

            # Get top processes
            top_processes = self.get_top_processes(limit=5, sort_by='cpu')

            # Get network info
            network_info = self.get_network_info()

            # Get boot time
            boot_time = self.get_boot_time()

            # Format output
            output_lines = []

            # System overview
            output_lines.append(colorize_text("=== SYSTEM INFORMATION ===", "blue"))
            output_lines.append(f"Boot Time: {boot_time}")
            output_lines.append("")

            # CPU information
            output_lines.append(colorize_text("CPU Information:", "green"))
            output_lines.append(f"  Usage: {cpu_percent:.1f}%")
            output_lines.append(f"  Cores: {cpu_count}")

            if cpu_freq:
                freq_ghz = cpu_freq.current / 1000  # Convert MHz to GHz
                output_lines.append(f"  Frequency: {freq_ghz:.2f} GHz")

            output_lines.append("")

            # Memory information
            output_lines.append(colorize_text("Memory Information:", "green"))
            output_lines.append(f"  Total: {format_size(memory_info['total'])}")
            output_lines.append(f"  Used: {format_size(memory_info['used'])} ({memory_info['percent']:.1f}%)")
            output_lines.append(f"  Available: {format_size(memory_info['available'])}")

            if memory_info['swap_total'] > 0:
                output_lines.append(f"  Swap: {format_size(memory_info['swap_used'])}/{format_size(memory_info['swap_total'])} ({memory_info['swap_percent']:.1f}%)")

            output_lines.append("")

            # Disk information
            output_lines.append(colorize_text("Disk Information:", "green"))
            output_lines.append(f"  Total: {format_size(disk_info['total'])}")
            output_lines.append(f"  Used: {format_size(disk_info['used'])} ({disk_info['percent']:.1f}%)")
            output_lines.append(f"  Free: {format_size(disk_info['free'])}")
            output_lines.append("")

            # Network information
            if network_info:
                output_lines.append(colorize_text("Network Information:", "green"))
                output_lines.append(f"  Bytes Sent: {format_size(network_info['bytes_sent'])}")
                output_lines.append(f"  Bytes Received: {format_size(network_info['bytes_recv'])}")
                output_lines.append(f"  Packets Sent: {network_info['packets_sent']:,}")
                output_lines.append(f"  Packets Received: {network_info['packets_recv']:,}")
                output_lines.append("")

            # Top processes
            output_lines.append(colorize_text("Top Processes by CPU:", "green"))
            output_lines.append("  PID    NAME                  CPU%   MEM%   RAM(MB)")
            output_lines.append("  " + "-" * 55)

            for proc in top_processes:
                output_lines.append(
                    f"  {proc['pid']:<6} {proc['name']:<20} {proc['cpu_percent']:<6.1f} "
                    f"{proc['memory_percent']:<6.1f} {proc['memory_mb']:<7.1f}"
                )

            return "\n".join(output_lines)

        except Exception as e:
            return colorize_text(f"Error getting system information: {str(e)}", "red")

    def monitor_process(self, pid: int) -> Dict[str, Any]:
        """Monitor a specific process.

        Args:
            pid: Process ID to monitor

        Returns:
            Dictionary with process information
        """
        try:
            proc = psutil.Process(pid)

            return {
                'pid': proc.pid,
                'name': proc.name(),
                'status': proc.status(),
                'cpu_percent': proc.cpu_percent(),
                'memory_percent': proc.memory_percent(),
                'memory_info': proc.memory_info()._asdict(),
                'create_time': datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S"),
                'num_threads': proc.num_threads(),
                'cmdline': ' '.join(proc.cmdline()[:5]),  # First 5 args only
            }

        except psutil.NoSuchProcess:
            return {'error': f'Process {pid} not found'}
        except psutil.AccessDenied:
            return {'error': f'Access denied for process {pid}'}
        except Exception as e:
            return {'error': f'Error monitoring process {pid}: {str(e)}'}

    def kill_process(self, pid: int, force: bool = False) -> str:
        """Kill a process.

        Args:
            pid: Process ID to kill
            force: Use SIGKILL instead of SIGTERM

        Returns:
            Result message
        """
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()

            if force:
                proc.kill()  # SIGKILL
                return f"Process {pid} ({proc_name}) killed forcefully"
            else:
                proc.terminate()  # SIGTERM
                return f"Process {pid} ({proc_name}) terminated"

        except psutil.NoSuchProcess:
            return colorize_text(f"Process {pid} not found", "red")
        except psutil.AccessDenied:
            return colorize_text(f"Access denied for process {pid}", "red")
        except Exception as e:
            return colorize_text(f"Error killing process {pid}: {str(e)}", "red")
