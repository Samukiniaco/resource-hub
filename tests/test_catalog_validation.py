import unittest
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.catalog import validate_catalog, CatalogValidationError

def base_catalog():
    return {
        "schema_version": 1,
        "app": {"catalog_version": "1.0.0", "changelog": "init"},
        "minecraft": {"versions": [{"id": "1.8.9", "name": "MC 1.8.9", "description": "", "banner": "", "link": "https://example.com", "warning": ""}]},
        "libraries": {"name": "libs", "link": "https://example.com/libs"},
        "java": [{"version": "21", "name": "Java 21", "link": "https://example.com/java"}],
        "launcher": {},
        "other": []
    }

class TestCatalogValidation(unittest.TestCase):
    def test_valid(self):
        cat = validate_catalog(base_catalog())
        self.assertEqual(cat.catalog_version, "1.0.0")
        self.assertEqual(len(cat.minecraft_versions), 1)

    def test_invalid_schema_version(self):
        d = base_catalog()
        d["schema_version"] = 2
        with self.assertRaises(CatalogValidationError):
            validate_catalog(d)

    def test_missing_minecraft_name(self):
        d = base_catalog()
        d["minecraft"]["versions"][0].pop("name")
        with self.assertRaises(CatalogValidationError):
            validate_catalog(d)

    def test_invalid_link_rejected(self):
        d = base_catalog()
        d["minecraft"]["versions"][0]["link"] = "javascript:alert(1)"
        with self.assertRaises(CatalogValidationError):
            validate_catalog(d)

    def test_invalid_banner_graceful(self):
        d = base_catalog()
        d["minecraft"]["versions"][0]["banner"] = "not-a-url"
        cat = validate_catalog(d)
        self.assertEqual(cat.minecraft_versions[0].banner, "")

    def test_empty_optional_fields(self):
        d = base_catalog()
        d["minecraft"]["versions"] = [{"id": "1.20", "name": "MC 1.20"}]
        d["java"] = []
        d["other"] = []
        cat = validate_catalog(d)
        self.assertEqual(cat.minecraft_versions[0].link, "")

    def test_libraries_invalid_link(self):
        d = base_catalog()
        d["libraries"] = {"name": "libs", "link": "ftp://bad"}
        with self.assertRaises(CatalogValidationError):
            validate_catalog(d)

    def test_other_missing_name(self):
        d = base_catalog()
        d["other"] = [{"description": "no name"}]
        with self.assertRaises(CatalogValidationError):
            validate_catalog(d)

if __name__ == "__main__":
    unittest.main()
