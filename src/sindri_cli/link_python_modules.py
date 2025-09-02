## { SCRIPT
##
## === DEPENDENCIES ===
##

import sys
import tomllib
import argparse
from pathlib import Path
from dataclasses import dataclass, field
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
    self_install: bool | None = None  # editable install of the project
    self_uninstall: bool | None = None  # uninstall of the project package


##
## === LOGGING HELPERS ===
##


def log_info(
    text: str,
) -> None:
    log_manager.render_line(
        log_manager.Message(
            text,
            message_type=log_manager.MessageType.DETAILS,
        ),
        show_time=True,
    )


def log_action(
    text: str,
    *,
    outcome: log_manager.ActionOutcome,
) -> None:
    log_manager.render_line(
        log_manager.Message(
            text,
            message_type=log_manager.MessageType.ACTION,
            action_outcome=outcome,
        ),
        show_time=True,
    )


def render_action_block(
    *,
    title: str,
    succeeded: bool | None,
    message: str = "",
    notes: dict[str, object] | None = None,
) -> None:
    if succeeded is None:
        outcome = log_manager.ActionOutcome.SKIPPED
    elif succeeded:
        outcome = log_manager.ActionOutcome.SUCCESS
    else:
        outcome = log_manager.ActionOutcome.FAILURE
    log_manager.render_block(
        log_manager.Message(
            message=message,
            message_type=log_manager.MessageType.ACTION,
            message_title=title,
            action_outcome=outcome,
            message_notes=(notes or {}),
        ),
        show_time=True,
    )


def render_general_block(
    *,
    title: str,
    message: str = "",
    message_type: log_manager.MessageType = log_manager.MessageType.DETAILS,
    notes: dict[str, str] | dict[str, object] | None = None,
) -> None:
    log_manager.render_block(
        log_manager.Message(
            message=message,
            message_type=message_type,
            message_title=title,
            message_notes=(notes or {}),
        ),
        show_time=True,
    )


##
## === PYPROJECT HELPERS ===
##


def read_project_name(
    target_dir: Path,
) -> str:
    pyproject_path = target_dir / "pyproject.toml"
    with pyproject_path.open("rb") as fp:
        data = tomllib.load(fp)
    name = data.get("project", {}).get("name")
    if not name or not isinstance(name, str):
        raise ValueError(f"Could not determine project name from: {pyproject_path}")
    return name.lower()


def package_name_for_alias(
    module_alias: str,
) -> str:
    """
    Resolve the *package* name for a given alias (prefers pyproject name; falls back to dashed dir name).
    """
    module_path = SUBMODULES[module_alias]
    try:
        return read_project_name(module_path)
    except Exception:
        return module_path.name.lower().replace("_", "-")


def names_from_aliases(
    aliases: list[str],
) -> list[str]:
    return [package_name_for_alias(a) for a in aliases]


##
## === SHELL HELPERS ===
##


def run_command(
    command: str,
    *,
    working_directory: Path | None = None,
    timeout_seconds: int = 90,
    show_output: bool = True,
    pre_action_message: str | None = None,
) -> bool:
    """
    Optionally log a single-line message *before* executing the shell command.
    """
    try:
        if pre_action_message:
            log_manager.render_line(
                log_manager.Message(
                    pre_action_message,
                    message_type=log_manager.MessageType.STEP,
                ),
                show_time=True,
            )
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
## === CHECK PROJECT ENV ===
##


def ensure_project_root(
    target_dir: Path,
) -> None:
    venv_path = target_dir / ".venv"
    if not venv_path.exists() or not venv_path.is_dir():
        raise FileNotFoundError(
            f"No virtual-environment directory found under: {venv_path}\n"
            "Create once with: `uv venv`.",
        )


##
## === STATUS HINTS ===
##


def render_status_hint_block(
    target_dir: Path,
) -> None:
    try:
        project_name = read_project_name(target_dir)
    except Exception:
        project_name = None
    pkg_names = [package_name_for_alias(a) for a in sorted(SUBMODULES)]
    width = max((len(n) for n in pkg_names), default=8)
    sub_lines = [f"{pkg:<{width}} : uv pip show {pkg}" for pkg in pkg_names]
    notes: dict[str, str] = {
        "All packages": "uv pip list  (check the 'Editable project location' column)",
        "Project path": str(target_dir),
        "Sindri Submodules": "\n\t" + "\n\t".join(sub_lines),
    }
    if project_name:
        notes["This project"] = f"uv pip show {project_name}"
    render_general_block(
        title="Package Status",
        message="Run any of the above to inspect editable installs.",
        message_type=log_manager.MessageType.HINT,
        notes=notes,
    )


##
## === CORE ACTIONS ===
##


