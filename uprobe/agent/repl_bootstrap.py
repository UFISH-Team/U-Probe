"""
Bootstrap Pantheon REPL in a workspace with the U-Probe team template.

This module intentionally bypasses the existing U-Probe CLI and the
`uprobe.agent.api.UProbeAgentAPI` workflow. Instead, it:
1) Copies `uprobe_team.md` into `<workspace>/.pantheon/teams/`
2) Copies `DEFAULT_PROTOCOL.yaml` into `<workspace>/DEFAULT_PROTOCOL.yaml`
3) Launches `python -m pantheon.repl --template <copied_md>`
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m uprobe.agent.repl_bootstrap",
        description=(
            "Copy uprobe_team.md into <workspace>/.pantheon/teams/ and launch "
            "Pantheon REPL with --template so uprobe_team is loaded by default."
        ),
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=str(Path.cwd()),
        help="Workspace directory to install templates into (default: CWD).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing <workspace>/.pantheon/teams/uprobe_team.md.",
    )

    # Pass-through options for pantheon.repl (keep it minimal but useful).
    parser.add_argument(
        "--memory-dir",
        type=str,
        default=None,
        help="Pantheon memory dir (passed to pantheon.repl).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        help="Log level for REPL (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable console logging in REPL (passed to pantheon.repl).",
    )
    parser.add_argument(
        "--resync",
        action="store_true",
        help=(
            "Force pantheon.repl to resync templates "
            "(cleans skills/agents/teams/prompts dirs)."
        ),
    )
    parser.add_argument(
        "--chat-id",
        type=str,
        default=None,
        help="Resume a specific chat ID (passed to pantheon.repl).",
    )
    parser.add_argument(
        "repl_args",
        nargs=argparse.REMAINDER,
        help=(
            "Additional arguments passed to pantheon.repl after '--'. "
            "Example: -- --log-level DEBUG"
        ),
    )
    return parser


def _normalize_repl_args(remainder: list[str]) -> list[str]:
    """Normalize argparse REMAINDER (strip leading '--' if present)."""
    if remainder and remainder[0] == "--":
        return remainder[1:]
    return remainder


def _install_team_template(workspace: Path, force: bool) -> Path:
    """Copy uprobe_team.md into <workspace>/.pantheon/teams/ and return dest."""
    src = Path(__file__).resolve().parent / "templates" / "uprobe_team.md"
    if not src.exists():
        raise FileNotFoundError(f"Team template not found: {src}")

    dest_dir = workspace / ".pantheon" / "teams"
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / "uprobe_team.md"
    if dest.exists() and not force:
        return dest

    shutil.copy2(src, dest)
    return dest


def _install_protocol_template(workspace: Path, force: bool) -> Path:
    """Copy DEFAULT_PROTOCOL.yaml into <workspace>/ and return dest."""
    src = Path(__file__).resolve().parent / "templates" / "DEFAULT_PROTOCOL.yaml"
    if not src.exists():
        raise FileNotFoundError(f"Protocol template not found: {src}")

    dest = workspace / "DEFAULT_PROTOCOL.yaml"
    if dest.exists() and not force:
        return dest

    shutil.copy2(src, dest)
    return dest


def _launch_repl(
    workspace: Path,
    template_path: Path,
    memory_dir: str | None,
    log_level: str | None,
    quiet: bool,
    resync: bool,
    chat_id: str | None,
    extra_args: list[str],
) -> int:
    """Launch pantheon.repl with --template and return exit code."""
    # Ensure `pantheon` can be imported even when running in an arbitrary
    # workspace directory during development (repo not installed site-wide).
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{repo_root}{os.pathsep}{pythonpath}" if pythonpath else str(repo_root)
    )

    cmd: list[str] = [
        sys.executable,
        "-m",
        "pantheon.repl",
        "--template",
        str(template_path),
        "--workspace",
        str(workspace),
    ]
    if memory_dir:
        cmd += ["--memory-dir", memory_dir]
    if chat_id:
        cmd += ["--chat-id", chat_id]
    if log_level:
        cmd += ["--log-level", log_level]
    if quiet:
        cmd += ["--quiet"]
    if resync:
        cmd += ["--resync"]
    if extra_args:
        cmd += extra_args

    completed = subprocess.run(cmd, cwd=str(workspace), env=env)
    return int(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve()
    template_path = _install_team_template(workspace=workspace, force=bool(args.force))
    _install_protocol_template(workspace=workspace, force=bool(args.force))

    extra_args = _normalize_repl_args(list(args.repl_args or []))
    return _launch_repl(
        workspace=workspace,
        template_path=template_path,
        memory_dir=args.memory_dir,
        log_level=args.log_level,
        quiet=bool(args.quiet),
        resync=bool(args.resync),
        chat_id=args.chat_id,
        extra_args=extra_args,
    )


if __name__ == "__main__":
    raise SystemExit(main())

