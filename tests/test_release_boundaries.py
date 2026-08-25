from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseBoundaryTests(unittest.TestCase):
    def test_release_builder_excludes_local_artifacts_and_generated_npm_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "release.zip"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_release.py"), "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with ZipFile(output) as archive:
                names = archive.namelist()
            for forbidden in (
                "/.tools/",
                "/.learning/",
                "/make-skills-plans/",
                "/make-skills-reviews/",
                "/make-skills-change-plans/",
                "/npm/python/",
            ):
                self.assertFalse(any(forbidden in name for name in names), forbidden)

    def test_installer_ignores_local_artifact_directories(self) -> None:
        installer = load_script("make_skills_install", ROOT / "scripts/install.py")
        ignored = installer.IGNORED(
            str(ROOT),
            ["SKILL.md", "make-skills-reviews", "make-skills-plans", "make-skills-change-plans", ".learning"],
        )
        self.assertEqual(
            ignored,
            {"make-skills-reviews", "make-skills-plans", "make-skills-change-plans", ".learning"},
        )


if __name__ == "__main__":
    unittest.main()
