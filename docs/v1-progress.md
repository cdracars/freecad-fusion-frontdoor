# Windows V1 progress and handoff

**Updated:** 2026-11-13  
**Current branch:** `codex/fusion-frontdoor-mockup`  
**Current pushed revision at handoff:** `ac0456b` (local changes are in progress; update this field after the next push)

This record tracks the Windows product path, not only the Frontdoor UI. “Verified” requires evidence on the stated Windows host/build; Linux tests and source inspection do not substitute for Windows behavior.

## V1 acceptance checklist

| Gate | State | Evidence and remaining work |
|---|---|---|
| Reproducible Windows app install and documented prerequisites | Open | Source app uses Python 3.12+ and PySide6; no reproducible packaged Windows release candidate or signing evidence. README contains developer setup steps. |
| Managed FreeCAD install, signature/digest verification, retry, no elevation | Partial | Isolated Windows 11 install of FreeCAD 1.1.4, release digest and Authenticode `Valid` status were recorded in [installation spec](specs/02-installation-and-profiles.md). No-elevation, repair/update, and interaction review are still open. Publisher matching has been hardened locally; run it against the real certificate on Windows after host access returns. |
| Fusion and Full profiles isolated from ordinary FreeCAD | Partial | Windows smoke confirmed the FreeCAD user data path was in the app-owned profile. Full profile launch and before/after comparison against an existing ordinary FreeCAD install have not been demonstrated. |
| Clear setup review and understandable first launch | Partial | Source includes a setup confirmation with release, size, source, install path, both profiles, and add-on revision; expected publisher was just added. A configured Windows profile reached `Design > Solid` without the Welcome surface and passed the first-action state smoke. UI review, retry/error flow, and fresh unconfigured experience remain open. |
| Intended modeling workflow from real user input through saved/reopened result | Open | Linux/FreeCAD 1.1.1 deterministic sketch/Pad/Pocket/Fillet/Chamfer model passed. Windows smoke entered a native XY sketch and used API-generated test geometry; no Windows mouse-drawn constrained sketch, full feature sequence, save, close, and reopen evidence. |
| Fusion mouse navigation and reversible recovery | Open | Pinned add-on staged in prior setup; actual Windows mouse mapping, NaviCube hit targets, restore/reapply persistence, and clean Full FreeCAD recovery are unverified. |
| Reliable operation and repeatable Windows validation | Partial | Individual Windows FreeCAD smoke processes exited and were cleaned up. There is no Windows-owned test lifecycle runner. Startup readiness is inferred from child-process status and needs an in-FreeCAD handshake. |
| Performance measured and bottlenecks improved | Open | No actual Windows startup/responsiveness/core-operation baseline exists. Do not describe this project as optimized until measurements and comparison exist. |
| Automated checks and independent review | Partial | Five installer publisher tests pass after the current hardening. Independent read-only review of `9144337...HEAD` found the substring publisher vulnerability; fix is underway and needs a review of the resulting change. Full release-candidate journey review remains open. |
| Reproducible release candidate, usage guide, and limitations | Open | No built Windows artifact, checksum/signature, versioned release notes, or final usage/limitations handoff. |

## Current work

- **Highest-risk finding:** `installer._is_expected_publisher` accepted a publisher when the expected company name appeared anywhere in the subject. New regression tests reproduced the spoof and mismatched-CN/O cases. Validation now parses the subject and requires exact matching `CN` and `O`, with case folding and the documented optional leading `The`.
- The setup confirmation now names the expected publisher; installation docs were corrected to reflect the existing confirmation dialog and the exact signer check.
- Local verification after the current changes: 16 unit tests pass with `PYTHONPATH=src`; Python compilation and `git diff --check` pass. A plain `python3 -m unittest` from the repo root does not include `src/` on `sys.path`, so it fails to import the package unless the project is installed or `PYTHONPATH=src` is set. These checks are not Windows certificate-verification evidence.
- Fusion launch readiness now uses a per-launch token passed only to the Fusion profile. The Frontdoor workbench writes an atomic marker after activation and task-surface display; the desktop app waits up to 90 seconds for that exact marker. Full FreeCAD status remains explicitly unconfirmed. Unit tests cover marker validation and token isolation, but this handshake has not yet run inside Windows FreeCAD.
- Independent review found no remaining bypass for the recorded publisher subject format. It also identified that the subject parser is intentionally partial and the actual certificate still needs a post-change Windows run. A reviewer is checking the latest readiness-handshake diff now.

## Windows host access blocker

The current non-elevated call to the existing Herdr bridge, `hc ls --all`, fails with:

```text
cannot open core lock: Read-only file system (os error 30)
```

No elevation request, bridge restart, or new Windows instance was attempted. The local process list contains no Herdr/FreeCAD process, which does **not** prove that the remote Windows host has no sessions. To continue hands-on validation, the existing Herdr core lock/state must become accessible to the current session without restarting the bridge, or an existing Windows pane/session must be made available through a supported non-elevated read/attach path. First inspect existing sessions before launching anything.

## Next actions

1. Review and commit the current local diff; push only after the user approves publication.
2. Restore access to the existing Windows Herdr pane without restarting/elevating/creating a new instance, then verify the hardened publisher check against the real certificate and exercise the readiness marker in FreeCAD 1.1.4.
3. Validate installation/setup, ordinary-profile preservation, both launch modes, mouse-drawn sketch and feature sequence, save/reopen, navigation, rollback, and failure recovery on Windows.
4. Build a reproducible Windows app artifact, capture startup and core-workflow performance baselines, and optimize only measured bottlenecks.
5. Assemble and review a versioned release candidate with usage steps, prerequisites, checksums, and known limitations. V1 remains active until all acceptance gates pass or a clearly documented external blocker remains.
