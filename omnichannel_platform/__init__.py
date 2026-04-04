"""Development shim for running the src-layout package from the repository root."""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

src_package_path = Path(__file__).resolve().parent.parent / "src" / __name__
if src_package_path.exists():
    __path__.append(str(src_package_path))
