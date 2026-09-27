"""Tester för mall/verifiera.py. Kör: python mall/test/test_verifiera.py"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "mall"))
from verifiera import starta_server, verifiera, visa_allt  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

fel_antal = 0


def ok(villkor, text):
    global fel_antal
    print(("OK   " if villkor else "FEL  ") + text)
    if not villkor:
        fel_antal += 1


def innehaller(fel, bit):
    return any(bit in f for f in fel)


# 1. En befintlig, korrekt sida passerar, inklusive inlänkning från index.html
with tempfile.TemporaryDirectory() as dumpar:
    fel = verifiera(ROT / "site", "extendmqtt.html", "index.html", Path(dumpar))
    ok(fel == [], f"extendmqtt.html passerar (fick: {fel})")
    ok((Path(dumpar) / "extendmqtt-sv-desktop.png").is_file(), "skärmdump SV desktop skapad")
    ok((Path(dumpar) / "extendmqtt-en-mobil.png").is_file(), "skärmdump EN mobil skapad")

# 2. Fixture med kända fel: varje fel ska rapporteras
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    shutil.copy(ROT / "site" / "index.html", tmp / "index.html")
    subprocess.run(
        ["pwsh", "-File", str(ROT / "mall" / "bygg-sida.ps1"),
         "-Innehall", str(ROT / "mall" / "test" / "fixtures" / "trasig.html"), "-Ut", str(tmp)],
        check=True, capture_output=True,
    )
    fel = verifiera(tmp, "trasig.html", "index.html", None)
    for f in fel:
        print("     rapporterat:", f)
    ok(innehaller(fel, "odefinieradFunktion"), "JS-fel rapporteras")
    ok(innehaller(fel, "Saknar data-en") and innehaller(fel, "Rubrik"), "saknad engelsk text rapporteras")
    ok(innehaller(fel, "inre markup") and innehaller(fel, "Text med"), "data-sv med inre markup rapporteras")
    ok(innehaller(fel, "finns-inte.html"), "trasig sidlänk rapporteras")
    ok(innehaller(fel, "#saknas"), "trasigt ankare rapporteras")
    ok(innehaller(fel, "index.html#finns-inte-heller"), "trasigt ankare på annan sida rapporteras")
    ok(innehaller(fel, "länkas inte från index.html"), "saknad inlänkning rapporteras")

# 3. Inför skärmdump ska alla scroll-animerade element (.reveal) göras synliga
httpd, bas = starta_server(ROT / "site")
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); page = b.new_page()
        page.goto(f"{bas}/extendmqtt.html")
        visa_allt(page)
        dolda = page.evaluate("document.querySelectorAll('.reveal:not(.visible)').length")
        ok(dolda == 0, f"alla .reveal synliga före skärmdump (dolda: {dolda})")
        b.close()
finally:
    httpd.shutdown()

# 4. Sida på nivå 3 med lang: en: /-länkar, länkar som slutar med /, ../-länkar och EN-start
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    shutil.copy(ROT / "site" / "index.html", tmp / "index.html")
    (tmp / "a" / "b").mkdir(parents=True)
    (tmp / "a" / "b" / "index.html").write_text("<!doctype html><html><body><p id='x'>B</p></body></html>", encoding="utf-8")
    innehall = tmp / "djup.html"
    innehall.write_bytes((
        "<!--\ntitle: Djup\ndescription: D\nlang: en\nrobots: noindex, nofollow\npage-css:\n-->\n"
        '<section style="background:var(--white);"><div class="container">'
        '<a href="/a/b/">rot-absolut mapp</a> <a href="/a/b/#x">rot-absolut ankare</a> '
        '<a href="../../b/">relativ mapp</a> <a href="/a/b/index.html">rot-absolut fil</a> '
        '<a href="/a/b/finns%20ej/">trasig</a></div></section>\n').encode("utf-8"))
    subprocess.run(["pwsh", "-File", str(ROT / "mall" / "bygg-sida.ps1"), "-Innehall", str(innehall),
                    "-Sokvag", "a/b/c/index.html", "-Ut", str(tmp)], check=True, capture_output=True)
    fel = verifiera(tmp, "a/b/c/index.html", None, None, forvantat_sprak="en")
    for f in fel:
        print("     rapporterat:", f)
    ok(not innehaller(fel, "/a/b/ pekar") and not innehaller(fel, "/a/b/#x") and not innehaller(fel, "../../b/"),
       "/-länkar, länkar som slutar med / och ../-länkar godtas")
    ok(not innehaller(fel, "index.html#"), "header-/footerlänkar ../../../index.html#… fungerar")
    ok(innehaller(fel, "finns%20ej"), "trasig länk med %-kodning rapporteras")
    ok(not innehaller(fel, "EN-läge"), "sidan startar i EN-läge")
    ok(any(f for f in fel) and len([f for f in fel if "finns%20ej" not in f]) == 0, "inga andra fel")

# 5. forvantat_sprak='en' på en svensk sida ger fel
fel = verifiera(ROT / "site", "extendmqtt.html", None, None, forvantat_sprak="en")
ok(innehaller(fel, "EN-läge"), "sida som inte startar i EN rapporteras")

print("Alla test OK" if fel_antal == 0 else f"{fel_antal} test fallerade")
sys.exit(1 if fel_antal else 0)
