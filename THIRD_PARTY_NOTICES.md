# Third-party components

The Frontdoor project's own code is licensed under the MIT License; see [`LICENSE`](LICENSE). The bundled components below retain their own licenses and notices.

## freecad-fusion add-on

- Project: <https://github.com/arxdsilva/freecad-fusion>
- Pinned source commit: `332ba07bdcaca194e5a3010d1fc0a365eeaefcf1`
- License: MIT
- The frontdoor downloads this component from the pinned GitHub archive and places it only in its managed Fusion profile. It is not bundled into this repository.
- The add-on's author describes Windows support, but the pinned repository README reports testing on FreeCAD 1.1 for macOS only. Windows behavior remains unverified until tested on Windows.

## PySide6 / Qt

- Project: <https://doc.qt.io/qtforpython-6/>
- The Windows preview build bundles PySide6 and the Qt libraries/plugins selected by `pyside6-deploy`.
- Qt for Python is offered under LGPLv3/GPLv3 or a commercial license. The exact license texts, notices, source-offer obligations, and the libraries actually included in a packaged build must be reviewed against the chosen distribution model before release. This notice is not a determination of compliance.

## Nuitka build tool

- Project: <https://nuitka.net/>
- Nuitka is used only to build the standalone app; it is not intentionally copied into the runtime ZIP.
- Nuitka's documentation describes its compiler as AGPLv3 with a Runtime exception for generated binaries. Confirm the applicable license and notices for the exact version and distribution before release; this notice is not a legal determination.
