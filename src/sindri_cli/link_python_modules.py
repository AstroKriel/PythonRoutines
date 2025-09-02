## { SCRIPT
##
## === DEPENDENCIES ===
##

import sys
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from jormi.ww_io import shell_manager, log_manager

##
## === GLOBAL PARAMS ===
##

_SCRIPT_DIR = Path(__file__).resolve().parent
SINDRI_DIR = _SCRIPT_DIR.parent.parent

SUBMODULES: dict[str, Path] = {
    "jormi": SINDRI_DIR / "submodules/jormi",
    "bifrost": SINDRI_DIR / "submodules/bifrost",
    "vegtamr": SINDRI_DIR / "submodules/vegtamr",
    "quokka": SINDRI_DIR / "submodules/ww_quokka_sims",
    "flash": SINDRI_DIR / "submodules/ww_flash_sims",
    "arepo": SINDRI_DIR / "submodules/ww_arepo_sims",
}

##
## === RESULTS STRUCT ===
##


@dataclass
class ResultsSummary:
    uninstalled_modules: list[tuple[str, bool]] = field(default_factory=list)  # (alias_name, successful)
    installed_modules: list[tuple[str, bool]] = field(default_factory=list)  # (alias_name, successful)
    self_install: bool | None = None  # project editable install


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


