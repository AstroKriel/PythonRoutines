## { SCRIPT

##
## === DEPENDENCIES ===
##

import sys
import json
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

SINDRI_PACKAGES: dict[str, Path] = {
    "jormi": SINDRI_DIR / "submodules/jormi",
    "bifrost": SINDRI_DIR / "submodules/bifrost",
    "vegtamr": SINDRI_DIR / "submodules/vegtamr",
    "quokka": SINDRI_DIR / "submodules/ww_quokka_sims",
    "flash": SINDRI_DIR / "submodules/ww_flash_sims",
    "arepo": SINDRI_DIR / "submodules/ww_arepo_sims",
}

##
## === TYPE ALIASES ===
##

AliasName = str
PackageName = str

##
## === DATA MODELS ===
##


@dataclass
class PlannedSummary:
    install_aliases: list[AliasName] = field(default_factory=list)
    uninstall_aliases: list[AliasName] = field(default_factory=list)
    install_names: list[PackageName] = field(default_factory=list)
    uninstall_names: list[PackageName] = field(default_factory=list)
    broken_aliases: str = "none"
    alias_to_name: dict[AliasName, PackageName] = field(default_factory=dict)


@dataclass
class ResultsSummary:
    uninstalled_packages: list[tuple[AliasName, bool]] = field(default_factory=list)
    installed_packages: list[tuple[AliasName, bool]] = field(default_factory=list)
    broken_aliases: list[tuple[AliasName, str]] = field(default_factory=list)
    self_install: bool | None = None
    self_uninstall: bool | None = None


@dataclass(frozen=True)
class PackageStatus:
    is_valid: bool
    package_alias: AliasName
    package_path: Path
    package_name: PackageName | None
    reason: str | None


@dataclass(frozen=True)
class CommandOutcome:
    success: bool
    output: str | None


##
## === FORMATTING HELPERS ===
##


def arrow_label(
    alias: AliasName,
    name: PackageName,
) -> str:
    return alias if (alias == name) else f"{alias} {log_manager.Symbols.RIGHT_ARROW.value} {name}"


def format_optional_outcome(
    flag: bool | None,
) -> str:
    return (log_manager.Symbols.EM_DASH.value if (flag is None) else ("succeeded" if flag else "failed"))


def format_batch_outcome(
    requested_aliases: list[AliasName],
    failed_package_names: list[PackageName],
) -> str:
    if not requested_aliases:
        return log_manager.Symbols.EM_DASH.value
    return "all succeeded" if not failed_package_names else f"failed: {', '.join(failed_package_names)}"


def split_success_failure(
    results: list[tuple[AliasName, bool]],
    *,
    alias_to_name: dict[AliasName, PackageName],
    failure_reasons: dict[AliasName, str] | None = None,
) -> tuple[list[PackageName], list[PackageName]]:
    succeeded: list[PackageName] = []
    failed: list[PackageName] = []
    for alias, success in results:
        name = alias_to_name.get(alias, alias)
        if success:
            succeeded.append(name)
        else:
            reason = (failure_reasons or {}).get(alias)
            failed.append(name if not reason else f"{name}[{reason}]")
    return succeeded, failed


def list_or_dash(items: list[str]) -> str:
    return ", ".join(items) if items else log_manager.Symbols.EM_DASH.value


##
## === PYPROJECT / SHELL HELPERS ===
##


def read_package_name(
    target_dir: Path,
) -> str:
    pyproject_path = target_dir / "pyproject.toml"
    with pyproject_path.open("rb") as fp:
        pyproject = tomllib.load(fp)
    package_name = pyproject.get("project", {}).get("name")
    if not package_name or not isinstance(package_name, str):
        raise ValueError(f"Could not determine package name from: {pyproject_path}")
    return package_name.lower()


def run_command(
    command: str,
    *,
    working_directory: Path | None = None,
    timeout_seconds: int = 90,
    capture_output: bool = False,
    use_shell: bool = False,
    message: str | None = None,
) -> CommandOutcome:
    try:
        if message:
            log_manager.log_task(message, show_time=True)
        result = shell_manager.execute_shell_command(
            command,
            working_directory=working_directory,
            timeout_seconds=timeout_seconds,
            use_shell=use_shell,
            capture_output=capture_output,
        )
        return CommandOutcome(
            success=result.succeeded,
            output=result.stdout if capture_output else None,
        )
    except Exception as exception:
        log_manager.log_outcome(
            f"Command failed: {command}\n{exception}",
            outcome=log_manager.ActionOutcome.FAILURE,
        )
        return CommandOutcome(success=False, output=None)


