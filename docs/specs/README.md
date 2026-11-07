# Frontdoor specification pack

This directory turns the decisions and requirements accumulated during development into linked, reviewable specifications. It describes the Windows-first product target while recording the Linux FreeCAD 1.1.1 evidence available today.

## Start here

- [Product goals and scope](01-product-and-scope.md)
- [Windows installation and profile isolation](02-installation-and-profiles.md)
- [Frontdoor workspace and first-run experience](03-frontdoor-experience.md)
- [Modular setup architecture](04-experience-architecture.md)
- [Solid modeling workflow](05-solid-workflow.md)
- [Theme and navigation](06-theme-and-navigation.md)
- [Acceptance, validation, and open questions](07-acceptance-and-validation.md)

## Existing project documents

- [`PRODUCT.md`](../../PRODUCT.md) is the short product snapshot.
- [`SPEC.md`](../../SPEC.md) is the integrated MVP requirement and current implementation record.
- [`MOCKUP_SPEC.md`](../../MOCKUP_SPEC.md) governs the visual-only HTML mockup.
- [`research/freecad-theme-fusion-comparison.md`](../../research/freecad-theme-fusion-comparison.md) contains the source-backed comparison that informed the theme, ribbon, and workbench decisions.
- [`README.md`](../../README.md) contains developer and smoke-run instructions.

## How to read status

Each requirement uses one of these states:

- **Decision** — product direction accepted during this work; implementation may still be incomplete.
- **Implemented** — code exists, but the behavior is not necessarily verified on every target.
- **Verified** — the stated behavior passed the specific local run described in the validation spec.
- **Open** — needs a product decision, evidence, or both.
- **Deferred** — intentionally outside the first release slice.

`SPEC.md` remains the integration-level source for MVP acceptance. The documents here add detail by topic; they do not imply that every requirement is implemented. If documents disagree, update the topic spec and `SPEC.md` together, and keep the validation status tied to evidence.

## Accepted product direction

- Help Autodesk Fusion users reach useful FreeCAD modeling quickly; build a **Fusion-friendly** setup, not a clone or Autodesk product.
- Lead with a small Frontdoor-owned task interface. Do not confront a new user with FreeCAD's full installed workbench list.
- Use FreeCAD's native modeling commands and data model. Keep specialized workbenches available through **Full FreeCAD**.
- Keep all Frontdoor-managed files and settings in app-owned locations. Never alter the user's ordinary FreeCAD installation or profile.
- Prefer existing extensions where they fill a verified need; do not make an add-on the UI foundation when it cannot provide the required task navigation.
- The prototype HTML is visual-only. The product implementation is Python/PySide6 plus an in-process FreeCAD workbench.