def self_install_project(
    target_dir: Path,
    dry_run: bool,
) -> bool:
    project_name = read_project_name(target_dir)
    command = "uv pip install -e ."
    title = "Install project"
    if dry_run:
        render_action_block(
            title=title,
            succeeded=None,
            message="[dry-run] Would run: uv pip install -e .",
            notes={"project": str(target_dir)},
        )
        return True
    succeeded = run_command(
        command,
        working_directory=target_dir,
        pre_action_message=f"Installing project: {project_name}",
    )
    print(" ")
    render_action_block(
        title=title,
        succeeded=succeeded,
        message=("Completed." if succeeded else "Failed."),
        notes={
            "project": str(target_dir),
            "command": command,
        },
    )
    return succeeded


def self_uninstall_project(
    target_dir: Path,
    dry_run: bool,
) -> bool:
    project_name = read_project_name(target_dir)
    command = f"uv pip uninstall {project_name}"
    title = "Uninstall project"
    if dry_run:
        render_action_block(
            title=title,
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "project": str(target_dir),
                "package": project_name,
            },
        )
        return True
    succeeded = run_command(
        command,
        working_directory=target_dir,
        pre_action_message=f"Uninstalling project: {project_name}",
    )
    print(" ")
    render_action_block(
        title=title,
        succeeded=succeeded,
        message=("Completed." if succeeded else "Failed."),
        notes={
            "project": str(target_dir),
            "package": project_name,
            "command": command,
        },
    )
    return succeeded


def install_module_to_project(
    target_dir: Path,
    module_alias: str,
    dry_run: bool,
) -> bool:
    module_local_path = SUBMODULES[module_alias].resolve()
    package_name = package_name_for_alias(module_alias)
    command = f'uv pip install -e "{module_local_path}"'
    title = f"Install `{package_name}`"
    if not module_local_path.exists():
        render_action_block(
            title=title,
            succeeded=False,
            message="Failed. Submodule path does not exist.",
            notes={
                "package": package_name,
                "module-path": str(module_local_path),
            },
        )
        return False
    if module_local_path == target_dir.resolve():
        render_action_block(
            title=title,
            succeeded=False,
            message="Failed. Refused to install module into itself.",
            notes={
                "package": package_name,
                "module-path": str(module_local_path),
            },
        )
        return False
    if dry_run:
        render_action_block(
            title=f"Planned install `{package_name}`",
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "package": package_name,
                "module-path": str(module_local_path),
                "project": str(target_dir),
            },
        )
        return True
    succeeded = run_command(
        command,
        working_directory=target_dir,
        pre_action_message=f"Installing `{package_name}` module",
    )
    print(" ")
    render_action_block(
        title=f"Installed `{package_name}`",
        succeeded=succeeded,
        message=("Completed." if succeeded else "Failed."),
        notes={
            "package": package_name,
            "module-path": str(module_local_path),
            "project": str(target_dir),
            "command": command,
        },
    )
    return succeeded


def uninstall_module_from_project(
    target_dir: Path,
    module_alias: str,
    dry_run: bool,
) -> bool:
    module_local_path = SUBMODULES[module_alias].resolve()
    package_name = package_name_for_alias(module_alias)
    command = f"uv pip uninstall {package_name}"
    title = f"Uninstall `{package_name}`"
    if dry_run:
        render_action_block(
            title=title,
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "package": package_name,
                "project": str(target_dir),
            },
        )
        return True
    succeeded = run_command(
        command,
        working_directory=target_dir,
        pre_action_message=f"Uninstalling `{package_name}` module",
    )
    print(" ")
    render_action_block(
        title=title,
        succeeded=succeeded,
        message=("Completed." if succeeded else "Failed."),
        notes={
            "package-name": package_name,
            "package-path": module_local_path,
            "project": str(target_dir),
            "command": command,
        },
    )
    return succeeded


##
## === ARG PARSING ===
##


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install/uninstall local submodules into an existing target project (editable installs via uv).",
    )
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Target project directory (must contain pyproject.toml and .venv)",
    )
    parser.add_argument(
        "--self-install",
        action="store_true",
        help="Editable install of the project itself",
    )
    parser.add_argument(
        "--self-uninstall",
        action="store_true",
        help="Uninstall the project's editable install",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print commands you can run to check status",
    )
    for module_alias in sorted(SUBMODULES):
        module_pretty = SUBMODULES[module_alias].name
        parser.add_argument(
            f"--{module_alias}",
            action="store_true",
            help=f"Install submodule `{module_pretty}`",
        )
        parser.add_argument(
            f"--no-{module_alias}",
            action="store_true",
            help=f"Uninstall submodule `{module_pretty}`",
        )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without executing",
    )
    return parser.parse_args()


##
## === WORKFLOW CLASS ===
##


