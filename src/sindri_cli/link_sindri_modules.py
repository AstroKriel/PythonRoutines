## { SCRIPT

##
## === DEPENDENCIES ===
##

import sys
import tomllib
import argparse
from typing import Any
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
    uninstalled_modules: list[tuple[str, bool]] = field(default_factory=list)
    installed_modules: list[tuple[str, bool]] = field(default_factory=list)
    broken_modules: list[tuple[str, str]] = field(default_factory=list)
    self_install: bool | None = None
    self_uninstall: bool | None = None


##
## === PLANNED INFO (reused later) ===
##


@dataclass
class PlannedInfo:
    install_aliases: list[str] = field(default_factory=list)
    uninstall_aliases: list[str] = field(default_factory=list)
    install_names: list[str] = field(default_factory=list)
    uninstall_names: list[str] = field(default_factory=list)
    broken_readable: str = "none"
    alias_to_name: dict[str, str] = field(default_factory=dict)


##
## === HELPERS FOR SUMMARY ===
##


def format_optional_outcome(
    flag: bool | None,
) -> str:
    return (log_manager.Symbols.EM_DASH.value if flag is None else ("succeeded" if flag else "failed"))


def format_batch_outcome(
    requested_aliases: list[str],
    failed_display_names: list[str],
) -> str:
    if not requested_aliases:
        return log_manager.Symbols.EM_DASH.value
    return "all succeeded" if not failed_display_names else f"failed: {', '.join(failed_display_names)}"


