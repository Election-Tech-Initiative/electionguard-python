import subprocess
import sys

from tests.base_test_case import BaseTestCase


class TestGuiImportWarnings(BaseTestCase):
    """Importing the GUI must not raise deprecation warnings from its web bridge."""

    def test_import_gui_without_deprecation_warnings(self):
        # A fresh interpreter, because a module that is already imported
        # does not warn again, and pytest's own warning filters do not apply.
        result = subprocess.run(
            [
                sys.executable,
                "-W",
                "error::DeprecationWarning",
                "-c",
                "import electionguard_gui",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
