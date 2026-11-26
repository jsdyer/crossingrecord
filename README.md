# Crossing Record

Compare ICBC crash counts at Langley intersections before and after documented road work. [Open the tool](https://coolcode.ca/crossingrecord/).

<!-- coolcode:guide -->
Select a dot on the junction map or search by road name. Choose a Langley junction and compare annual averages on either side of a reference year. Douglas Crescent at 203 Street and 56 Avenue at 201A Street have linked, completed city projects. The project year is excluded from both periods. Counts represent crashes reported to ICBC, and the view shows how many years support each average.
<!-- /coolcode:guide -->

## Published junction profiles

[Browse documented road projects](https://coolcode.ca/crossingrecord/junctions/). Each profile links its municipal project record, the exact ICBC junction label and all available annual counts. For the comparison it takes the same number of consecutive complete calendar years immediately before and after the City’s project year. The last complete year is determined by the source retrieval date. Select “Open this junction and matched comparison on the map” to reproduce the chosen dates and junction. “All available years” remains the default when entering the map directly. Pages are regenerated from the checked dataset during publication. When the ICBC workbook rolls forward, its earlier complete years are retained for these matched projects with their original source-check dates. Newer official counts supersede earlier observations for the same year.

## Sources and interpretation

ICBC assigns approximate locations when a crash report has enough detail. This view uses its Langley municipality field and exact junction labels, including turning lanes where recorded. Boundary records assigned to neighbouring municipalities and reports without a junction name are outside this selection. Zero means the extract has no matching report. A casualty crash is a crash involving injury or death. Traffic volume, construction and reporting can all change across years.

The collector extracts ICBC’s public Hyper table from its official packaged Tableau workbook. It selects INTERSECTION_CRASH=Y, MUNICIPALITY_NAME=LANGLEY and a nonblank road location. It sums TOTAL_CRASHES for all severities and separately for CASUALTY CRASH. It groups on the complete ROAD_LOCATION_DESCRIPTION, preserving distinct interchange and turning-lane labels. There is no deduplication by similar street names. The covered years move with ICBC’s workbook. Changes in reported crashes can reflect traffic exposure, disruption, development and reporting. At 208 Street and 88 Avenue, Township engineering report 25-22 supplies a peak-hour lower bound for each of two right turns and an eight-hour pedestrian count. The place name is matched exactly. These observations have different time bases and cannot be combined into a crash rate. [Township report 25-22, copy (PDF)](https://www.langleyunion.ca/content/files/2025/02/2025-02-24-Council-Meeting---Sliplanes-Report.pdf). The two project years come from Langley City’s completed pages, which give estimated durations rather than commissioning dates.

[ICBC public workbook](https://public.tableau.com/workbooks/ICBCReportedCrashes.twb). Contains information licensed under ICBC’s Open Data Licence.

## Data and maintenance

The page reports the retrieval date in UTC separately from the periods of observation. The offline build uses the last validated snapshot committed in `web/data/edition.json`. The monthly Actions workflow also supports manual runs. A failed refresh exits before replacing the published edition. Each dot retains a distinct latitude and longitude from the same workbook, matched on the complete junction label. Two labels in the 2021–2025 edition each have two published locations. Both dots select the same historical series. Counts apply to the label, without implying individual crashes occurred at a dot. All filtering runs in the browser. OpenStreetMap receives street-tile requests for the displayed area. Leaflet is bundled under the licence in web/vendor. The page downloads the edition from CoolCode and stores no selections.

Run `python3 scripts/refresh.py` to rebuild the data from source. Install the official Hyper reader with python3 -m pip install -r scripts/requirements.txt first.

Run `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests` and `python3 scripts/build.py`. Serve the generated `dist/` directory to preview. The Pages workflow tests desktop and mobile browser views before deployment.

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. A scheduler on our own Linux server is the planned independent trigger. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
