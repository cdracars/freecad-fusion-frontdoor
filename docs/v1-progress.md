# Windows V1 progress and handoff

**Updated:** 2026-11-13  
**Current branch:** `codex/fusion-frontdoor-mockup`
**Publication state:** reviewed source and handoff changes were pushed to the public project branch on 2026-11-13; use the branch HEAD as the current revision.

This record tracks the Windows product path, not only the Frontdoor UI. “Verified” requires evidence on the stated Windows host/build; Linux tests and source inspection do not substitute for Windows behavior.

## V1 acceptance checklist

| Gate | State | Evidence and remaining work |
|---|---|---|
| Windows desktop package and documented prerequisites | Partial | Spec, PowerShell build script, exact-version build inputs, workbench payload archive builder, unsigned ZIP staging, BUILD-INFO and SHA-256 sidecar are implemented locally. Script has not run on Windows; no artifact, clean-machine launch, signing, or reproducibility evidence. |
| Managed FreeCAD install, signature/digest verification, retry, no elevation | Partial | Isolated Windows 11 install of FreeCAD 1.1.4, release digest and Authenticode `Valid` status were recorded in [installation spec](specs/02-installation-and-profiles.md). No-elevation, repair/update, and interaction review are still open. Publisher matching has been hardened locally; run it against the real certificate on Windows after host access returns. |
| Fusion and Full profiles isolated from ordinary FreeCAD | Partial | Windows smoke confirmed the FreeCAD user data path was in the app-owned profile. Full profile launch and before/after comparison against an existing ordinary FreeCAD install have not been demonstrated. |
| Clear setup review and understandable first launch | Partial | Source includes a setup confirmation with release, size, source, install path, both profiles, and add-on revision; expected publisher was just added. A configured Windows profile reached `Design > Solid` without the Welcome surface and passed the first-action state smoke. UI review, retry/error flow, and fresh unconfigured experience remain open. |
| Intended modeling workflow from real user input through saved/reopened result | Open | Linux/FreeCAD 1.1.1 deterministic sketch/Pad/Pocket/Fillet/Chamfer model passed. Windows smoke entered a native XY sketch and used API-generated test geometry; no Windows mouse-drawn constrained sketch, full feature sequence, save, close, and reopen evidence. |
| Fusion mouse navigation and reversible recovery | Open | Pinned add-on staged in prior setup; actual Windows mouse mapping, NaviCube hit targets, restore/reapply persistence, and clean Full FreeCAD recovery are unverified. |
| Reliable operation and repeatable Windows validation | Partial | Fusion launch status now waits for a launch-token marker written after Frontdoor workbench activation and task-surface display. Unit tests cover marker serialization and token isolation; activation-to-marker and UI timeout/handoff behavior remain untested inside FreeCAD/Windows. Individual Windows smoke processes exited and were cleaned up; there is no Windows-owned test lifecycle runner. |
| Performance measured and bottlenecks improved | Open | No actual Windows startup/responsiveness/core-operation baseline exists. Do not describe this project as optimized until measurements and comparison exist. |
| Automated checks and independent review | Partial | Twenty-one local unit tests pass, including publisher spoof rejection, startup marker/token checks, and portable add-on payload resource staging. Independent review confirmed exact CN/O matching against the recorded signer format and identified/fixed a PowerShell condition issue. The Windows package script itself and actual Windows certificate/full user journey still need runtime review/validation. |
| Release candidate, usage guide, and limitations | Open | Portable unsigned ZIP path and preview instructions are documented, but no Windows artifact or checksum exists. No project `LICENSE` file is present; choose and document the project license before public app distribution. Qt/license review, Windows smoke, signed candidate, release notes, and final handoff remain. |

## Current work

