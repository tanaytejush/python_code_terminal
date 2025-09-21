"""Streamlit frontend for Python Terminal."""

import streamlit as st
import requests
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Python Terminal",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for terminal-like appearance
st.markdown("""
<style>
    .terminal-container {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Courier New', monospace;
        padding: 14px;
        border-radius: 6px;
        white-space: pre-wrap;
        font-size: 14px;
        height: 460px;
        overflow-y: auto;
        border: 1px solid #1f2328;
    }

    .terminal-input {
        background-color: #21262d;
        color: #c9d1d9;
        font-family: 'Courier New', monospace;
        border: 1px solid #30363d;
        padding: 8px;
        border-radius: 4px;
    }

    .prompt {
        color: #58a6ff;
        font-weight: bold;
    }

    .stButton > button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }

    .stButton > button:hover {
        background-color: #30363d;
        border-color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)


class TerminalApp:
    """Streamlit Terminal Application."""

    def __init__(self):
        self.base_url = BASE_URL
        self.init_session_state()

    def init_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'command_history' not in st.session_state:
            st.session_state.command_history = []

        if 'output_history' not in st.session_state:
            st.session_state.output_history = []

        if 'current_directory' not in st.session_state:
            st.session_state.current_directory = "/"

        if 'connected' not in st.session_state:
            st.session_state.connected = False

    def check_connection(self) -> bool:
        """Check if the backend API is available."""
        try:
            response = requests.get(f"{self.base_url}/sysinfo", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command via the API."""
        try:
            response = requests.post(
                f"{self.base_url}/exec",
                json={"cmd": command},
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "stdout": "",
                    "stderr": f"API Error: {response.status_code}",
                    "rc": 1,
                    "cwd": st.session_state.current_directory
                }

        except requests.exceptions.Timeout:
            return {
                "stdout": "",
                "stderr": "Command timed out",
                "rc": 1,
                "cwd": st.session_state.current_directory
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Connection error: {str(e)}",
                "rc": 1,
                "cwd": st.session_state.current_directory
            }

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information from the API."""
        try:
            response = requests.get(f"{self.base_url}/sysinfo", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def format_output(self, result: Dict[str, Any], command: str) -> str:
        """Format command output for display."""
        prompt = f"pyterm:{self.get_short_path(st.session_state.current_directory)}$ "

        # Start with command
        output = f"{prompt}{command}"

        # Add stdout if present
        if result.get("stdout"):
            output += f"\n{result['stdout'].rstrip()}"

        # Add stderr if present
        if result.get("stderr"):
            output += f"\nERROR: {result['stderr']}"

        # Add return code if non-zero
        if result.get("rc", 0) != 0:
            output += f"\n[Return code: {result['rc']}]"

        return output

    def get_short_path(self, path: str) -> str:
        """Shorten path for display."""
        if len(path) > 40:
            return "..." + path[-37:]
        return path

    def render_system_monitor(self):
        """Render compact system monitoring badges."""
        sysinfo = self.get_system_info()

        if "error" in sysinfo:
            st.warning(f"System info unavailable: {sysinfo['error']}")
            return

        cpu_percent = sysinfo.get("cpu_percent", 0)
        mem_percent = sysinfo.get("mem_percent", 0)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("CPU", f"{cpu_percent:.1f}%")
        with col2:
            st.metric("Memory", f"{mem_percent:.1f}%")

    def render_terminal(self):
        """Render the main terminal interface."""
        st.title("🐍 Python Terminal")
        st.caption(f"Connected to {self.base_url}")

        st.markdown(
            f"**Current directory:** `{st.session_state.current_directory}`"
        )

        self.render_system_monitor()
        st.markdown("---")

        # Terminal output area
        output_container = st.container()

        with output_container:
            if st.session_state.output_history:
                recent_output = st.session_state.output_history[-15:]
                combined_output = "\n\n".join(recent_output)

                st.markdown(
                    f'<div class="terminal-container">{combined_output}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="terminal-container">Welcome to Python Terminal Web Interface<br>'
                    'Type your command below to get started.<br><br>'
                    f'<span class="prompt">pyterm:{self.get_short_path(st.session_state.current_directory)}$ </span></div>',
                    unsafe_allow_html=True
                )

        # Command input with form for Enter key support
        with st.form(key="command_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                command = st.text_input(
                    "Command:",
                    value="",
                    placeholder="Type a command…",
                    label_visibility="collapsed"
                )

            with col2:
                execute_button = st.form_submit_button("Execute", type="primary")

        # Execute command
        if (execute_button or command) and command.strip():
            with st.spinner("Executing command..."):
                result = self.execute_command(command.strip())

                # Update current directory
                if result.get("cwd"):
                    st.session_state.current_directory = result["cwd"]

                # Add to history
                formatted_output = self.format_output(result, command.strip())
                st.session_state.output_history.append(formatted_output)
                st.session_state.command_history.append(command.strip())

        # Command history expander
        if st.session_state.command_history:
            with st.expander("📜 Command History", expanded=False):
                for i, hist_cmd in enumerate(reversed(st.session_state.command_history[-10:]), 1):
                    st.code(hist_cmd, language="bash")

    def run(self):
        """Main application entry point."""
        # Check connection
        st.session_state.connected = self.check_connection()

        if not st.session_state.connected:
            st.title("🐍 Python Terminal")
            st.error(f"Cannot reach backend at {self.base_url}.")
            st.info("Start the backend with `./run_api.sh` and refresh this page.")
            return

        # Render main terminal
        self.render_terminal()

        # Footer
        st.markdown("---")
        st.markdown(
            "**Python Terminal v1.0** | "
            "Built with Streamlit | "
            f"Backend: {self.base_url}"
        )


def main():
    """Main function to run the Streamlit app."""
    app = TerminalApp()
    app.run()


if __name__ == "__main__":
    main()
