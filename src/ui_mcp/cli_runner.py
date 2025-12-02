"""CLI runner for MCP tools.

Executes UI CLI commands via subprocess and returns parsed JSON output.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Project root is parent of src/
PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_cli(
    args: list[str],
    timeout: int = 30,
    skip_confirmation: bool = True,
) -> dict:
    """Run UI CLI command and return parsed output.

    Args:
        args: Command arguments (e.g., ["lo", "health", "-o", "json"])
        timeout: Command timeout in seconds
        skip_confirmation: Add -y flag to skip confirmations for actions

    Returns:
        Parsed JSON output or error dict with 'error' key
    """
    # Use the same Python that's running the MCP server
    # This ensures we're in the correct conda environment
    python_path = sys.executable
    cmd = [python_path, "-m", "ui_cli.main"] + args

    # Add JSON output flag if not present
    if "-o" not in args and "--output" not in args:
        cmd.extend(["-o", "json"])

    # Add -y for action commands to skip confirmation
    if skip_confirmation and any(
        action in args for action in ["block", "unblock", "kick", "restart", "create"]
    ):
        if "-y" not in args and "--yes" not in args:
            cmd.append("-y")

    # Set up environment with PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

        # Try to parse stdout as JSON
        stdout = result.stdout.strip()
        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                # Not JSON, return as raw output
                if result.returncode == 0:
                    return {"output": stdout}
                else:
                    return {
                        "error": True,
                        "message": result.stderr.strip() or stdout,
                        "exit_code": result.returncode,
                    }

        # No stdout, check for errors
        if result.returncode != 0:
            return {
                "error": True,
                "message": result.stderr.strip() or "Command failed with no output",
                "exit_code": result.returncode,
            }

        return {"output": ""}

    except subprocess.TimeoutExpired:
        return {"error": True, "message": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"error": True, "message": "CLI not found. Run from project root."}
    except Exception as e:
        return {"error": True, "message": str(e)}


def format_result(data: dict, summary: str | None = None) -> str:
    """Format result dict as JSON string for MCP response.

    Args:
        data: Result data from CLI
        summary: Optional human-readable summary to prepend

    Returns:
        JSON string suitable for MCP tool response
    """
    if summary and "error" not in data:
        data = {"summary": summary, **data}
    return json.dumps(data, indent=2)
