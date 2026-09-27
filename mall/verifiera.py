"""Verifierar en byggd sida i site/: JS-fel, SV/EN-växling, länkar, mobilmeny och inlänkning.

Kör: python mall/verifiera.py extendmqtt.html --fran index.html --skarmdumpar <katalog>
"""
import argparse
import functools
import http.server
import re
import sys
import threading
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

EXTERNT = re.compile(r"^(https?:|mailto:|tel:|javascript:)", re.I)

# Element i innehållet (inte header/mobilmeny/footer) vars data-sv-element har barn-element:
# applyLang() sätter textContent och raderar då den inre markupen.
JS_NASTLADE = """() => [...document.querySelectorAll('[data-sv]')]
  .filter(e => !e.closest('header, #mobileNav, footer') && e.children.length > 0)
  .map(e => e.dataset.sv)"""
# data-en saknas eller är tom: applyLang() faller då tillbaka på svenskan, så texten förblir svensk i EN.
JS_SAKNAR_EN = """() => [...document.querySelectorAll('[data-sv]')]
  .filter(e => !e.closest('header, #mobileNav, footer') && !(e.dataset.en || '').trim())
  .map(e => e.dataset.sv)"""
JS_TOMMA_DATA = """() => [...document.querySelectorAll('[data-sv]')]
  .filter(e => e.textContent.trim() === '').map(e => e.dataset.sv)"""
JS_ID_MED_TEXT = """() => Object.fromEntries([...document.querySelectorAll('body [id]')]
  .filter(e => !['SCRIPT', 'STYLE'].includes(e.tagName))
  .map(e => [e.id, e.textContent.trim() !== '']))"""


class TystHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def starta_server(rot: Path):
    handler = functools.partial(TystHandler, directory=str(rot))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def lyssna_efter_fel(page, fel: list):
    def konsol(m):
        # Webbtypsnitt från Google kan saknas offline; det är inte ett fel i sidan.
        if m.type == "error" and "fonts.g" not in (m.location or {}).get("url", ""):
            fel.append(f"Konsolfel: {m.text}")

    page.on("console", konsol)
    page.on("pageerror", lambda e: fel.append(f"JS-fel: {e}"))


def visa_allt(page):
    """Gör scroll-animerade element (.reveal) synliga så att en helsidesdump visar allt innehåll."""
    page.evaluate("document.querySelectorAll('.reveal').forEach(e => e.classList.add('visible'))")
    page.wait_for_timeout(1000)  # låt CSS-övergången (inkl. reveal-delay) bli klar


def losa_upp(rot: Path, sida: str, sokvag: str) -> Path:
    """Löser en länks sökväg till en fil under rot: /-länkar från rot, andra relativt sidans mapp, mapp → index.html."""
    sokvag = unquote(sokvag)
    bas = rot if sokvag.startswith("/") else (rot / sida).parent
    mal = (bas / sokvag.lstrip("/")).resolve()
    if sokvag.endswith("/") or mal.is_dir():
        mal = mal / "index.html"
    return mal


def kontrollera_lankar(page, rot: Path, sida: str) -> list:
    fel = []
    ids = set(page.eval_on_selector_all("[id]", "els => els.map(e => e.id)"))
    denna = (rot / sida).resolve()
    for href in page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
        if EXTERNT.match(href):
            continue
        delar = urlsplit(href)
        mal = losa_upp(rot, sida, delar.path) if delar.path else denna
        if not mal.is_file():
            fel.append(f"Länken {href} pekar på en fil som inte finns")
            continue
        if delar.fragment:
            if mal == denna:
                finns = delar.fragment in ids
            else:
                finns = re.search(r"""id=["']%s["']""" % re.escape(delar.fragment), mal.read_text(encoding="utf-8")) is not None
            if not finns:
                fel.append(f"Länken {href} pekar på ett ankare som saknas")
    return fel