class LinkModules:

    def __init__(
        self,
        user_args,
    ):
        self.user_args = user_args
        self.target_dir: Path | None = None
        self.modules_to_install: list[str] = []
        self.modules_to_uninstall: list[str] = []
        self.do_self_install: bool = False
        self.do_self_uninstall: bool = False
        self.show_stutus_hint: bool = False
        self.is_dry_run: bool = False
        self.results = ResultsSummary()

    def parse_and_verify_args(
        self,
    ) -> None:
        target_dir = self.user_args.target_dir.resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target project directory does not exist: {target_dir}")
        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            log_action(
                f"No pyproject.toml found in {target_dir}",
                outcome=log_manager.ActionOutcome.FAILURE,
            )
            sys.exit(1)
        try:
            ensure_project_root(target_dir)
        except Exception as exception:
            log_action(
                str(exception),
                outcome=log_manager.ActionOutcome.FAILURE,
            )
            sys.exit(1)
        self.modules_to_install = [a for a in sorted(SUBMODULES) if getattr(self.user_args, a)]
        self.modules_to_uninstall = [a for a in sorted(SUBMODULES) if getattr(self.user_args, f"no_{a}")]
        self.do_self_install = bool(self.user_args.self_install)
        self.do_self_uninstall = bool(self.user_args.self_uninstall)
        self.show_stutus_hint = bool(self.user_args.status)
        self.is_dry_run = bool(self.user_args.dry_run)
        planned_installs = ", ".join(names_from_aliases(self.modules_to_install)) or "—"
        planned_uninstalls = ", ".join(names_from_aliases(self.modules_to_uninstall)) or "—"
        render_general_block(
            title="Planned Actions",
            message="Review the items below.",
            notes={
                "project": str(target_dir),
                "self-install": self.do_self_install,
                "self-uninstall": self.do_self_uninstall,
                "installs": planned_installs,
                "uninstalls": planned_uninstalls,
                "status": self.show_stutus_hint,
                "dry-run": self.is_dry_run,
            },
        )
        user_response = input("Proceed? [y/N]: ").strip().lower()
        if user_response not in ("y", "yes"):
            log_action(
                "Aborted by user.",
                outcome=log_manager.ActionOutcome.SKIPPED,
            )
            sys.exit(1)
        print(" ")
        modules_to_reinstall = set(self.modules_to_uninstall) & set(self.modules_to_install)
        if modules_to_reinstall:
            names = ", ".join(sorted(package_name_for_alias(a) for a in modules_to_reinstall))
            log_info(f"Reinstall will occur for: {names} (uninstall → install)")
        self.target_dir = target_dir

    def apply_requested_actions(
        self,
    ) -> None:
        assert self.target_dir is not None
        for module_alias in self.modules_to_uninstall:
            successful = uninstall_module_from_project(
                self.target_dir,
                module_alias,
                self.is_dry_run,
            )
            self.results.uninstalled_modules.append((module_alias, successful))
        if self.do_self_uninstall:
            self.results.self_uninstall = self_uninstall_project(
                self.target_dir,
                self.is_dry_run,
            )
        if self.do_self_install:
            self.results.self_install = self_install_project(
                self.target_dir,
                self.is_dry_run,
            )
        for module_alias in self.modules_to_install:
            successful = install_module_to_project(
                self.target_dir,
                module_alias,
                self.is_dry_run,
            )
            self.results.installed_modules.append((module_alias, successful))
        if self.show_stutus_hint:
            render_status_hint_block(self.target_dir)

    def summarise_and_exit(
        self,
    ) -> None:
        failed_uninstalls = [
            package_name_for_alias(alias) for (alias, successful) in self.results.uninstalled_modules if not successful
        ]
        failed_installs = [
            package_name_for_alias(alias) for (alias, successful) in self.results.installed_modules if not successful
        ]
        self_status = self.results.self_install
        self_un_status = self.results.self_uninstall
        render_general_block(
            title="Final Summary",
            message="Completed with the following results.",
            notes={
                "self-install": ("—" if self_status is None else ("succeeded" if self_status else "failed")),
                "self-uninstall": ("—" if self_un_status is None else ("succeeded" if self_un_status else "failed")),
                "uninstalls": ("all succeeded" if not failed_uninstalls else f"failed: {', '.join(failed_uninstalls)}"),
                "installs": ("all succeeded" if not failed_installs else f"failed: {', '.join(failed_installs)}"),
            },
        )
        collected_results: list[bool] = []
        if self_status is not None:
            collected_results.append(bool(self_status))
        if self_un_status is not None:
            collected_results.append(bool(self_un_status))
        collected_results.extend(bool(successful) for _, successful in self.results.uninstalled_modules)
        collected_results.extend(bool(successful) for _, successful in self.results.installed_modules)
        sys.exit(0 if all(collected_results) else 1)

    def run(
        self,
    ) -> None:
        self.parse_and_verify_args()
        self.apply_requested_actions()
        self.summarise_and_exit()


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