def list_or_dash(
    items: list[str],
) -> str:
    return ", ".join(items) if items else log_manager.Symbols.EM_DASH.value


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
    return [get_display_name(module_alias, module_statuses=module_statuses) for module_alias in module_aliases]


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
            log_manager.log_task(message, show_time=True)
        shell_manager.execute_shell_command(
            command,
            timeout_seconds=timeout_seconds,
            show_output=show_output,
            working_directory=str(working_directory) if working_directory else None,
        )
        return True
    except Exception as exception:
        log_manager.log_outcome(
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
        f"{name:<{column_width}} : {hint}" if
        (error_message is None) else f"{name:<{column_width}} : {error_message:>12} \n\t{hint}"
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
    log_manager.log_context(
        title="Package Status",
        message="Run any of the above to inspect editable installs (broken items are listed with a reason).",
        notes=notes,
    )


##
## === CORE ACTIONS ===
##


def self_install_project_status(target_dir: Path, dry_run: bool) -> bool:
    project_name = read_project_name(target_dir)
    command = "uv pip install -e ."
    title = "Install project"
    if dry_run:
        log_manager.log_action(
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
    log_manager.log_empty_lines(lines=1)
    log_manager.log_action(
        title=title,
        succeeded=succeeded,
        message=f"Command: {command}",
        notes={
            "project-name": project_name,
            "project-path": str(target_dir),
        },
    )
    return succeeded


def self_uninstall_project_status(target_dir: Path, dry_run: bool) -> bool:
    project_name = read_project_name(target_dir)
    command = f"uv pip uninstall {project_name}"
    title = "Uninstall project"
    if dry_run:
        log_manager.log_action(
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
    log_manager.log_empty_lines(lines=1)
    log_manager.log_action(
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
        log_manager.log_action(
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
        log_manager.log_action(
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
        log_manager.log_action(
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
        log_manager.log_action(
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
    log_manager.log_empty_lines(lines=1)
    log_manager.log_action(
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
        log_manager.log_action(
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
        log_manager.log_action(
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
    log_manager.log_empty_lines(lines=1)
    log_manager.log_action(
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
        self.module_statuses: dict[str, ModuleStatus] = {}
        self.plan = PlannedInfo()

    def parse_and_verify_args(
        self,
    ) -> None:
        target_dir = self.user_args.target_dir.resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target project directory does not exist: {target_dir}")
        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            log_manager.log_outcome(
                f"No pyproject.toml found in {target_dir}",
                outcome=log_manager.ActionOutcome.FAILURE,
            )
            sys.exit(1)
        try:
            ensure_project_root(target_dir)
        except Exception as exception:
            log_manager.log_outcome(
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
        self.modules_to_install = validated_modules_to_install
        self.plan.install_aliases = list(self.modules_to_install)
        self.plan.uninstall_aliases = list(self.modules_to_uninstall)
        self.plan.install_names = get_display_names(
            self.modules_to_install,
            module_statuses=self.module_statuses,
        )
        self.plan.uninstall_names = get_display_names(
            self.modules_to_uninstall,
            module_statuses=self.module_statuses,
        )
        self.plan.alias_to_name = {
            alias: get_display_name(alias, module_statuses=self.module_statuses)
            for alias in sorted(SINDRI_MODULES)
        }
        planned_installs = list_or_dash(self.plan.install_names)
        planned_uninstalls = list_or_dash(self.plan.uninstall_names)
        notes: dict[str, Any] = {
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
                f"{module_alias} {log_manager.Symbols.RIGHT_ARROW.value} "
                f"{get_display_name(module_alias, module_statuses=self.module_statuses)}[{reason}]"
                for module_alias, reason in self.results.broken_modules
            )
            self.plan.broken_readable = broken_readable
            notes["requested-broken-modules"] = broken_readable
        else:
            self.plan.broken_readable = "none"
        log_manager.log_context(
            title="Planned Actions",
            notes=notes,
            message="Review the items above.",
        )
        user_response = input("Proceed? [y/N]: ").strip().lower()
        if user_response not in ("y", "yes"):
            log_manager.log_outcome("Aborted by user.", outcome=log_manager.ActionOutcome.SKIPPED)
            sys.exit(1)
        log_manager.log_empty_lines(lines=1)
        modules_to_reinstall = set(self.modules_to_uninstall) & set(self.modules_to_install)
        if modules_to_reinstall:
            list_of_modules = ", ".join(
                sorted(get_display_name(alias, module_statuses=self.module_statuses) for alias in modules_to_reinstall),
            )
            log_manager.log_note(
                f"Reinstall will occur for: {list_of_modules} "
                f"(uninstall {log_manager.Symbols.RIGHT_ARROW.value} install)",
                show_time=True,
            )
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
            self.results.self_uninstall = self_uninstall_project_status(
                self.target_dir,
                self.is_dry_run,
            )
        if self.do_self_install:
            self.results.self_install = self_install_project_status(
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

    def summarise_and_exit(self) -> None:
        failed_uninstalls = [
            self.plan.alias_to_name[module_alias]
            for (module_alias, successful) in self.results.uninstalled_modules
            if not successful
        ]
        failed_installs = [
            self.plan.alias_to_name[module_alias]
            for (module_alias, successful) in self.results.installed_modules
            if not successful
        ]
        install_project_status = self.results.self_install
        uninstall_project_status = self.results.self_uninstall
        log_manager.log_summary(
            title="Final Summary",
            message="Finished.",
            notes={
                "project-install": format_optional_outcome(install_project_status),
                "project-uninstall": format_optional_outcome(uninstall_project_status),
                "module-uninstalls": format_batch_outcome(self.plan.uninstall_aliases, failed_uninstalls),
                "module-installs": format_batch_outcome(self.plan.install_aliases, failed_installs),
                "planned-installs": list_or_dash(self.plan.install_names),
                "planned-uninstalls": list_or_dash(self.plan.uninstall_names),
                "requested-broken-modules": self.plan.broken_readable,
            },
        )
        status_summary: list[bool] = []
        if install_project_status is not None:
            status_summary.append(bool(install_project_status))
        if uninstall_project_status is not None:
            status_summary.append(bool(uninstall_project_status))
        status_summary.extend(bool(successful) for (_, successful) in self.results.uninstalled_modules)
        status_summary.extend(bool(successful) for (_, successful) in self.results.installed_modules)
        sys.exit(0 if all(status_summary) else 1)

    def run(self) -> None:
        self.parse_and_verify_args()
        self.apply_requested_actions()
        self.summarise_and_exit()


##
## === MAIN ===
##


def main():
    user_args = parse_args()
    LinkModules(user_args).run()


if __name__ == "__main__":
    main()

## } SCRIPT