- **Highest-risk finding:** `installer._is_expected_publisher` accepted a publisher when the expected company name appeared anywhere in the subject. New regression tests reproduced the spoof and mismatched-CN/O cases. Validation now parses the subject and requires exact matching `CN` and `O`, with case folding and the documented optional leading `The`.
- The setup confirmation now names the expected publisher; installation docs were corrected to reflect the existing confirmation dialog and the exact signer check.
- Local verification after the current changes: 21 unit tests pass with `PYTHONPATH=src`; Python compilation, deterministic workbench payload generation, and `git diff --check` pass. Tests cover the ZIP resource staging fallback with mocked `importlib.resources`; they do not prove behavior in a frozen Windows package. A plain `python3 -m unittest` from the repo root does not include `src/` on `sys.path`, so it fails to import the package unless the project is installed or `PYTHONPATH=src` is set. These checks are not Windows certificate-verification or packaging evidence.
- Fusion launch status now uses a per-launch token passed only to the Fusion profile. The Frontdoor workbench writes an atomic marker after activation and task-surface display; the desktop app waits up to 90 seconds for that exact marker and says only “Frontdoor workbench loaded.” This does not certify every modeling command or the navigation add-on. Full FreeCAD status remains explicitly unconfirmed. Unit tests cover marker validation and token isolation, but this handshake has not yet run inside Windows FreeCAD.
- Independent review found no remaining bypass for the recorded publisher subject format. It also identified that the subject parser is intentionally partial and the actual certificate still needs a post-change Windows run. Follow-up review found the readiness signal is token-isolated and flagged the original status wording as broader than the evidence; the UI/spec wording is now narrowed to workbench load.
- The local packaging scaffold uses Qt's official `pyside6-deploy` in standalone mode, pinned exact versions (Python 3.13.17 x64; PySide6 6.12.0; Nuitka 4.3.4; ordered-set 4.1.0; zstandard 0.25.0), and a generated ZIP resource for the Frontdoor workbench. `scripts/build_windows.ps1` creates an isolated build venv, checks for Visual Studio `dumpbin`, refuses dirty-source builds and unowned output directories, creates an unsigned ZIP with build metadata/notices, and emits a SHA-256 sidecar. Inputs are not yet hash-locked; artifact output, clean-machine start, and included Qt runtime contents remain unverified on Windows. See [packaging research](../research/windows-pyside6-packaging.md).
- The generated `pysidedeploy.spec` is local build state and intentionally excluded from the preview artifact to avoid leaking machine paths. The package notice calls for checking the actual included Qt modules and their license obligations before distribution. This is not a legal determination.
- The repository currently has no root `LICENSE`/`COPYING` file. The Windows review package includes a third-party notice, but its own redistribution terms need to be documented before public distribution; no license has been selected or added.

## Windows host access blocker

The current non-elevated call to the existing Herdr bridge, `hc ls --all`, fails with:

```text
cannot open core lock: Read-only file system (os error 30)
```

No elevation request, bridge restart, or new Windows instance was attempted. The local process list contains no Herdr/FreeCAD process, which does **not** prove that the remote Windows host has no sessions. To continue hands-on validation, the existing Herdr core lock/state must become accessible to the current session without restarting the bridge, or an existing Windows pane/session must be made available through a supported non-elevated read/attach path. First inspect existing sessions before launching anything.

## Next actions

1. Restore access to the existing Windows Herdr pane without restarting/elevating/creating a new instance, install the pinned build toolchain if available, run the package build, and launch the ZIP on the same host.
2. Validate installation/setup, ordinary-profile preservation, both launch modes, mouse-drawn sketch and feature sequence, save/reopen, navigation, rollback, and failure recovery on Windows.
3. Capture Windows startup and core-workflow performance baselines; optimize only measured bottlenecks.
4. Hash-lock the actual Windows wheel set, compare two clean builds, complete the licensing review, and assemble the signed versioned RC with usage steps, prerequisites, checksum, and known limitations. V1 remains active until all acceptance gates pass or a clearly documented external blocker remains.