def kontrollera_sprak(page) -> list:
    fel = [f"data-sv med inre markup (försvinner vid språkbyte): '{sv}'" for sv in page.evaluate(JS_NASTLADE)]
    fel += [f"Saknar data-en (visas på svenska i EN): '{sv}'" for sv in page.evaluate(JS_SAKNAR_EN)]
    sv_ids = page.evaluate(JS_ID_MED_TEXT)
    page.click("#langToggle")
    fel += [f"Element blir tomt i EN (tom i EN): data-sv='{sv}'" for sv in page.evaluate(JS_TOMMA_DATA)]
    en_ids = page.evaluate(JS_ID_MED_TEXT)
    fel += [f"Element blir tomt i EN (tom i EN): id='{i}'" for i, har in sv_ids.items() if har and not en_ids.get(i, False)]
    if "undefined" in page.inner_text("body"):
        fel.append("Texten 'undefined' syns i EN (saknad nyckel i translations)")
    page.click("#langToggle")
    return fel


def kontrollera_inlankning(rot: Path, sida: str, fran: str) -> list:
    kalla = rot / fran
    if not kalla.is_file():
        return [f"Källsidan {fran} finns inte"]
    if not re.search(r'href="%s(#[^"]*)?"' % re.escape(sida), kalla.read_text(encoding="utf-8")):
        return [f"{sida} länkas inte från {fran}"]
    return []


def verifiera(rot: Path, sida: str, fran=None, skarmdumpar=None, forvantat_sprak=None) -> list:
    rot = Path(rot).resolve()
    if not (rot / sida).is_file():
        return [f"Sidan {sida} finns inte i {rot}"]
    fel = []
    namn = sida[:-5].replace("/", "_") if sida.endswith(".html") else sida.replace("/", "_")
    httpd, bas = starta_server(rot)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            # Desktop: JS-fel, språk, länkar, skärmdump SV
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            lyssna_efter_fel(page, fel)
            page.goto(f"{bas}/{sida}", wait_until="load")
            if forvantat_sprak and page.evaluate("document.documentElement.lang") != forvantat_sprak:
                fel.append(f"Sidan startar inte i {forvantat_sprak.upper()}-läge")
            if skarmdumpar:
                Path(skarmdumpar).mkdir(parents=True, exist_ok=True)
                visa_allt(page)
                page.screenshot(path=str(Path(skarmdumpar) / f"{namn}-sv-desktop.png"), full_page=True)
            fel += kontrollera_sprak(page)
            fel += kontrollera_lankar(page, rot, sida)
            page.close()
            # Mobil: hamburgermeny, skärmdump EN
            mobil = browser.new_page(viewport={"width": 375, "height": 812})
            mobil.goto(f"{bas}/{sida}", wait_until="load")
            mobil.click("#hamburger")
            if not mobil.is_visible("#mobileNav"):
                fel.append("Mobilmenyn öppnas inte vid 375 px")
            mobil.click("#hamburger")
            if skarmdumpar:
                mobil.evaluate("if (currentLang !== 'en') toggleLang()")
                visa_allt(mobil)
                mobil.screenshot(path=str(Path(skarmdumpar) / f"{namn}-en-mobil.png"), full_page=True)
            browser.close()
    finally:
        httpd.shutdown()
    if fran:
        fel += kontrollera_inlankning(rot, sida, fran)
    return fel


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verifierar en byggd sida i site/.")
    ap.add_argument("sida", help="filnamn i --rot, t.ex. extendmqtt.html")
    ap.add_argument("--rot", type=Path, default=Path(__file__).resolve().parent.parent / "site")
    ap.add_argument("--fran", help="sida som ska länka till sidan, t.ex. index.html")
    ap.add_argument("--skarmdumpar", type=Path, help="katalog för skärmdumpar")
    ap.add_argument("--sprak", choices=["sv", "en"], help="förväntat startspråk")
    a = ap.parse_args(argv)
    fel = verifiera(a.rot, a.sida, a.fran, a.skarmdumpar, a.sprak)
    for f in fel:
        print("FEL:", f)
    print("OK" if not fel else f"{len(fel)} fel")
    return 1 if fel else 0


if __name__ == "__main__":
    sys.exit(main())
