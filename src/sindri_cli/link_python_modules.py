## { SCRIPT
##
## === DEPENDENCIES ===
##

import sys
import argparse
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from pathlib import Path
from jormi.ww_io import shell_manager, log_manager


##
## === GLOBAL PARAMS ===
##

_SCRIPT_DIR = Path(__file__).resolve().parent
SINDRI_DIR = _SCRIPT_DIR.parent.parent

SUBMODULES: dict[str, Path] = {
    "arepo":  SINDRI_DIR / "submodules/ww_arepo_sims",
    "flash":  SINDRI_DIR / "submodules/ww_flash_sims",
    "quokka": SINDRI_DIR / "submodules/ww_quokka_sims",
    "bifrost": SINDRI_DIR / "submodules/bifrost",
    "jormi":  SINDRI_DIR / "submodules/jormi",
    "vegtamr": SINDRI_DIR / "submodules/vegtamr",
}


##
## === RESULTS STRUCT ===
##

@dataclass
class ResultsSummary:
    uninstalls: List[Tuple[str, bool]] = field(default_factory=list)  # (alias, success)
    installs:   List[Tuple[str, bool]] = field(default_factory=list)  # (alias, success)
    self_install: Optional[bool] = None                                # project editable install


##
## === LOGGING HELPERS ===
##

def log_info(text: str) -> None:
    log_manager.render_line(
        log_manager.Message(text, message_type=log_manager.MessageType.GENERAL),
        show_time=True,
    )

def log_action(text: str, *, outcome: log_manager.ActionOutcome) -> None:
    log_manager.render_line(
        log_manager.Message(
            text,
            message_type=log_manager.MessageType.ACTION,
            action_outcome=outcome,
        ),
        show_time=True,
    )


##
## === SHELL HELPERS ===
##

def _run(
    command: str,
    *,
    working_directory: Path | None = None,
    timeout_seconds: int = 900,
    show_output: bool = True,
) -> bool:
    try:
        shell_manager.execute_shell_command(
            command,
            timeout_seconds=timeout_seconds,
            show_output=show_output,
            working_directory=str(working_directory) if working_directory else None,
        )
        return True
    except Exception as exc:
        log_action(
            f"Command failed: {command}\n{exc}",
            outcome=log_manager.ActionOutcome.FAILURE,
        )
        return False


##
## === PROJECT PYTHON (LINUX/macOS) ===
##

def _project_python(target_dir: Path) -> str:
    project_python_path = target_dir / ".venv" / "bin" / "python"
    if not project_python_path.exists():
        raise FileNotFoundError(
            f"Expected project interpreter at {project_python_path}. Create with: `uv venv`.",
        )
    return str(project_python_path)


##
## === CORE ACTIONS ===
##

def install_project_self(
    target_dir: Path,
    project_python_exe: str,
    dry_run: bool,
) -> bool:
    if dry_run:
        log_info(f'[dry-run] Would run in {target_dir}: uv pip install -e . --python "{project_python_exe}"')
        return True
    log_info(f"Installing project (editable) into: {target_dir}/.venv")
    was_successful = _run(
        f'uv pip install -e . --python "{project_python_exe}"',
        working_directory=target_dir,
    )
    log_action(
        "Editable install of project",
        outcome=(log_manager.ActionOutcome.SUCCESS if was_successful else log_manager.ActionOutcome.FAILURE),
    )
    return was_successful


def link_alias_into_project(
    target_dir: Path,
    project_python_exe: str,
    module_alias: str,
    dry_run: bool,
) -> bool:
    module_local_path = SUBMODULES[module_alias].resolve()
    module_name = module_local_path.name

    if not module_local_path.exists():
        log_action(f"Submodule not found: {module_local_path}", outcome=log_manager.ActionOutcome.FAILURE)
        return False
    if module_local_path == target_dir.resolve():
        log_action(f"Refusing to link `{module_name}` into itself.", outcome=log_manager.ActionOutcome.FAILURE)
        return False

    if dry_run:
        log_info(f'[dry-run] Would link `{module_name}` from: {module_local_path} using --python "{project_python_exe}"')
        return True

    log_info(f"Linking `{module_name}` from: {module_local_path}")
    was_successful = _run(
        f'uv pip install -e "{module_local_path}" --python "{project_python_exe}"',
        working_directory=target_dir,
    )
    log_action(
        f"Linked `{module_name}`",
        outcome=(log_manager.ActionOutcome.SUCCESS if was_successful else log_manager.ActionOutcome.FAILURE),
    )
    return was_successful


def uninstall_alias_from_project(
    target_dir: Path,
    project_python_exe: str,
    module_alias: str,
    dry_run: bool,
) -> bool:
    module_local_path = SUBMODULES[module_alias].resolve()
    module_name = module_local_path.name

    if dry_run:
        log_info(f'[dry-run] Would uninstall `{module_name}` using --python "{project_python_exe}"')
        return True

    log_info(f"Uninstalling `{module_name}` from project env")
    was_successful = _run(
        f'uv pip uninstall {module_name} --python "{project_python_exe}"',
        working_directory=target_dir,
    )
    log_action(
        f"Uninstalled `{module_name}`",
        outcome=(log_manager.ActionOutcome.SUCCESS if was_successful else log_manager.ActionOutcome.FAILURE),
    )
    return was_successful


