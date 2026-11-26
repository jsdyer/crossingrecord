"""Exercise the built starter at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=__import__("os").environ.get("CHROMIUM_PATH"))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.route("https://tile.openstreetmap.org/**", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.locator("#explore").wait_for()
                page.locator("#tile-notice").wait_for()
                page.unroute("https://tile.openstreetmap.org/**")
                tile = '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#cadfc9"/></svg>'
                page.route("https://tile.openstreetmap.org/**", lambda route: route.fulfill(content_type="image/svg+xml", body=tile))
                page.locator("#retry-tiles").click()
                page.wait_for_selector("img.leaflet-tile-loaded")
                assert page.locator("#tile-notice").is_hidden()
                assert page.locator("#projectlink").is_visible()
                assert page.locator("#junction-map path.leaflet-interactive").count() >= 100
                assert page.locator("#first").input_value() in page.locator("#junction-location").inner_text()
                page.locator("#fit-junctions").click()
                page.locator("#second").select_option("Casualty crashes")
                assert page.locator("#history tbody tr").count() >= 5
                page.locator("#turnexample").click()
                assert "203 pedestrians" in page.locator("#turns").inner_text()
                page.locator("#search").fill("xyz-nothing")
                assert "No matching" in page.locator("#finding").inner_text()
                assert page.locator(".metrics").is_hidden()
                page.locator("#search").fill("201A ST")
                assert page.locator("#first option").count() >= 1
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                page.reload()
                page.wait_for_function("document.querySelector('#value1').textContent.includes('/ year')")
                assert page.locator("#current-junction").inner_text() == page.locator("#first").input_value()
                result_top = page.locator("#value1").bounding_box()["y"]
                assert 0 <= result_top < 844
                assert result_top < page.locator("#search").bounding_box()["y"]
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: project subpath, data, filters and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