def run_command(
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
    except Exception as exception:
        log_action(
            f"Command failed: {command}\n{exception}",
            outcome=log_manager.ActionOutcome.FAILURE,
        )
        return False


##
## === PROJECT PYTHON (LINUX/macOS) ===
##


def ensure_project_venv_is_local(target_dir: Path) -> None:
    venv_path = target_dir / ".venv"
    if not venv_path.exists() or not venv_path.is_dir():
        raise FileNotFoundError(
            f"No virtual-environment directory found under: {venv_path}\n"
            "Create once with: `uv venv`"
        )


##
## === CORE ACTIONS ===
##


def self_install_project(
    target_dir: Path,
    dry_run: bool,
) -> bool:
    if dry_run:
        log_info(f'[dry-run] Would run in {target_dir}: `uv pip install -e .`')
        return True
    log_info(f"Installing project (editable) into: {target_dir}/.venv")
    successful = run_command(
        f'uv pip install -e .',
        working_directory=target_dir,
    )
    log_action(
        "Editable install of project",
        outcome=(log_manager.ActionOutcome.SUCCESS if successful else log_manager.ActionOutcome.FAILURE),
    )
    return successful


def link_module_to_project(
    target_dir: Path,
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
        log_info(f'[dry-run] Would link `{module_name}` from: {module_local_path}')
        return True
    log_info(f"Linking `{module_name}` from: {module_local_path}")
    successful = run_command(
        f'uv pip install -e "{module_local_path}"',
        working_directory=target_dir,
    )
    log_action(
        f"Linked `{module_name}`",
        outcome=(log_manager.ActionOutcome.SUCCESS if successful else log_manager.ActionOutcome.FAILURE),
    )
    return successful


def unlink_module_from_project(
    target_dir: Path,
    module_alias: str,
    dry_run: bool,
) -> bool:
    module_local_path = SUBMODULES[module_alias].resolve()
    module_name = module_local_path.name
    if dry_run:
        log_info(f'[dry-run] Would uninstall `{module_name}`')
        return True
    log_info(f"Uninstalling `{module_name}` from project env")
    successful = run_command(
        f'uv pip uninstall {module_name}',
        working_directory=target_dir,
    )
    log_action(
        f"Uninstalled `{module_name}`",
        outcome=(log_manager.ActionOutcome.SUCCESS if successful else log_manager.ActionOutcome.FAILURE),
    )
    return successful


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


class LinkModules:

    def __init__(self, user_args):
        self.user_args = user_args

        self.target_dir: Path | None = None
        self.selected_install_aliases: list[str] = []
        self.selected_uninstall_aliases: list[str] = []
        self.do_self_install: bool = False
        self.is_dry_run: bool = False

        self.results = ResultsSummary()

    def parse_and_verify_args(self) -> None:
        """Check inputs, resolve paths, choose actions, confirm with user."""
        target_dir = self.user_args.target_dir.resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target project directory does not exist: {target_dir}")
        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            log_action(f"No pyproject.toml found in {target_dir}", outcome=log_manager.ActionOutcome.FAILURE)
            sys.exit(1)
        try:
            ensure_project_venv_is_local(target_dir)
        except Exception as exception:
            log_action(str(exception), outcome=log_manager.ActionOutcome.FAILURE)
            sys.exit(1)
        log_info(f"Target project directory: {target_dir}")
        user_response = input("Proceed? [y/N]: ").strip().lower()
        if user_response not in ("y", "yes"):
            log_action("Aborting per user input.", outcome=log_manager.ActionOutcome.SKIPPED)
            sys.exit(1)
        selected_install_aliases = [a for a in sorted(SUBMODULES) if getattr(self.user_args, a)]
        selected_uninstall_aliases = [a for a in sorted(SUBMODULES) if getattr(self.user_args, f"no_{a}")]
        do_self_install = bool(self.user_args.self_install)
        is_dry_run = bool(self.user_args.dry_run)
        if not do_self_install and not selected_install_aliases and not selected_uninstall_aliases:
            log_info("No actions were provided. Examples:")
            log_info("  --self-install  or  --jormi  or  --no-jormi")
            sys.exit(1)
        self.target_dir = target_dir
        self.selected_install_aliases = selected_install_aliases
        self.selected_uninstall_aliases = selected_uninstall_aliases
        self.do_self_install = do_self_install
        self.is_dry_run = is_dry_run

    def apply_actions(self) -> None:
        """Run: uninstalled_modules → self-install (optional) → installed_modules."""
        assert self.target_dir is not None
        ## first unlink (uninstall) requested modules
        for module_alias in self.selected_uninstall_aliases:
            successful = unlink_module_from_project(
                self.target_dir,
                module_alias,
                self.is_dry_run,
            )
            self.results.uninstalled_modules.append((module_alias, successful))
        ## install project inplace
        if self.do_self_install:
            self.results.self_install = self_install_project(
                self.target_dir,
                self.is_dry_run,
            )
        ## link (editable install) requested modules
        for module_alias in self.selected_install_aliases:
            successful = link_module_to_project(
                self.target_dir,
                module_alias,
                self.is_dry_run,
            )
            self.results.installed_modules.append((module_alias, successful))

    def summarize_and_exit(self) -> None:
        failed_uninstalls = [alias for (alias, successful) in self.results.uninstalled_modules if not successful]
        failed_installs = [alias for (alias, successful) in self.results.installed_modules if not successful]
        self_status = self.results.self_install
        if failed_uninstalls: log_info(f"Uninstall failures: {', '.join(failed_uninstalls)}")
        if failed_installs: log_info(f"Install failures: {', '.join(failed_installs)}")
        if self_status is not None: log_info(f"Project editable install: {'succeeded' if self_status else 'failed'}")
        log_info(f"Summarised results: {self.results}")
        collected_results: list[bool] = []
        if self_status is not None:
            collected_results.append(bool(self_status))
        collected_results.extend(bool(successful) for _, successful in self.results.uninstalled_modules)
        collected_results.extend(bool(successful) for _, successful in self.results.installed_modules)
        sys.exit(0 if all(collected_results) else 1)

    def run(self) -> None:
        self.parse_and_verify_args()
        self.apply_actions()
        self.summarize_and_exit()


##
## === MAIN ===
##


def main():
    user_args = parse_args()
    LinkModules(user_args).run()


##
## === ENTRY POINT ===
##

if __name__ == "__main__":
    main()

## } SCRIPT
