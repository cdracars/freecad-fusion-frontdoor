"""Stable main-module entry point for the frozen Frontdoor desktop app."""

from frontdoor.app import main


if __name__ == "__main__":
    raise SystemExit(main())
