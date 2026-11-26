"""Publish source-backed comparisons for completed City projects in the ICBC edition."""
from datetime import date
from html import escape
import json
import re
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

# Reviewed matches between the completed City listings and exact ICBC junction labels.
NAMES = {
    "203 ST & 56 AVE & DOUGLAS CRES & TURNING LANE":
        ("Douglas Crescent at 203 Street", "douglas-crescent-at-203-street"),
    "201A ST & 56 AVE": ("56 Avenue at 201A Street", "56-avenue-at-201a-street"),
}


def paired_years(years, reference, retrieved):
    complete = {y for y in years if y < date.fromisoformat(retrieved).year}
    n = 0
    while reference - n - 1 in complete and reference + n + 1 in complete:
        n += 1
    return [*range(reference - n, reference), *range(reference + 1, reference + n + 1)]


def span(years):
    return f"{years[0]}–{years[-1]}" if len(years) > 1 else str(years[0])


def layout(title, description, canonical, prefix, heading, content):
    return f"""<!doctype html>
<html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · CoolCode</title><meta name="description" content="{escape(description, quote=True)}">
<link rel="canonical" href="{escape(canonical, quote=True)}"><link rel="stylesheet" href="{prefix}style.css">
<script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script></head>
<body><main><nav aria-label="Site"><a href="https://coolcode.ca/">CoolCode.ca</a><a href="{prefix}">Crossing Record</a></nav>
<header><p class="tool-name">Langley, British Columbia</p><h1>{escape(heading)}</h1><p>{escape(description)}</p></header>
{content}</main></body></html>"""


def publish(stage, base):
    path = stage / "data/edition.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    years = data["years"]
    profiles = {}
    summaries = []
    directory = stage / "junctions"
    directory.mkdir()
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    def add_url(url):
        ET.SubElement(ET.SubElement(sitemap, "url"), "loc").text = url

    add_url(base + "junctions/")
    used_slugs = set()
    for label, project in data["projects"].items():
        name, slug = NAMES.get(label, (label, re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")))
        counts = data["sites"].get(label)
        if not project or counts is None:
            continue
        if len(years) != len(counts) or any(len(c) != 2 or not 0 <= c[1] <= c[0] for c in counts):
            raise ValueError(f"Inconsistent annual counts for {label}")
        reference = project["year"]
        archived = data.get("projectArchive", {}).get(label, {})
        by_year = {int(year): entry["counts"] for year, entry in archived.items()}
        by_year.update(zip(years, counts))
        all_years = sorted(by_year)
        paired = paired_years(all_years, reference, data["retrieved"])
        if reference not in by_year or not paired:
            continue
        if not slug or slug in used_slugs:
            raise ValueError(f"Junction needs a distinct profile URL: {label}")
        used_slugs.add(slug)
        before, after = paired[:len(paired)//2], paired[len(paired)//2:]
        def totals(period):
            return [sum(by_year[y][i] for y in period) for i in (0, 1)]
        earlier, later = totals(before), totals(after)
        route = f"junctions/{slug}/"
        profiles[label] = {"name": name, "path": route, "year": reference, "pairedYears": paired}
        wording = (f"ICBC recorded {earlier[0]} crashes in {span(before)} and {later[0]} in {span(after)} "
                   f"at this junction. The City lists the road project in {reference}.")
        summaries.append(f'<li><a href="{slug}/">{escape(name)}</a><p>{escape(wording)}</p></li>')
        query = escape(urlencode({"junction": label, "year": reference, "window": "matched"}), quote=True)
        pc = escape(project["url"], quote=True)
        workbook = escape(data["source"], quote=True)
        annual_rows = []
        for year in all_years:
            row = by_year[year]
            note = ("Project year · excluded" if year == reference else "Before" if year in before
                    else "After" if year in after else "Outside matched periods")
            if year not in years:
                note += " · source checked " + escape(archived[str(year)]["retrieved"])
            annual_rows.append(f'<tr><th scope="row">{year}</th><td>{row[0]}</td><td>{row[1]}</td><td>{note}</td></tr>')
        period_rows = []
        for caption, period, values in (("Before", before, earlier), ("After", after, later)):
            period_rows.append(f'<tr><th scope="row">{caption} · {span(period)}</th><td>{values[0]}</td>'
                               f'<td>{values[1]}</td><td>{values[0]/len(period):.1f}</td></tr>')
        years_text = "one complete calendar year" if len(before) == 1 else f"{len(before)} complete calendar years"
        content = f"""<p><a href="../../?{query}">Open this junction and matched comparison on the map</a></p>
<section><h2>Before and after the project year</h2>
<p>Each period covers {years_text} immediately beside {reference}. The project year is excluded from both totals.</p>
<table><thead><tr><th scope="col">Period</th><th scope="col">Reported crashes</th><th scope="col">Casualty crashes</th><th scope="col">Reported per year</th></tr></thead><tbody>{''.join(period_rows)}</tbody></table></section>
<section><h2>Annual ICBC counts</h2><p>ICBC junction label <strong>{escape(label)}</strong>. Casualty crashes involve injury or death and are included in the reported total.</p>
<table><thead><tr><th scope="col">Year</th><th scope="col">Reported crashes</th><th scope="col">Casualty crashes</th><th scope="col">Comparison period</th></tr></thead><tbody>{''.join(annual_rows)}</tbody></table></section>
<section><h2>Road work and sources</h2><p>{escape(project['text'])} Langley City lists this work as completed and gives an estimated schedule in {reference}.</p>
<p>Traffic volume, reporting practices and other conditions can vary between years. These counts alone cannot establish the effect of the project.</p>
<ul><li><a href="{pc}">Langley City project record</a></li><li><a href="{workbook}">ICBC reported crashes workbook</a> · source checked {escape(data['retrieved'])}</li></ul>
<p>Contains information licensed under ICBC’s Open Data Licence.</p></section>
<footer><a href="../">Browse all documented junction projects</a><a href="../../?{query}">Explore this junction</a></footer>"""
        folder = stage / route
        folder.mkdir()
        (folder / "index.html").write_text(layout(f"{name} ICBC crash history", wording, base + route,
                                                 "../../", name, content), encoding="utf-8")
        add_url(base + route)

    subtitle = "Compare annual ICBC crash counts at Langley junctions with completed City road projects."
    listing = ''.join(summaries) or "<li>No projects have a complete calendar year on both sides in this edition.</li>"
    directory_content = f"""<section><h2>Junctions with matched project records</h2>
<ul class="project-profiles">{listing}</ul></section>
<section><h2>How projects are compared</h2><p>Each profile matches a City project to an exact ICBC junction label. It uses equally long periods of complete calendar years before and after the project year, and shows every available annual count separately.</p>
<p><a href="../">Explore the full Langley intersection map</a> · <a href="{escape(data['source'], quote=True)}">ICBC reported crashes workbook</a></p></section>"""
    (directory / "index.html").write_text(layout("Langley road projects and intersection crash histories", subtitle,
           base + "junctions/", "../", "Langley intersection project records", directory_content), encoding="utf-8")
    ET.ElementTree(sitemap).write(stage / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    data["projectProfiles"] = profiles
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
