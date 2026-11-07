from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .errors import FrontdoorError
from .launcher import launch_freecad
from .setup import setup_existing_freecad


def _progress(message: str, percentage: int) -> None:
    marker = f"{percentage:3d}%" if percentage else " ..."
    print(f"[{marker}] {message}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="frontdoor-setup",
        description="Set up isolated Fusion-style profiles around an existing FreeCAD executable.",
    )
    parser.add_argument("--freecad", required=True, type=Path, help="Path to the existing FreeCAD executable")
    parser.add_argument(
        "--mode",
        choices=("fusion", "full", "both"),
        default="fusion",
        help="Profile(s) to prepare; Fusion mode downloads the pinned community add-on",
    )
    parser.add_argument(
        "--launch",
        choices=("fusion", "full"),
        help="Launch the selected profile after setup finishes",
    )
    parser.add_argument(
        "--freecad-arg",
        action="append",
        default=[],
        help="Argument passed through to FreeCAD; repeat for multiple arguments",
    )
    args = parser.parse_args(argv)
    profiles = ("fusion", "full") if args.mode == "both" else (args.mode,)
    if args.launch and args.launch not in profiles:
        parser.error(f"--launch {args.launch} requires --mode {args.launch} or --mode both")
    try:
        result = setup_existing_freecad(args.freecad, profiles=profiles, progress=_progress)
        print(f"FreeCAD executable: {result.executable}")
        if result.fusion_profile:
            print(f"Fusion profile: {result.fusion_profile}")
        if result.full_profile:
            print(f"Full FreeCAD profile: {result.full_profile}")
        if args.launch:
            process = launch_freecad(result.executable, args.launch, tuple(args.freecad_arg))
            for _ in range(6):
                if process.poll() is not None:
                    break
                time.sleep(0.5)
            exit_code = process.poll()
            if exit_code not in (None, 0):
                raise FrontdoorError(
                    f"FreeCAD exited immediately with status {exit_code}; startup and add-on loading were not verified."
                )
            if exit_code == 0:
                print(f"FreeCAD exited with status 0; check its window for profile: {args.launch}.")
                print("The CLI cannot confirm that the add-on loaded.")
            else:
                print(f"FreeCAD is still running with profile: {args.launch}.")
                print("The CLI cannot confirm that the add-on loaded.")
    except (FrontdoorError, OSError, ValueError) as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
