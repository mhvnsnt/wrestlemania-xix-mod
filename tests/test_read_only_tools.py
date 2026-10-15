from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


class ReadOnlyToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "sample"
        self.root.mkdir()
        (self.root / "sample.bin").write_bytes(b"YDSP\x00\x01test")
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "note.txt").write_text("hello", encoding="utf-8")
        self.originals = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }

    def run_tool(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOLS / script), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_sources_unchanged(self) -> None:
        current = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        self.assertEqual(current, self.originals)

    def test_inventory_csv(self) -> None:
        output = Path(self.temp.name) / "inventory.csv"
        result = self.run_tool(
            "inventory_files.py", str(self.root), "--format", "csv", "--output", str(output)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with output.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["relative_path"] for row in rows}, {"sample.bin", "nested/note.txt"})
        self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))
        self.assert_sources_unchanged()

    def test_inventory_json(self) -> None:
        output = Path(self.temp.name) / "inventory.json"
        result = self.run_tool(
            "inventory_files.py", str(self.root), "--format", "json", "--output", str(output)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"relative_path": "sample.bin"', output.read_text(encoding="utf-8"))
        self.assert_sources_unchanged()

    def test_signature_inspector(self) -> None:
        result = self.run_tool("inspect_signatures.py", str(self.root), "--bytes", "4")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("59 44 53 50", result.stdout)
        self.assertIn("YDSP", result.stdout)
        self.assert_sources_unchanged()

    def test_invalid_root_fails(self) -> None:
        result = self.run_tool("inspect_signatures.py", str(self.root / "missing"))
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
