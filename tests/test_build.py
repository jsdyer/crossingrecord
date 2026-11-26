import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from html import unescape
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build import ROOT, build, metadata
from junction_profiles import paired_years
from source_io import previous_project_years


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "web", self.root / "web")
        shutil.copyfile(ROOT / "tool.json", self.root / "tool.json")
        shutil.copyfile(ROOT / "README.md", self.root / "README.md")

    def edit(self, **changes):
        tool = json.loads((self.root / "tool.json").read_text())
        tool.update(changes)
        (self.root / "tool.json").write_text(json.dumps(tool))

    def test_build_is_scoped_to_web_and_escapes_metadata(self):
        (self.root / "private.txt").write_text("must not publish")
        self.edit(title='<img src=x onerror="bad()">')
        build(self.root)
        page = (self.root / "dist/index.html").read_text()
        self.assertIn('&lt;img', page)
        self.assertNotIn('<img', page)
        self.assertNotIn('{{', page)
        self.assertIn('href="./style.css"', page)
        self.assertFalse((self.root / "dist/private.txt").exists())
        self.assertTrue((self.root / "dist/.nojekyll").exists())

    def test_paired_years_require_complete_adjacent_years_on_both_sides(self):
        self.assertEqual(paired_years([2022, 2023, 2024, 2025, 2026], 2024, "2026-09-15"), [2023, 2025])
        self.assertEqual(paired_years([2021, 2023, 2024, 2025, 2026], 2024, "2027-01-01"), [2023, 2025])
        self.assertEqual(paired_years([2023, 2024], 2024, "2026-09-15"), [])
        self.assertEqual(paired_years([2022, 2023, 2024, 2025, 2026], 2024, "2027-01-01"), [2022, 2023, 2025, 2026])

    def test_project_observations_roll_forward_without_overwriting_revisions(self):
        old = {"source": "workbook", "projects": {"A": {"year": 2023}}, "years": [2021, 2022, 2023],
               "sites": {"A": [[0, 0], [4, 2], [8, 3]]}, "retrieved": "2023-11-01"}
        new = {"source": "workbook", "projects": old["projects"], "years": [2022, 2024]}
        self.assertEqual(previous_project_years(old, new), {"A": {"2021": {"counts": [0, 0], "retrieved": "2023-11-01"}}})
        self.assertEqual(previous_project_years(old, {**new, "source": "different"}), {})

    def test_directory_profiles_and_interactive_comparisons_share_exact_source_data(self):
        build(self.root)
        site = self.root / "dist"
        data = json.loads((site / "data/edition.json").read_text())
        urls = {n.text for n in ET.parse(site / "sitemap.xml").findall(".//{*}loc")}
        base = "https://coolcode.ca/crossingrecord/"
        directory = (site / "junctions/index.html").read_text()
        self.assertIn(base + "junctions/", urls)
        self.assertIn('href="./junctions/"', (site / "index.html").read_text())
        self.assertEqual(len(urls), 1 + len(data["projectProfiles"]))
        self.assertLessEqual(set(data["projectProfiles"]), set(data["projects"]))
        for label, profile in data["projectProfiles"].items():
            path = profile["path"]
            page = unescape((site / path / "index.html").read_text())
            self.assertIn(f'rel="canonical" href="{base + path}"', page)
            self.assertIn(base + path, urls)
            self.assertIn(path.removeprefix("junctions/"), directory)
            self.assertIn(label, page)
            self.assertIn(data["projects"][label]["url"], page)
            self.assertIn(data["source"], page)
            self.assertIn(urlencode({"junction": label, "year": profile["year"], "window": "matched"}), page)
            for year, (total, casualty) in zip(data["years"], data["sites"][label]):
                self.assertIn(f'<th scope="row">{year}</th><td>{total}</td><td>{casualty}</td>', page)
            self.assertNotIn(profile["year"], profile["pairedYears"])

    def test_url_matches_tool_id(self):
        self.edit(url="/different/")
        with self.assertRaises(ValueError): metadata(self.root)

    def test_requires_a_source_sentence_and_a_guide_note(self):
        (self.root / "README.md").write_text("# A tool")
        with self.assertRaisesRegex(ValueError, "README note"):
            metadata(self.root)
        self.edit(data_info={"mode": "local", "detail": ""})
        with self.assertRaisesRegex(ValueError, "homepage card"):
            metadata(self.root)

    def test_browser_access_is_explicit(self):
        self.edit(access="install")
        with self.assertRaisesRegex(ValueError, "immediately usable"):
            metadata(self.root)

    def test_failed_build_keeps_existing_output(self):
        build(self.root)
        existing = (self.root / "dist/index.html").read_bytes()
        self.edit(source="javascript:bad()")
        with self.assertRaises(ValueError): build(self.root)
        self.assertEqual((self.root / "dist/index.html").read_bytes(), existing)


if __name__ == "__main__": unittest.main()
