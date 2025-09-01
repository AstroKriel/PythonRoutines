## { SCRIPT

##
## === DEPENDENCIES ===
##

import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import Iterable
from jormi.ww_io import shell_manager
from jormi.utils import logging_utils

##
## === GLOBAL PARAMS ===
##

SCRIPT_DIR = Path(__file__).resolve().parent
STYLE_FILE_NAME = ".style.yapf"
STYLE_FILE_PATH = SCRIPT_DIR / STYLE_FILE_NAME
FILES_TO_IGNORE = set()
DIRS_TO_IGNORE = (
    ".DS_Store",
    "__pycache__",
    ".venv",
    ".git",
    "build",
    "dist",
    ".eggs",
)

##
## === LOGGING HELPERS ===
##


def log_info(text: str) -> None:
    logging_utils.render_line(
        logging_utils.Message(text, message_type=logging_utils.MessageType.GENERAL),
        show_time=True,
    )


def log_action(text: str, *, outcome: logging_utils.ActionOutcome) -> None:
    logging_utils.render_line(
        logging_utils.Message(
            text,
            message_type=logging_utils.MessageType.ACTION,
            action_outcome=outcome,
        ),
        show_time=True,
    )


##
## === HELPER FUNCTIONS ===
##


def ensure_styling_rules_exist() -> None:
    if not STYLE_FILE_PATH.exists():
        log_action(
            f"Styling file `{STYLE_FILE_NAME}` was not found next to the script: {STYLE_FILE_PATH}",
            outcome=logging_utils.ActionOutcome.FAILURE,
        )
        sys.exit(1)


def ensure_uv_is_available() -> None:
    if shutil.which("uv") is None:
        log_action(
            "`uv` not found in PATH. Install uv first.",
            outcome=logging_utils.ActionOutcome.FAILURE,
        )
        sys.exit(1)
    log_action("Found `uv`", outcome=logging_utils.ActionOutcome.SUCCESS)


def _should_ignore_dirname(dir_name: str) -> bool:
    return dir_name in DIRS_TO_IGNORE


def _should_ignore_file(path: Path) -> bool:
    if path.name in FILES_TO_IGNORE:
        return True
    if path.suffix.lower() != ".py":
        return True
    if any(path_part in DIRS_TO_IGNORE for path_part in path.parts):
        return True
    return False


def collect_py_files(targets: Iterable[Path]) -> list[Path]:
    file_paths: list[Path] = []
    for path in targets:
        if not path.exists():
            continue
        if path.is_file():
            if not _should_ignore_file(path):
                file_paths.append(path)
            continue
        for dir_path, dir_names, file_names in os.walk(path, topdown=True):
            ## prune directories in-place so os.walk does not descend into them
            dir_names[:] = [
                dir_name for dir_name in dir_names if not _should_ignore_dirname(dir_name)
            ]
            for filename in file_names:
                full_path = Path(dir_path) / filename
                if _should_ignore_file(full_path):
                    continue
                file_paths.append(full_path)
    file_paths.sort()
    return file_paths


def apply_trailing_commas(file_paths: list[Path]) -> None:
    if not file_paths:
        log_info("No Python files to update for trailing commas")
        return
    log_info(f"Adding trailing commas where safe ({len(file_paths)} files)")
    for file_path in file_paths:
        shell_manager.execute_shell_command(
            f'uvx --from add-trailing-comma add-trailing-comma --exit-zero-even-if-changed "{file_path}"',
            timeout_seconds=120,
            show_output=True,
        )
    log_action("Completed trailing-commas pass", outcome=logging_utils.ActionOutcome.SUCCESS)


def apply_yapf_style(file_paths: list[Path]) -> None:
    if not file_paths:
        log_info("No files for YAPF")
        return
    if not STYLE_FILE_PATH.exists():
        log_action(
            f"Style file `{STYLE_FILE_NAME}` was not found next to the script: {STYLE_FILE_PATH}",
            outcome=logging_utils.ActionOutcome.FAILURE,
        )
        sys.exit(1)
    log_info(f"Running YAPF-styling on {len(file_paths)} file(s)")
    for file_path in file_paths:
        shell_manager.execute_shell_command(
            f'uvx --from yapf yapf -i --verbose --style "{STYLE_FILE_PATH}" "{file_path}"',
            timeout_seconds=300,
            show_output=True,
        )
    log_action("Completed YAPF formatting", outcome=logging_utils.ActionOutcome.SUCCESS)


##
## === MAIN ROUTINE ===
##


def format_project(targets: list[str] | None = None) -> int:
    log_info("Formatting with jormi's YAPF profile")
    ensure_styling_rules_exist()
    ensure_uv_is_available()
    log_info(f"Using style rules from: {STYLE_FILE_PATH}")
    if not targets:
        resolved_targets = [Path.cwd()]
    else:
        resolved_targets = [Path(target).resolve() for target in targets]
    log_info("Scanning target roots: " + ", ".join(map(str, resolved_targets)))
    file_paths = collect_py_files(resolved_targets)
    log_info(f"Discovered {len(file_paths)} Python files across {len(resolved_targets)} target(s)")
    if not file_paths:
        log_info("No Python files were found under: " + ", ".join(map(str, resolved_targets)))
        log_action("Nothing to do", outcome=logging_utils.ActionOutcome.SKIPPED)
        return 0
    apply_trailing_commas(file_paths)
    apply_yapf_style(file_paths)
    log_action("Formatting finished", outcome=logging_utils.ActionOutcome.SUCCESS)
    return 0


##
## === USER INTERFACE ===
##


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply trailing-commas rule and YAPF styling to selected targets.",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help=(
            "Folders or files to format. "
            "If none are provided, the current working directory is scanned and formatted. "
            "If provided, targets are resolved relative to your current working directory; "
            "absolute paths are also accepted."
        ),
    )
    args = parser.parse_args(argv if (argv is not None) else sys.argv[1:])
    return format_project(args.targets)


##
## === ENTRY POINT ===
##

if __name__ == "__main__":
    raise SystemExit(main())

## } SCRIPT