##
## === ARG PARSING ===
##

def parse_args():
    parser = argparse.ArgumentParser(
        description="Link/unlink local submodules into an existing target project's uv env (no state, no verification).",
    )
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Target project directory (must contain pyproject.toml and .venv)",
    )
    parser.add_argument("--self-install", action="store_true", help="Editable install of the project itself")
    for module_alias in sorted(SUBMODULES):
        module_pretty = SUBMODULES[module_alias].name
        parser.add_argument(f"--{module_alias}", action="store_true", help=f"Link submodule `{module_pretty}`")
        parser.add_argument(f"--no-{module_alias}", action="store_true", help=f"Uninstall submodule `{module_pretty}`")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    return parser.parse_args()


##
## === WORKFLOW CLASS ===
##

class LinkWorkflow:
    def __init__(self, user_args):
        self.user_args = user_args

        # planned/derived state
        self.target_dir: Path | None = None
        self.project_python_exe: str | None = None
        self.selected_install_aliases: list[str] = []
        self.selected_uninstall_aliases: list[str] = []
        self.do_self_install: bool = False
        self.is_dry_run: bool = False

        # results
        self.results = ResultsSummary()

    def validate_and_plan(self) -> None:
        """Check inputs, resolve paths, choose actions, confirm with user."""
        target_dir = self.user_args.target_dir.resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target project directory does not exist: {target_dir}")

        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            log_action(f"No pyproject.toml found in {target_dir}", outcome=log_manager.ActionOutcome.FAILURE)
            sys.exit(1)

        try:
            project_python_exe = _project_python(target_dir)
        except Exception as exc:
            log_action(str(exc), outcome=log_manager.ActionOutcome.FAILURE)
            sys.exit(1)

        log_info(f"Target project directory: {target_dir}")
        log_info(f"Using interpreter: {project_python_exe}")
        user_response = input("Proceed? [y/N]: ").strip().lower()
        if user_response not in ("y", "yes"):
            log_action("Aborting per user input.", outcome=log_manager.ActionOutcome.SKIPPED)
            sys.exit(1)

        selected_install_aliases   = [a for a in sorted(SUBMODULES) if getattr(self.user_args, a)]
        selected_uninstall_aliases = [a for a in sorted(SUBMODULES) if getattr(self.user_args, f"no_{a}")]
        do_self_install = bool(self.user_args.self_install)
        is_dry_run = bool(self.user_args.dry_run)

        if not do_self_install and not selected_install_aliases and not selected_uninstall_aliases:
            log_info("No actions were provided. Examples:")
            log_info("  --self-install  or  --jormi  or  --no-jormi")
            sys.exit(1)

        # commit plan to instance
        self.target_dir = target_dir
        self.project_python_exe = project_python_exe
        self.selected_install_aliases = selected_install_aliases
        self.selected_uninstall_aliases = selected_uninstall_aliases
        self.do_self_install = do_self_install
        self.is_dry_run = is_dry_run

    def apply_actions(self) -> None:
        """Run: uninstalls → self-install (optional) → installs."""
        assert self.target_dir is not None and self.project_python_exe is not None

        # Uninstall first (clean slate)
        for module_alias in self.selected_uninstall_aliases:
            was_successful = uninstall_alias_from_project(
                self.target_dir, self.project_python_exe, module_alias, self.is_dry_run
            )
            self.results.uninstalls.append((module_alias, was_successful))

        # Editable install of the project itself
        if self.do_self_install:
            self.results.self_install = install_project_self(
                self.target_dir, self.project_python_exe, self.is_dry_run
            )

        # Link requested aliases
        for module_alias in self.selected_install_aliases:
            was_successful = link_alias_into_project(
                self.target_dir, self.project_python_exe, module_alias, self.is_dry_run
            )
            self.results.installs.append((module_alias, was_successful))

    def summarize_and_exit(self) -> None:
        """Log a concise summary and exit with 0 on success, 1 on any failure."""
        failed_uninstalls = [alias for alias, was_successful in self.results.uninstalls if not was_successful]
        failed_installs   = [alias for alias, was_successful in self.results.installs   if not was_successful]
        self_status       = self.results.self_install

        if failed_uninstalls:
            log_info(f"Uninstall failures: {', '.join(failed_uninstalls)}")
        if failed_installs:
            log_info(f"Install failures: {', '.join(failed_installs)}")
        if self_status is not None:
            log_info(f"Project editable install: {'succeeded' if self_status else 'failed'}")

        # Optional: full object for inspection
        log_info(f"Action results: {self.results}")

        flat_bools: list[bool] = []
        if self_status is not None:
            flat_bools.append(bool(self_status))
        flat_bools.extend(bool(was_successful) for _, was_successful in self.results.uninstalls)
        flat_bools.extend(bool(was_successful) for _, was_successful in self.results.installs)

        sys.exit(0 if all(flat_bools) else 1)

    def run(self) -> None:
        self.validate_and_plan()
        self.apply_actions()
        self.summarize_and_exit()


##
## === MAIN ===
##

def main():
    user_args = parse_args()
    LinkWorkflow(user_args).run()


##
## === ENTRY POINT ===
##

if __name__ == "__main__":
    main()

## } SCRIPT
