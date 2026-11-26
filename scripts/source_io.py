"""Fetch publisher resources and replace a complete, validated edition atomically."""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / "web/data/edition.json"


def fetch(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (CoolCode public data refresh)"})
    with urlopen(request, timeout=100) as response:
        return response.read()


def previous_project_years(previous, edition):
    """Keep complete project-year observations only when they leave the rolling workbook."""
    if previous.get("source") != edition["source"]:
        return {}
    archived = {}
    active_years = set(edition["years"])
    for label, project in edition["projects"].items():
        if previous.get("projects", {}).get(label, {}).get("year") != project["year"]:
            continue
        old = {year: entry for year, entry in previous.get("projectArchive", {}).get(label, {}).items()
               if int(year) not in active_years}
        for year, counts in zip(previous["years"], previous["sites"].get(label, [])):
            if year not in active_years and year < int(previous["retrieved"][:4]):
                old[str(year)] = {"counts": counts, "retrieved": previous["retrieved"]}
        if old:
            archived[label] = old
    return archived


def publish(edition):
    edition["count"] = len(edition["sites"])
    edition["retrieved"] = datetime.now(timezone.utc).date().isoformat()
    if EDITION.exists():
        archived = previous_project_years(json.loads(EDITION.read_text(encoding="utf-8")), edition)
        if archived:
            edition["projectArchive"] = archived
    output = EDITION.with_suffix(".tmp")
    output.write_text(json.dumps(edition, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    output.replace(EDITION)
