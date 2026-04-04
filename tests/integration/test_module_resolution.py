from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_package_is_importable_from_repository_root_without_pythonpath() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    result = subprocess.run(
        [sys.executable, "-c", "import omnichannel_platform; print(omnichannel_platform.__path__)"],
        cwd=repository_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "src/omnichannel_platform" in result.stdout
