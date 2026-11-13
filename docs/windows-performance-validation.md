# Windows performance validation

This procedure captures an estimate from the launch request immediately before `Popen` to the Frontdoor task-surface `show()`/`raise_()` calls during workbench activation. It does not measure exact OS process creation, Qt painting, or interactive responsiveness. It is opt-in, local-only, and does not send telemetry. No Windows baseline has been captured yet.

## Capture startup readiness

1. Extract the unsigned preview ZIP and complete setup once in its isolated profile.
2. Open PowerShell in the extracted folder. Set a log path and run the app:

   ```powershell
   $env:FRONTDOOR_PERF_LOG = Join-Path $PWD "frontdoor-startup.jsonl"
   $app = Get-ChildItem -Path $PWD -Recurse -File -Filter frontdoor_entry.exe | Select-Object -First 1
   if (-not $app) { throw "frontdoor_entry.exe was not found" }
   & $app.FullName
   ```

3. Click **Launch Fusion**. When the Frontdoor workbench confirms readiness, the app appends one JSON record to `frontdoor-startup.jsonl`. Close the FreeCAD window before the next sample. Repeat ten launches; retain the JSONL file with the host and build identity.
4. Compute median and 95th percentile from `duration_ms`. These samples measure process start through in-process workbench/task-surface readiness, not the separate Frontdoor desktop launchpad or FreeCAD download/setup. Record Windows build, CPU, RAM, FreeCAD version, display scale, Frontdoor commit, and whether the operating-system file cache was warm.

The logger is inactive unless `FRONTDOOR_PERF_LOG` is explicitly set. The status message and normal launch behavior do not change when it is enabled. Python's `perf_counter_ns` is used across the Frontdoor and FreeCAD processes; Python documents the performance counter as shared across processes on Windows. [Python time documentation](https://docs.python.org/3.13/library/time.html)

## Capture core-operation samples

1. In the existing Windows FreeCAD 1.1.4 Fusion profile, open FreeCAD's Python console and set `FRONTDOOR_CORE_PERF_LOG` in that running process, replacing the example path:

   ```python
   import os
   os.environ["FRONTDOOR_CORE_PERF_LOG"] = r"C:\Users\you\Documents\frontdoor-core.jsonl"
   ```

2. Run [`tests/frontdoor_core_performance.FCMacro`](../tests/frontdoor_core_performance.FCMacro) from **Macro → Macros → Execute**. Repeat ten times in the same FreeCAD process and profile. Each run creates and closes only its own temporary document.
3. Keep the benchmark file, FreeCAD version, Windows build, CPU, RAM, Frontdoor commit, and display scale with the startup samples. Compare median and 95th percentile for `model_update_ms` and `recompute_ms` per operation.

The macro constructs the same 20 × 20 × 10 mm Pad and 10 × 10 × 5 mm Pocket used by the workflow spec, with the Pocket sketch attached to the Pad's top face, then applies 1 mm Fillet and Chamfer branches. It verifies expected Pad/Pocket volumes, the stored 1 mm dress-up parameters, and a single valid solid after each operation. It uses FreeCAD's native [Pad](https://freecad.github.io/API/d9/d14/classPartDesign_1_1Pad.html) `Length`, [Fillet](https://freecad.github.io/SourceDoc/d0/d50/classPartDesign_1_1Fillet.html) `Radius`, and [Chamfer](https://freecad.github.io/SourceDoc/da/d6f/classPartDesign_1_1Chamfer.html) `Size` properties. These samples measure feature setup and FreeCAD model recompute, not button-to-result latency or interactive sketching. It has not yet been run on Windows.

Only include a JSONL row in timing summaries when `completed` is `true`, `failures` is empty, and all required operation records (`pad`, `pocket`, `fillet`, `chamfer`) are present and valid. Partial or failed runs are diagnostic only.

## Still needed

- Capture the ten-run startup baseline on the existing Windows host before changing launch behavior, then compare under the same host, profile, FreeCAD version, and conditions.
- Measure button-to-result latency for the representative UI workflow and interaction responsiveness at the validated Windows display scales; the core macro measures data-model update/recompute only.
- Compare baseline and post-change samples under matching Windows host, FreeCAD build, geometry, profile, and cache conditions, and include them in the release handoff.

Do not call Frontdoor optimized until those Windows measurements exist and demonstrate an improvement without weakening the workflow checks.
