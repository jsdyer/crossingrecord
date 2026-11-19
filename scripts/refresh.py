"""Summarize ICBC's packaged Tableau workbook at named junctions in Langley."""
from collections import defaultdict
from io import BytesIO
from pathlib import Path
import tempfile
from zipfile import ZipFile
from tableauhyperapi import Connection, HyperProcess, Telemetry
from source_io import fetch, publish

WORKBOOK = "https://public.tableau.com/workbooks/ICBCReportedCrashes.twb"
QUERY = """
SELECT "ROAD_LOCATION_DESCRIPTION", "DATE_OF_LOSS_YEAR", "CRASH_SEVERITY", SUM("TOTAL_CRASHES")
FROM "Extract"."Extract"
WHERE "MUNICIPALITY_NAME" = 'LANGLEY' AND "INTERSECTION_CRASH" = 'Y'
AND COALESCE("ROAD_LOCATION_DESCRIPTION", '') <> ''
GROUP BY "ROAD_LOCATION_DESCRIPTION", "DATE_OF_LOSS_YEAR", "CRASH_SEVERITY"
ORDER BY 1,2,3
"""
LOCATION_QUERY = """
SELECT DISTINCT "ROAD_LOCATION_DESCRIPTION", "LATITUDE", "LONGITUDE"
FROM "Extract"."Extract"
WHERE "MUNICIPALITY_NAME" = 'LANGLEY' AND "INTERSECTION_CRASH" = 'Y'
AND COALESCE("ROAD_LOCATION_DESCRIPTION", '') <> ''
AND "LATITUDE" IS NOT NULL AND "LONGITUDE" IS NOT NULL
ORDER BY 1,2,3
"""


def source_locations(rows, sites):
    locations = defaultdict(list)
    for name, lat, lon in rows:
        if name not in sites or not (48 < lat < 50 and -124 < lon < -121):
            raise ValueError("Review Langley junction coordinates")
        locations[name].append([float(lat), float(lon)])
    if not locations:
        raise ValueError("No mapped junctions in ICBC workbook")
    return locations


PROJECTS = {
    "203 ST & 56 AVE & DOUGLAS CRES & TURNING LANE":{
        "year":2024, "text":"Northwest corner rebuilt for pedestrian access, with traffic signal upgrades.",
        "url":"https://www.langleycity.ca/business-development/current-projects/douglas-crescent-and-203-street-intersection-improvements"},
    "201A ST & 56 AVE":{
        "year":2024,"text":"Traffic signal upgraded during the 56 Avenue utility project.",
        "url":"https://www.langleycity.ca/business-development/current-projects/56-avenue-water-storm-and-sanitary-sewer-replacement"}
}


def summarize(rows):
    all_sites = defaultdict(dict)
    all_years = set()
    for site, year, severity, count in rows:
        if severity not in ("PROPERTY DAMAGE ONLY", "CASUALTY CRASH") or count < 1:
            raise ValueError("Review source severity and count")
        counts = all_sites[site].setdefault(year,[0,0])
        counts[0] += count
        counts[1] += count if severity == "CASUALTY CRASH" else 0
        all_years.add(year)
    years = sorted(all_years)
    if len(years) < 5 or len(all_sites) < 100 or not PROJECTS.keys() <= all_sites.keys():
        raise ValueError("Missing years, junctions or project matches")
    # Exact source labels identify locations. One row per place and year keeps the
    # published download small; a zero means no matching reports in this extract.
    sites = {site:[by_year.get(y,[0,0]) for y in years] for site,by_year in sorted(all_sites.items())}
    return {"start":str(years[0]),"end":str(years[-1]),"years":years,"sites":sites,
            "projects":PROJECTS,"source":WORKBOOK}


def main():
    with tempfile.TemporaryDirectory() as folder, ZipFile(BytesIO(fetch(WORKBOOK))) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith("public data set.hyper")]
        if len(names) != 1:
            raise ValueError("Review workbook extract names")
        path = Path(folder) / "crashes.hyper"
        path.write_bytes(archive.read(names[0]))
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,parameters={"use_tcp_port":"auto","log_dir":folder}) as process:
            with Connection(process.endpoint,str(path)) as connection:
                edition = summarize(connection.execute_list_query(QUERY))
                edition["locations"] = source_locations(
                    connection.execute_list_query(LOCATION_QUERY), edition["sites"]
                )
    publish(edition)


if __name__ == "__main__":
    main()
