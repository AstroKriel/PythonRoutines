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

SINDRI_MODULES: dict[str, Path] = {
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
    uninstalled_modules: list[tuple[str, bool]] = field(default_factory=list)  # (module_alias, successful)
    installed_modules: list[tuple[str, bool]] = field(default_factory=list)  # (module_alias, successful)
    broken_modules: list[tuple[str, str]] = field(default_factory=list)  # (module_alias, reason)
    self_install: bool | None = None  # editable install of the project
    self_uninstall: bool | None = None  # uninstall of the project package


##
## === LOGGING HELPERS ===
##


def log_detail(
    text: str,
) -> None:
    log_manager.render_line(
        log_manager.Message(
            text,
            message_type=log_manager.MessageType.DETAILS,
        ),
        show_time=True,
    )


def log_outcome(
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


def log_action(
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


def log_details(
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
        pyproject = tomllib.load(fp)
    project_name = pyproject.get("project", {}).get("name")
    if not project_name or not isinstance(project_name, str):
        raise ValueError(f"Could not determine project name from: {pyproject_path}")
    return project_name.lower()


##
## === CENTRALISED INTEGRITY CHECK ===
##


@dataclass(frozen=True)
class ModuleStatus:
    is_valid: bool
    module_alias: str
    module_path: Path
    module_name: str | None
    reason: str | None


def verify_sindri_module(
    module_alias: str,
) -> ModuleStatus:
    module_path = SINDRI_MODULES[module_alias].resolve()
    if not module_path.exists():
        return ModuleStatus(
            module_alias=module_alias,
            module_path=module_path,
            module_name=None,
            is_valid=False,
            reason="missing-path",
        )
    pyproject_path = module_path / "pyproject.toml"
    if not pyproject_path.exists():
        return ModuleStatus(
            module_alias=module_alias,
            module_path=module_path,
            module_name=None,
            is_valid=False,
            reason="missing-pyproject",
        )
    try:
        module_name = read_project_name(module_path)
        return ModuleStatus(
            module_alias=module_alias,
            module_path=module_path,
            module_name=module_name,
            is_valid=True,
            reason=None,
        )
    except Exception:
        return ModuleStatus(
            module_alias=module_alias,
            module_path=module_path,
            module_name=None,
            is_valid=False,
            reason="missing-project-name",
        )


def get_sindri_module_status() -> dict[str, ModuleStatus]:
    return {module_alias: verify_sindri_module(module_alias) for module_alias in SINDRI_MODULES}


def get_package_name(
    module_alias: str,
    *,
    module_statuses: dict[str, ModuleStatus],
) -> str:
    module_status = module_statuses[module_alias]
    if module_status.is_valid and module_status.module_name:
        return module_status.module_name
    raise ValueError(f"Cannot resolve package name for broken module: {module_alias} ({module_status.reason})")


def get_package_names(
    module_aliases: list[str],
    *,
    module_statuses: dict[str, ModuleStatus],
) -> list[str]:
    return [get_package_name(
        module_alias,
        module_statuses=module_statuses,
    ) for module_alias in module_aliases]


def get_display_name(
    module_alias: str,
    *,
    module_statuses: dict[str, ModuleStatus],
) -> str:
    module_status = module_statuses[module_alias]
    return module_status.module_name or module_status.module_path.name.lower().replace("_", "-")


def get_display_names(
    module_aliases: list[str],
    *,
    module_statuses: dict[str, ModuleStatus],
) -> list[str]:
    return [get_display_name(
        module_alias,
        module_statuses=module_statuses,
    ) for module_alias in module_aliases]


##
## === SHELL HELPERS ===
##


def run_command(
    command: str,
    *,
    working_directory: Path | None = None,
    timeout_seconds: int = 90,
    show_output: bool = True,
    message: str | None = None,
) -> bool:
    try:
        if message:
            log_manager.render_line(
                log_manager.Message(
                    message,
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
        log_outcome(
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
    *,
    module_statuses: dict[str, ModuleStatus],
) -> None:
    try:
        project_name = read_project_name(target_dir)
    except Exception:
        project_name = None
    rows: list[tuple[str, str | None, str]] = []
    width_candidates: list[str] = []
    for module_alias in sorted(module_statuses):
        module_status = module_statuses[module_alias]
        if module_status.is_valid and module_status.module_name:
            name = module_status.module_name
            error_message = None
            hint = f"uv pip show {name}"
        else:
            name = module_status.module_path.name.lower().replace("_", "-")
            error_message = f"BROKEN[{module_status.reason}]"
            hint = f"{log_manager.Symbols.HOOKED_ARROW.value} inspect: {module_status.module_path}"
        width_candidates.append(name)
        rows.append((name, error_message, hint))
    column_width = max((len(n) for n in width_candidates), default=8)
    lines = [
        f"{name:<{column_width}} : {hint}"
        if (error_message is None) else
        f"{name:<{column_width}} : {error_message:>12} \n\t{hint}"
        for (name, error_message, hint) in rows
    ]
    num_broken_modules = sum(1 for _, module_status_text, _ in rows if module_status_text is not None)
    num_valid_modules = len(rows) - num_broken_modules
    notes: dict[str, str] = {
        "all packages": "uv pip list  (check the 'Editable project location' column)",
        "project path": str(target_dir),
        "sindri modules": "\n\t" + "\n\t".join(lines),
        "summary": f"OK={num_valid_modules}, BROKEN={num_broken_modules}",
    }
    if project_name:
        notes["this project"] = f"uv pip show {project_name}"
    log_details(
        title="Package Status",
        message="Run any of the above to inspect editable installs (broken items are listed with a reason)",
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
        log_action(
            title=title,
            succeeded=None,
            message="[dry-run] Would run: uv pip install -e .",
            notes={"project-path": str(target_dir)},
        )
        return True
    succeeded = run_command(
        command,
        working_directory=target_dir,
        message=f"Installing project: {project_name}",
    )
    print(" ")
    log_action(
        title=title,
        succeeded=succeeded,
        message=f"Command: {command}",
        notes={
            "project-name": project_name,
            "project-path": str(target_dir),
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
        log_action(
            title=title,
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "project-name": project_name,
                "project-path": str(target_dir),
            },
        )
        return True
    succeeded = run_command(
        command,
        working_directory=target_dir,
        message=f"Uninstalling project: {project_name}",
    )
    print(" ")
    log_action(
        title=title,
        succeeded=succeeded,
        message=f"Command: {command}",
        notes={
            "project-name": project_name,
            "project-path": str(target_dir),
        },
    )
    return succeeded


def install_module_to_project(
    target_dir: Path,
    module_alias: str,
    dry_run: bool,
    *,
    module_statuses: dict[str, ModuleStatus],
) -> bool:
    module_status = module_statuses[module_alias]
    module_local_path = module_status.module_path

    if not module_status.is_valid or not module_status.module_name:
        log_action(
            title=f"Install `{module_alias}`",
            succeeded=False,
            message="Failed. Broken module (see notes).",
            notes={
                "module-alias": module_alias,
                "module-path": str(module_local_path),
                "reason": module_status.reason,
            },
        )
        return False
    module_name = module_status.module_name
    command = f'uv pip install -e "{module_local_path}"'
    title = f"Install `{module_name}`"
    if not module_local_path.exists():
        log_action(
            title=title,
            succeeded=False,
            message="Failed. Module path does not exist.",
            notes={
                "module-name": module_name,
                "module-path": str(module_local_path),
            },
        )
        return False
    if module_local_path == target_dir.resolve():
        log_action(
            title=title,
            succeeded=False,
            message="Failed. Refused to install module into itself.",
            notes={
                "module-name": module_name,
                "module-path": str(module_local_path),
            },
        )
        return False
    if dry_run:
        log_action(
            title=f"Planned install `{module_name}`",
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "module-name": module_name,
                "module-path": str(module_local_path),
                "target-project": str(target_dir),
            },
        )
        return True
    succeeded = run_command(
        command,
        working_directory=target_dir,
        message=f"Installing `{module_name}` module",
    )
    print(" ")
    log_action(
        title=f"Installed `{module_name}`",
        succeeded=succeeded,
        message=f"Command: {command}",
        notes={
            "module-name": module_name,
            "module-path": str(module_local_path),
            "target-project": str(target_dir),
        },
    )
    return succeeded


def uninstall_module_from_project(
    target_dir: Path,
    module_alias: str,
    dry_run: bool,
    *,
    module_statuses: dict[str, ModuleStatus],
) -> bool:
    module_status = module_statuses[module_alias]
    module_local_path = module_status.module_path
    if not module_status.is_valid or not module_status.module_name:
        log_action(
            title=f"Uninstall `{module_alias}`",
            succeeded=False,
            message="Failed. Broken module (cannot resolve package name).",
            notes={
                "module-alias": module_alias,
                "module-path": str(module_local_path),
                "reason": module_status.reason,
            },
        )
        return False
    module_name = module_status.module_name
    command = f"uv pip uninstall {module_name}"
    title = f"Uninstall `{module_name}`"
    if dry_run:
        log_action(
            title=title,
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "module-name": module_name,
                "target-project": str(target_dir),
            },
        )
        return True
    succeeded = run_command(
        command,
        working_directory=target_dir,
        message=f"Uninstalling `{module_name}` module",
    )
    print(" ")
    log_action(
        title=title,
        succeeded=succeeded,
        message=f"Command: {command}",
        notes={
            "module-name": module_name,
            "module-path": str(module_local_path),
            "target-project": str(target_dir),
        },
    )
    return succeeded


##
## === ARG PARSING ===
##


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install/uninstall local modules into an existing target project (editable installs via uv).",
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
        help="Uninstall the project editable install",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print commands you can run to check status",
    )
    for module_alias in sorted(SINDRI_MODULES):
        module_pretty = SINDRI_MODULES[module_alias].name
        parser.add_argument(
            f"--{module_alias}",
            action="store_true",
            help=f"Install module `{module_pretty}`",
        )
        parser.add_argument(
            f"--no-{module_alias}",
            action="store_true",
            help=f"Uninstall module `{module_pretty}`",
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
        self.module_statuses: dict[str, ModuleStatus] = {}  # central integrity cache

    def parse_and_verify_args(
        self,
    ) -> None:
        target_dir = self.user_args.target_dir.resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target project directory does not exist: {target_dir}")
        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            log_outcome(
                f"No pyproject.toml found in {target_dir}",
                outcome=log_manager.ActionOutcome.FAILURE,
            )
            # keep style: exit via sys.exit for hard failures
            sys.exit(1)
        try:
            ensure_project_root(target_dir)
        except Exception as exception:
            log_outcome(
                str(exception),
                outcome=log_manager.ActionOutcome.FAILURE,
            )
            sys.exit(1)
        self.module_statuses = get_sindri_module_status()
        self.modules_to_install = [
            module_alias for module_alias in sorted(SINDRI_MODULES) if getattr(self.user_args, module_alias)
        ]
        self.modules_to_uninstall = [
            module_alias for module_alias in sorted(SINDRI_MODULES) if getattr(self.user_args, f"no_{module_alias}")
        ]
        self.do_self_install = bool(self.user_args.self_install)
        self.do_self_uninstall = bool(self.user_args.self_uninstall)
        self.show_stutus_hint = bool(self.user_args.status)
        self.is_dry_run = bool(self.user_args.dry_run)
        validated_modules_to_install: list[str] = []
        for module_alias in self.modules_to_install:
            module_status = self.module_statuses[module_alias]
            if module_status.is_valid:
                validated_modules_to_install.append(module_alias)
            else:
                self.results.broken_modules.append((module_alias, str(module_status.reason)))
                log_outcome(
                    f"Skipping `{module_alias}` : broken module ({module_status.reason}).",
                    outcome=log_manager.ActionOutcome.FAILURE,
                )
        self.modules_to_install = validated_modules_to_install
        planned_installs = ", ".join(
            get_display_names(
                self.modules_to_install,
                module_statuses=self.module_statuses,
            ),
        ) or log_manager.Symbols.EM_DASH.value
        planned_uninstalls = ", ".join(
            get_display_names(
                self.modules_to_uninstall,
                module_statuses=self.module_statuses,
            ),
        ) or log_manager.Symbols.EM_DASH.value
        notes: dict[str, object] = {
            "target-project": str(target_dir),
            "self-install": self.do_self_install,
            "self-uninstall": self.do_self_uninstall,
            "installs": planned_installs,
            "uninstalls": planned_uninstalls,
            "status": self.show_stutus_hint,
            "dry-run": self.is_dry_run,
        }
        if self.results.broken_modules:
            broken_readable = ", ".join(
                f"{module_alias}({reason})" for module_alias, reason in self.results.broken_modules
            )
            notes["broken"] = broken_readable

        log_details(
            title="Planned Actions",
            notes=notes,
            message="Review the items above.",
        )
        user_response = input("Proceed? [y/N]: ").strip().lower()
        if user_response not in ("y", "yes"):
            log_outcome(
                "Aborted by user.",
                outcome=log_manager.ActionOutcome.SKIPPED,
            )
            sys.exit(1)
        print(" ")
        modules_to_reinstall = set(self.modules_to_uninstall) & set(self.modules_to_install)
        if modules_to_reinstall:
            list_of_modules = ", ".join(
                sorted(
                    get_display_name(module_alias, module_statuses=self.module_statuses)
                    for module_alias in modules_to_reinstall
                ),
            )
            log_detail(f"Reinstall will occur for: {list_of_modules} (uninstall {log_manager.Symbols.RIGHT_ARROW.value} install)")
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
                module_statuses=self.module_statuses,
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
                module_statuses=self.module_statuses,
            )
            self.results.installed_modules.append((module_alias, successful))
        if self.show_stutus_hint:
            render_status_hint_block(self.target_dir, module_statuses=self.module_statuses)

    def summarise_and_exit(
        self,
    ) -> None:
        failed_uninstalls = [
            get_display_name(module_alias, module_statuses=self.module_statuses)
            for (module_alias, successful) in self.results.uninstalled_modules
            if not successful
        ]
        failed_installs = [
            get_display_name(module_alias, module_statuses=self.module_statuses)
            for (module_alias, successful) in self.results.installed_modules
            if not successful
        ]
        self_status = self.results.self_install
        self_un_status = self.results.self_uninstall
        broken_summary = (
            "none" if not self.results.broken_modules else ", ".join(
                f"{get_display_name(module_alias, module_statuses=self.module_statuses)}[{reason}]"
                for module_alias, reason in self.results.broken_modules
            )
        )
        log_details(
            title="Final Summary",
            message="Finished.",
            notes={
                "self-install": ("—" if self_status is None else ("succeeded" if self_status else "failed")),
                "self-uninstall": ("—" if self_un_status is None else ("succeeded" if self_un_status else "failed")),
                "uninstalls": ("all succeeded" if not failed_uninstalls else f"failed: {', '.join(failed_uninstalls)}"),
                "installs": ("all succeeded" if not failed_installs else f"failed: {', '.join(failed_installs)}"),
                "broken": broken_summary,
            },
        )
        collected_results: list[bool] = []
        if self_status is not None:
            collected_results.append(bool(self_status))
        if self_un_status is not None:
            collected_results.append(bool(self_un_status))
        collected_results.extend(bool(successful) for (_, successful) in self.results.uninstalled_modules)
        collected_results.extend(bool(successful) for (_, successful) in self.results.installed_modules)
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
