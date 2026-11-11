# PyInstaller spec for the macOS and Windows apps (KD-packaging-pyinstaller, architecture
# section 7). Build with packaging/build_macos.sh or packaging/build_windows.ps1, not by
# calling PyInstaller directly.
#
# On Windows this spec builds a plain x64 folder app with no BUNDLE step, which
# packaging/windows-installer.iss then wraps in an installer.

import re
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent  # noqa: F821 (SPECPATH is defined by PyInstaller)
PACKAGE = ROOT / "src" / "patent_intelligence"


def _read(pattern: str, path: Path) -> str:
    return re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE).group(1)


VERSION = _read(r'^__version__ = "([^"]+)"', PACKAGE / "__init__.py")
APP_NAME = _read(r'^APP_NAME = "([^"]+)"', PACKAGE / "settings.py")
BUNDLE_IDENTIFIER = "edu.tcu.cosc40943.team06.patentintelligence"
MINIMUM_MACOS = "15.0"  # OE-desktop-os, OI-17

analysis = Analysis(  # noqa: F821
    [str(PACKAGE / "app.py")],
    pathex=[str(ROOT / "src")],
    # storage/migrate.py finds its scripts next to itself, so they go at the same path.
    datas=[
        (str(PACKAGE / "storage" / "migrations" / "*.sql"), "patent_intelligence/storage/migrations")
    ],
    excludes=["pytest", "ruff", "tkinter", "_tkinter"],
    noarchive=False,
)
pyz = PYZ(analysis.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    console=False,
    target_arch="arm64" if sys.platform == "darwin" else None,
    # PyInstaller ad-hoc signs on macOS when no identity is given: free, and required on
    # Apple silicon. Not notarized (OI-12, RISK-unsigned-app).
    codesign_identity=None,
)
collected = COLLECT(  # noqa: F821
    exe,
    analysis.binaries,
    analysis.datas,
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        collected,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier=BUNDLE_IDENTIFIER,
        version=VERSION,
        info_plist={
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "LSMinimumSystemVersion": MINIMUM_MACOS,
            "LSApplicationCategoryType": "public.app-category.productivity",
            "NSHighResolutionCapable": True,
        },
    )
