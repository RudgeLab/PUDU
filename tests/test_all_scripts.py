import pathlib
import subprocess
import unittest

AUTOMATED_SCRIPTS_DIR = pathlib.Path("scripts/automated_ot2")
LIBRE_SCRIPTS_DIR = pathlib.Path("scripts/libre")
MANUAL_SCRIPTS_DIR = pathlib.Path("scripts/manual")


class TestAllScripts(unittest.TestCase):
    def test_all_scripts_with_simulator(self):
        for scripts_dir in (AUTOMATED_SCRIPTS_DIR, LIBRE_SCRIPTS_DIR):
            self.assertTrue(scripts_dir.exists(), f"Scripts dir not found: {scripts_dir}")
            script_files = sorted(scripts_dir.glob("*.py"), key=lambda p: p.name.lower())

            for script_path in script_files:
                with self.subTest(script=str(script_path)):
                    print(f"\n=== Simulating: {script_path} ===")
                    result = subprocess.run(
                        ["opentrons_simulate", str(script_path)],
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(
                        result.returncode,
                        0,
                        msg=f"Simulation failed for {script_path}:\n{result.stderr}",
                    )


class TestManualScripts(unittest.TestCase):
    def test_manual_scripts_are_excluded_from_simulator(self):
        self.assertTrue(MANUAL_SCRIPTS_DIR.exists(), f"Manual scripts dir not found: {MANUAL_SCRIPTS_DIR}")
        manual_py_files = sorted(MANUAL_SCRIPTS_DIR.glob("*.py"), key=lambda p: p.name.lower())
        self.assertGreater(len(manual_py_files), 0, "No manual scripts were found for manual-specific tests")

    def test_manual_scripts_are_valid_python(self):
        manual_py_files = sorted(MANUAL_SCRIPTS_DIR.glob("*.py"), key=lambda p: p.name.lower())
        for script_path in manual_py_files:
            with self.subTest(script=str(script_path)):
                result = subprocess.run(
                    ["python", "-m", "py_compile", str(script_path)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"Manual script failed syntax check for {script_path}:\n{result.stderr}",
                )


if __name__ == "__main__":
    unittest.main()
