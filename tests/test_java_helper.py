import unittest
import tempfile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.java_helper import find_java_exes, update_java_path

class TestJavaHelper(unittest.TestCase):
    def test_find_single(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "jdk" / "bin").mkdir(parents=True)
            exe = root / "jdk" / "bin" / "java.exe"
            exe.write_text("fake")
            found = find_java_exes(root)
            self.assertEqual(len(found), 1)
            self.assertTrue(str(found[0]).endswith("java.exe"))

    def test_find_multiple(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a" / "bin").mkdir(parents=True)
            (root / "b" / "bin").mkdir(parents=True)
            (root / "a" / "bin" / "java.exe").write_text("a")
            (root / "b" / "bin" / "java.exe").write_text("b")
            found = find_java_exes(root)
            self.assertEqual(len(found), 2)

    def test_find_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = find_java_exes(Path(tmp))
            self.assertEqual(found, [])

    def test_update_preserves_other_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            conf = Path(tmp) / "vortex_launcher.conf"
            conf.write_text("# comment\nJavaPath = C:\\old\\java.exe\nOther=123\n", encoding="utf-8")
            new_java = Path(tmp) / "java.exe"
            new_java.write_text("fake")
            ok, msg = update_java_path(conf, new_java)
            self.assertTrue(ok)
            content = conf.read_text(encoding="utf-8")
            self.assertIn(str(new_java), content)
            self.assertIn("# comment", content)
            self.assertIn("Other=123", content)

    def test_update_missing_javapath(self):
        with tempfile.TemporaryDirectory() as tmp:
            conf = Path(tmp) / "vortex_launcher.conf"
            conf.write_text("Other=123\n", encoding="utf-8")
            new_java = Path(tmp) / "java.exe"
            new_java.write_text("fake")
            ok, msg = update_java_path(conf, new_java)
            self.assertFalse(ok)

    def test_update_missing_conf(self):
        with tempfile.TemporaryDirectory() as tmp:
            conf = Path(tmp) / "nonexistent.conf"
            new_java = Path(tmp) / "java.exe"
            new_java.write_text("fake")
            ok, _ = update_java_path(conf, new_java)
            self.assertFalse(ok)

if __name__ == "__main__":
    unittest.main()
