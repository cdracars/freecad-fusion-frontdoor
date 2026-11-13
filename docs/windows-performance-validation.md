# Windows performance validation

This procedure captures the time from starting the managed FreeCAD process to the Frontdoor workbench showing its task surface. It is opt-in, local-only, and does not send telemetry. No Windows baseline has been captured yet.

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

## Still needed

- Capture the ten-run startup baseline on the existing Windows host before changing launch behavior, then compare under the same host, profile, FreeCAD version, and conditions.
- Add/run a repeatable benchmark for sketch entry, Pad, Pocket, Fillet, and Chamfer with the same part geometry; record action latency, recompute time, and valid-solid results. The current startup logger does not measure these operations.
- Measure interaction responsiveness at the validated Windows display scales and include the baseline and post-change samples in the release handoff.

Do not call Frontdoor optimized until those Windows measurements exist and demonstrate an improvement without weakening the workflow checks.