##
## === PACKAGE VERIFICATION ===
##


def verify_sindri_package(
    package_alias: AliasName,
) -> PackageStatus:
    package_path = SINDRI_PACKAGES[package_alias].resolve()
    if not package_path.exists():
        return PackageStatus(
            package_alias=package_alias,
            package_path=package_path,
            package_name=None,
            is_valid=False,
            reason="missing-path",
        )
    pyproject_path = package_path / "pyproject.toml"
    if not pyproject_path.exists():
        return PackageStatus(
            package_alias=package_alias,
            package_path=package_path,
            package_name=None,
            is_valid=False,
            reason="missing-pyproject",
        )
    try:
        package_name = read_package_name(package_path)
        return PackageStatus(
            package_alias=package_alias,
            package_path=package_path,
            package_name=package_name,
            is_valid=True,
            reason=None,
        )
    except Exception:
        return PackageStatus(
            package_alias=package_alias,
            package_path=package_path,
            package_name=None,
            is_valid=False,
            reason="missing-package-name",
        )


def verify_sindri_packages() -> dict[AliasName, PackageStatus]:
    return {package_alias: verify_sindri_package(package_alias) for package_alias in SINDRI_PACKAGES}


def get_package_name(
    package_alias: AliasName,
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> PackageName:
    package_status = sindri_packages[package_alias]
    return package_status.package_name or package_alias


def get_package_names(
    package_aliases: list[AliasName],
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> list[PackageName]:
    return [get_package_name(package_alias, sindri_packages=sindri_packages) for package_alias in package_aliases]


##
## === ENV INSPECTION (uv) ===
##


def _installed_packages_lower() -> set[str]:
    outcome = run_command("uv pip list --format=json", capture_output=True)
    if not outcome.success or not outcome.output:
        return set()
    try:
        entries = json.loads(outcome.output)
        return {str(entry.get("name", "")).lower() for entry in entries if isinstance(entry, dict)}
    except Exception:
        return set()


def compute_sindri_install_state(
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> dict[AliasName, bool]:
    installed = _installed_packages_lower()
    state: dict[AliasName, bool] = {}
    for alias, status in sindri_packages.items():
        if status.is_valid and status.package_name:
            state[alias] = (status.package_name.lower() in installed)
        else:
            state[alias] = False
    return state


def format_install_state_summary_arrow(
    state: dict[AliasName, bool],
    *,
    alias_to_name: dict[AliasName, PackageName],
) -> tuple[str, str]:
    dash = log_manager.Symbols.EM_DASH.value
    installed_aliases = sorted([alias_name for (alias_name, success) in state.items() if success])
    missing_aliases = sorted([alias_name for (alias_name, success) in state.items() if not success])
    installed_labels = [arrow_label(alias_name, alias_to_name[alias_name]) for alias_name in installed_aliases]
    missing_labels = [arrow_label(alias_name, alias_to_name[alias_name]) for alias_name in missing_aliases]
    return (
        ", ".join(installed_labels) if installed_labels else dash,
        ", ".join(missing_labels) if missing_labels else dash,
    )


##
## === ENVIRONMENT CHECKS ===
##


def ensure_package_root(
    target_dir: Path,
) -> None:
    venv_path = target_dir / ".venv"
    if not venv_path.exists() or not venv_path.is_dir():
        raise FileNotFoundError(
            f"No virtual-environment directory found under: {venv_path}\n"
            "Create once with: `uv venv`.",
        )


##
## === RENDERING ===
##


def render_status_hint_block(
    target_dir: Path,
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> None:
    try:
        package_name = read_package_name(target_dir)
    except Exception:
        package_name = None
    rows: list[tuple[str, str | None, str]] = []
    width_candidates: list[str] = []
    for package_alias in sorted(sindri_packages):
        package_status = sindri_packages[package_alias]
        if package_status.is_valid and package_status.package_name:
            name = package_status.package_name
            error_message = None
            hint = f"uv pip show {name}"
        else:
            name = package_status.package_path.name.lower().replace("_", "-")
            error_message = f"BROKEN[{package_status.reason}]"
            hint = f"{log_manager.Symbols.HOOKED_ARROW.value} inspect: {package_status.package_path}"
        width_candidates.append(name)
        rows.append((name, error_message, hint))
    column_width = max((len(n) for n in width_candidates), default=8)
    lines = [
        f"{name:<{column_width}} : {hint}" if
        (error_message is None) else f"{name:<{column_width}} : {error_message:>12} \n\t{hint}"
        for (name, error_message, hint) in rows
    ]
    num_broken_packages = sum(1 for _, package_status_text, _ in rows if package_status_text is not None)
    num_valid_packages = len(rows) - num_broken_packages
    notes: dict[str, str] = {
        "all packages": "uv pip list  (check the third column)",
        "package path": str(target_dir),
        "sindri packages": "\n\t" + "\n\t".join(lines),
        "summary": f"OK={num_valid_packages}, BROKEN={num_broken_packages}",
    }
    if package_name:
        notes["this package"] = f"uv pip show {package_name}"
    log_manager.log_context(
        title="Package Status",
        message="Run any of the above to inspect editable installs (broken items are listed with alias_name reason).",
        notes=notes,
    )


##
## === CORE ACTIONS ===
##


def self_install_package(
    target_dir: Path,
    dry_run: bool,
) -> bool:
    package_name = read_package_name(target_dir)
    command = "uv pip install -e ."
    title = "Install package"
    if dry_run:
        log_manager.log_action(
            title=title,
            succeeded=None,
            message="[dry-run] Would run: uv pip install -e .",
            notes={
                "package-path": str(target_dir),
            },
        )
        return True
    result = run_command(
        command,
        working_directory=target_dir,
        capture_output=False,
        message=f"Installing package: {package_name}",
    )
    log_manager.log_empty_lines(lines=1)
    log_manager.log_action(
        title=title,
        succeeded=result.success,
        message=f"Command: {command}",
        notes={
            "package-name": package_name,
            "package-path": str(target_dir),
        },
    )
    return result.success


def self_uninstall_package(
    target_dir: Path,
    dry_run: bool,
) -> bool:
    package_name = read_package_name(target_dir)
    command = f"uv pip uninstall {package_name}"
    title = "Uninstall package"
    if dry_run:
        log_manager.log_action(
            title=title,
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "package-name": package_name,
                "package-path": str(target_dir),
            },
        )
        return True
    result = run_command(
        command,
        working_directory=target_dir,
        capture_output=False,
        message=f"Uninstalling package: {package_name}",
    )
    log_manager.log_empty_lines(lines=1)
    log_manager.log_action(
        title=title,
        succeeded=result.success,
        message=f"Command: {command}",
        notes={
            "package-name": package_name,
            "package-path": str(target_dir),
        },
    )
    return result.success


def install_package(
    target_dir: Path,
    package_alias: AliasName,
    dry_run: bool,
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> bool:
    package_status = sindri_packages[package_alias]
    package_local_path = package_status.package_path
    if not package_status.is_valid or not package_status.package_name:
        log_manager.log_action(
            title=f"Install `{package_alias}`",
            succeeded=False,
            message=f"Failed. Broken package: {package_status.reason}.",
            notes={
                "package-alias": package_alias,
                "package-path": str(package_local_path),
                "reason": package_status.reason,
            },
        )
        return False
    package_name = package_status.package_name
    command = f'uv pip install -e "{package_local_path}"'
    title = f"Install `{package_name}`"
    if not package_local_path.exists():
        log_manager.log_action(
            title=title,
            succeeded=False,
            message="Failed. Package path does not exist.",
            notes={
                "package-name": package_name,
                "package-path": str(package_local_path),
            },
        )
        return False
    if package_local_path == target_dir.resolve():
        log_manager.log_action(
            title=title,
            succeeded=False,
            message="Failed. Refused to install package into itself.",
            notes={
                "package-name": package_name,
                "package-path": str(package_local_path),
            },
        )
        return False
    if dry_run:
        log_manager.log_action(
            title=title,
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "package-name": package_name,
                "package-path": str(package_local_path),
                "target-package": str(target_dir),
            },
        )
        return True
    result = run_command(
        command,
        working_directory=target_dir,
        capture_output=False,
        message=f"Installing `{package_name}` package",
    )
    log_manager.log_empty_lines(lines=1)
    log_manager.log_action(
        title=title,
        succeeded=result.success,
        message=f"Command: {command}",
        notes={
            "package-name": package_name,
            "package-path": str(package_local_path),
            "target-package": str(target_dir),
        },
    )
    return result.success


def uninstall_package(
    target_dir: Path,
    package_alias: AliasName,
    dry_run: bool,
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> bool:
    package_status = sindri_packages[package_alias]
    package_local_path = package_status.package_path
    if not package_status.is_valid or not package_status.package_name:
        log_manager.log_action(
            title=f"Uninstall `{package_alias}`",
            succeeded=False,
            message="Failed. Broken package (cannot resolve package name).",
            notes={
                "package-alias": package_alias,
                "package-path": str(package_local_path),
                "reason": package_status.reason,
            },
        )
        return False
    package_name = package_status.package_name
    command = f"uv pip uninstall {package_name}"
    title = f"Uninstall `{package_name}`"
    if dry_run:
        log_manager.log_action(
            title=title,
            succeeded=None,
            message=f"[dry-run] Would run: {command}",
            notes={
                "package-name": package_name,
                "target-package": str(target_dir),
            },
        )
        return True
    result = run_command(
        command,
        working_directory=target_dir,
        capture_output=False,
        message=f"Uninstalling `{package_name}` package",
    )
    log_manager.log_empty_lines(lines=1)
    log_manager.log_action(
        title=title,
        succeeded=result.success,
        message=f"Command: {command}",
        notes={
            "package-name": package_name,
            "package-path": str(package_local_path),
            "target-package": str(target_dir),
        },
    )
    return result.success


##
## === CLI ===
##


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install/uninstall local packages into an existing target package (editable installs via uv).",
    )
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Target package directory (must contain pyproject.toml and .venv)",
    )
    parser.add_argument(
        "--self-install",
        action="store_true",
        help="Editable install of the package itself",
    )
    parser.add_argument(
        "--self-uninstall",
        action="store_true",
        help="Uninstall the package editable install",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print commands you can run to check status",
    )
    for package_alias in sorted(SINDRI_PACKAGES):
        package_pretty = SINDRI_PACKAGES[package_alias].name
        parser.add_argument(
            f"--{package_alias}",
            action="store_true",
            help=f"Install package `{package_pretty}`",
        )
        parser.add_argument(
            f"--no-{package_alias}",
            action="store_true",
            help=f"Uninstall package `{package_pretty}`",
        )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without executing",
    )
    return parser.parse_args()


##
## === WORKFLOW ===
##


class LinkPackages:

    def __init__(
        self,
        user_args,
    ):
        self.user_args = user_args
        self.target_dir: Path | None = None
        self.aliases_to_install: list[AliasName] = []
        self.aliases_to_uninstall: list[AliasName] = []
        self.do_self_install: bool = False
        self.do_self_uninstall: bool = False
        self.show_stutus_hint: bool = False
        self.is_dry_run: bool = False
        self.sindri_packages: dict[AliasName, PackageStatus] = {}
        self.action_plan = PlannedSummary()
        self.results = ResultsSummary()

    def _validate_package_root(
        self,
    ) -> Path:
        target_dir = self.user_args.target_dir.resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target package directory does not exist: {target_dir}")
        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            log_manager.log_outcome(
                f"No pyproject.toml found in {target_dir}",
                outcome=log_manager.ActionOutcome.FAILURE,
            )
            sys.exit(1)
        try:
            ensure_package_root(target_dir)
        except Exception as exception:
            log_manager.log_outcome(str(exception), outcome=log_manager.ActionOutcome.FAILURE)
            sys.exit(1)
        return target_dir

    def _collect_actions_from_args(
        self,
    ) -> None:
        self.aliases_to_install = [alias for alias in sorted(SINDRI_PACKAGES) if getattr(self.user_args, alias)]
        self.aliases_to_uninstall = [
            alias for alias in sorted(SINDRI_PACKAGES) if getattr(self.user_args, f"no_{alias}")
        ]
        self.do_self_install = bool(self.user_args.self_install)
        self.do_self_uninstall = bool(self.user_args.self_uninstall)
        self.show_stutus_hint = bool(self.user_args.status)
        self.is_dry_run = bool(self.user_args.dry_run)

    def _verify_and_prepare_plan(
        self,
    ) -> None:
        for alias in self.aliases_to_install:
            status = self.sindri_packages[alias]
            if not status.is_valid:
                self.results.broken_aliases.append((alias, str(status.reason)))
        self.action_plan.install_aliases = list(self.aliases_to_install)
        self.action_plan.uninstall_aliases = list(self.aliases_to_uninstall)
        self.action_plan.alias_to_name = {
            alias: get_package_name(alias, sindri_packages=self.sindri_packages
                                    )
            for alias in sorted(SINDRI_PACKAGES)
        }
        self.action_plan.install_names = get_package_names(
            self.aliases_to_install,
            sindri_packages=self.sindri_packages,
        )
        self.action_plan.uninstall_names = get_package_names(
            self.aliases_to_uninstall,
            sindri_packages=self.sindri_packages,
        )

    def _render_plan_and_confirm(
        self,
        target_dir: Path,
    ) -> None:
        current_state = compute_sindri_install_state(sindri_packages=self.sindri_packages)
        installed_line, missing_line = format_install_state_summary_arrow(
            current_state,
            alias_to_name=self.action_plan.alias_to_name,
        )
        planned_installs = list_or_dash(self.action_plan.install_names)
        planned_uninstalls = list_or_dash(self.action_plan.uninstall_names)
        notes: dict[str, Any] = {
            "target package": str(target_dir),
            "self-install": self.do_self_install,
            "self-uninstall": self.do_self_uninstall,
            "requested installs": planned_installs,
            "requested uninstalls": planned_uninstalls,
            "show sindri status": self.show_stutus_hint,
            "dry-run": self.is_dry_run,
            "already installed packages": installed_line,
            "available packages": missing_line,
        }
        if self.results.broken_aliases:
            broken_aliases = ", ".join(
                f"{arrow_label(alias, get_package_name(alias, sindri_packages=self.sindri_packages))}[{reason}]"
                for alias, reason in self.results.broken_aliases
            )
            self.action_plan.broken_aliases = broken_aliases
            notes["requested broken packages"] = broken_aliases
        else:
            self.action_plan.broken_aliases = "none"
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
        packages_to_reinstall = set(self.aliases_to_uninstall) & set(self.aliases_to_install)
        if packages_to_reinstall:
            list_of_packages = ", ".join(
                sorted(
                    get_package_name(alias, sindri_packages=self.sindri_packages
                                     ) for alias in packages_to_reinstall
                ),
            )
            log_manager.log_hint(
                f"Reinstall will occur for: {list_of_packages} "
                f"(uninstall {log_manager.Symbols.RIGHT_ARROW.value} install)",
                show_time=True,
            )

    def parse_and_verify_args(
        self,
    ) -> None:
        target_dir = self._validate_package_root()
        self.sindri_packages = verify_sindri_packages()
        self._collect_actions_from_args()
        self._verify_and_prepare_plan()
        self._render_plan_and_confirm(target_dir)
        self.target_dir = target_dir

    def apply_requested_actions(
        self,
    ) -> None:
        assert self.target_dir is not None
        for package_alias in self.aliases_to_uninstall:
            successful = uninstall_package(
                self.target_dir,
                package_alias,
                self.is_dry_run,
                sindri_packages=self.sindri_packages,
            )
            self.results.uninstalled_packages.append((package_alias, successful))
        if self.do_self_uninstall:
            self.results.self_uninstall = self_uninstall_package(
                self.target_dir,
                self.is_dry_run,
            )
        if self.do_self_install:
            self.results.self_install = self_install_package(
                self.target_dir,
                self.is_dry_run,
            )
        for package_alias in self.aliases_to_install:
            successful = install_package(
                self.target_dir,
                package_alias,
                self.is_dry_run,
                sindri_packages=self.sindri_packages,
            )
            self.results.installed_packages.append((package_alias, successful))
        if self.show_stutus_hint:
            render_status_hint_block(self.target_dir, sindri_packages=self.sindri_packages)

    def summarise_and_exit(
        self,
    ) -> None:
        successful_installs, failed_installs = split_success_failure(
            self.results.installed_packages,
            alias_to_name=self.action_plan.alias_to_name,
        )
        successful_uninstalls, failed_uninstalls = split_success_failure(
            self.results.uninstalled_packages,
            alias_to_name=self.action_plan.alias_to_name,
        )
        install_package_status = self.results.self_install
        uninstall_package_status = self.results.self_uninstall
        log_manager.log_summary(
            title="Final Summary",
            message="Finished.",
            notes={
                "self-install": format_optional_outcome(install_package_status),
                "self-uninstall": format_optional_outcome(uninstall_package_status),
                "Successfully installed": list_or_dash(successful_installs),
                "Successfully uninstalled": list_or_dash(successful_uninstalls),
                "Failed to install": list_or_dash(failed_installs),
                "Failed to uninstall": list_or_dash(failed_uninstalls),
            },
        )
        status_summary: list[bool] = []
        if install_package_status is not None:
            status_summary.append(bool(install_package_status))
        if uninstall_package_status is not None:
            status_summary.append(bool(uninstall_package_status))
        status_summary.extend(bool(successful) for (_, successful) in self.results.uninstalled_packages)
        status_summary.extend(bool(successful) for (_, successful) in self.results.installed_packages)
        sys.exit(0 if all(status_summary) else 1)

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
    LinkPackages(user_args).run()


if __name__ == "__main__":
    main()

## } SCRIPT
