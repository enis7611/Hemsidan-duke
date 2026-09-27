"""Tester för mall/guider.py. Kör: python mall/test/test_guider.py"""
import json
import re
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "mall"))
from guider import Katalog, OkandStruktur, ar_guide, konvertera  # noqa: E402

FIX = ROT / "mall" / "test" / "fixtures" / "leverans-2026-09-26"
GUIDER = json.loads((FIX / "simulationsmcp" / "v1" / "modeling_guides.json").read_text(encoding="utf-8"))
skriv_om = lambda a: "/simulationsmcp/v1/guides/" + a[len("/guides/"):] if a.startswith("/guides/") else a
ADRESSER = [skriv_om(a) for a in json.loads((FIX / "urls.json").read_text(encoding="utf-8"))]
KAT = Katalog(GUIDER, ADRESSER)
fel_antal = 0


def ok(villkor, text):
    global fel_antal
    print(("OK   " if villkor else "FEL  ") + text)
    if not villkor:
        fel_antal += 1


def adress_for(fil: Path) -> str:
    rel = fil.relative_to(FIX).as_posix()
    return skriv_om("/" + rel[: -len("index.html")])


sidor = sorted(FIX.glob("guides/**/index.html"))
ok(len(sidor) == 19, f"19 guidesidor i fixturen (fick {len(sidor)})")

resultat = {}
for fil in sidor:
    text = fil.read_text(encoding="utf-8")
    ok(ar_guide(text), f"känns igen som guide: {fil.relative_to(FIX)}")
    resultat[adress_for(fil)] = konvertera(text, adress_for(fil), KAT, skriv_om)

allt = "\n".join(resultat.values())
ok("[object Object]" not in allt, "inget [object Object] kvar")
ok('href="/guides/' not in allt, "alla /guides/-länkar omskrivna")
ok("data-sv=\"Tell us" not in allt and allt.count('data-en="Tell us about your problem"') == 19, "K10 CTA tvåspråkig på alla 19")

sq = resultat["/simulationsmcp/v1/guides/queuing/simple-queue/"]
ok(sq.startswith("<!--\ntitle: Simple Queue (M/M/1) | Duke Systems AB\ndescription: A single-server"), "metadata: title/description")
ok("\nlang: en\nrobots: noindex, nofollow\npage-css:\n" in sq, "metadata: lang + robots före page-css")
ok(".duke-table{" in sq, "tabell-CSS med i page-css")
ok('href="/simulationsmcp/v1/guides/queuing/multi-server/"' in sq, "variant med scenario blir länk (multi_server)")
ok("Finite queue (blocking)" in sq and "Set Queue maximum capacity" in sq, "variant utan scenario: namn + ändring")
ok('<span class="terminal-result">Arrivals (ItemOut) → WaitingLine (ItemIn)</span>' in sq, "kopplingar som terminalrader")
ok("<th>Block</th><th>Library</th><th>Label</th><th>Purpose</th>" in sq, "blocktabellens rubriker")
ok("mean service time &gt;= mean inter-arrival time" in sq, "text HTML-escapad (&gt;)")
ok('href="/simulationsmcp/v1/guides/queuing/"' in sq and "← Queuing Systems" in sq, "tillbaka-länk från brödsmulan")
ok(sq.count("mcp-bg-pattern") == 2, "två mörka sektioner (kopplingar, mått)")
ok(not re.search(r'data-sv="(?!Berätta|Tell)', sq.split("<!-- ─── CTA")[0]), "inga data-sv i guidetexten")

rot = resultat["/simulationsmcp/v1/guides/"]
ok(rot.count('class="service-card') == 6, "startsidan: ett kort per kategori (6)")
ok('href="/simulationsmcp/v1/guides/logistics/"' in rot, "startsidan: kategorilänkar omskrivna")
kat = resultat["/simulationsmcp/v1/guides/queuing/"]
ok(kat.count('class="service-card') == 3, "kategorisidan queuing: 3 guidekort")
ok("Logistics &amp; Supply Chain" in resultat["/simulationsmcp/v1/guides/logistics/"], "& i kategorinamn escapat")

# Okänd struktur stoppar
okand = (FIX / "guides/queuing/simple-queue/index.html").read_text(encoding="utf-8").replace(
    '<section class="key-metrics">', '<section class="ny-sektion">')
try:
    konvertera(okand, "/simulationsmcp/v1/guides/queuing/simple-queue/", KAT, skriv_om)
    ok(False, "okänd sektion stoppar (inget fel)")
except OkandStruktur as e:
    ok("ny-sektion" in str(e), f"okänd sektion stoppar [{e}]")
try:
    konvertera("<html><body><p>x</p></body></html>", "/x/", KAT, skriv_om)
    ok(False, "sida utan guide-content stoppar (inget fel)")
except OkandStruktur as e:
    ok(True, f"sida utan guide-content stoppar [{e}]")
ok(not ar_guide("<html><body><main><p>x</p></main></body></html>"), "vanlig sida känns inte igen som guide")

print("Alla test OK" if fel_antal == 0 else f"{fel_antal} test fallerade")
sys.exit(1 if fel_antal else 0)
