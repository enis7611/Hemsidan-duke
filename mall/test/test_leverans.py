"""Tester för mall/leverans.py. Kör: python mall/test/test_leverans.py"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "mall"))
import leverans as L  # noqa: E402

FIX = ROT / "mall" / "test" / "fixtures" / "leverans-2026-09-26"
REGLER = L.las_regler()
fel_antal = 0


def ok(villkor, text):
    global fel_antal
    print(("OK   " if villkor else "FEL  ") + text)
    if not villkor:
        fel_antal += 1


def ny_miljo(tmp: Path):
    """Kopia av leveransen + kopia av site/ + tom innehållsmapp."""
    shutil.copytree(FIX, tmp / "ingest")
    shutil.copytree(ROT / "site", tmp / "site")
    (tmp / "innehall").mkdir()
    return tmp / "ingest", tmp / "site", tmp / "innehall"


# 1. Adressregler
ok(L.skriv_om("/guides/queuing/", REGLER) == "/simulationsmcp/v1/guides/queuing/", "/guides/ skrivs om")
ok(L.skriv_om("/simulationsmcp/v1/guides/x/", REGLER) == "/simulationsmcp/v1/guides/x/", "redan omskriven lämnas")
ok(L.skriv_om("/simulationsmcp/v1/modeling_guides.json", REGLER) == "/simulationsmcp/v1/modeling_guides.json", "annan adress orörd")
ok(L.fil_for_adress("/a/b/") == "a/b/index.html" and L.fil_for_adress("/a/x.json") == "a/x.json", "adress → fil")
ok(L.adress_for_fil("guides/index.html") == "/guides/" and L.adress_for_fil("s/v1/x.json") == "/s/v1/x.json", "fil → adress")

# 2. UPLOAD.txt
up = L.las_upload((FIX / "UPLOAD.txt").read_text(encoding="utf-8"),
                  {"simulationsmcp/v1/modeling_guides.json", "simulationsmcp/v1/guide-schema.json"})
ok(up.version == "1.13.0" and up.datum == "2026-09-26", f"version/datum ({up.version}, {up.datum})")
ok(up.summor == {"simulationsmcp/v1/modeling_guides.json": "a923b679a0efba85b0801d59a9c93eedf41b13faa5259f4c6343f1010d207425"},
   f"kontrollsumma kopplad till rätt fil ({up.summor})")
ok(up.must == {"simulationsmcp/v1/modeling_guides.json", "simulationsmcp/v1/guide-schema.json"}, f"MUST-filer ({up.must})")

# 3. Plan för dagens leverans
with tempfile.TemporaryDirectory() as tmp:
    ingest, site, innehall = ny_miljo(Path(tmp))
    plan = L.planera(ingest, site, innehall, REGLER)
    ok(plan.stopp == [], f"inga stopp ({plan.stopp})")
    ok(len(plan.poster) == 21, f"21 poster (fick {len(plan.poster)})")
    ok(sum(p.spar == "kopia" for p in plan.poster) == 2 and sum(p.spar == "guide" for p in plan.poster) == 19, "2 kopior + 19 guider")
    ok(plan.regler_anvanda, "regeln användes")
    ok(plan.rotmappar == ["/simulationsmcp/v1/"], f"rotmapp ({plan.rotmappar})")
    g = next(p for p in plan.poster if p.kalla == "guides/queuing/simple-queue/index.html")
    ok(g.mal == "simulationsmcp/v1/guides/queuing/simple-queue/index.html" and g.status == "ny", "guide: mål + status ny")
    j = next(p for p in plan.poster if p.kalla.endswith("modeling_guides.json"))
    ok(j.must and j.summa and j.status == "ny", "JSON: MUST, summa, ny")
    text = L.beskriv(plan)
    ok("1.13.0" in text and "MUST" in text and "a923b679" in text, "beskriv: version, MUST, summa")

    # 4. Bygg + kontrollera (utan webbläsare här; verifieraren testas separat)
    byggda = L.bygg(plan, ingest, site, innehall)
    ok(len(byggda) == 21, f"21 filer byggda ({len(byggda)})")
    ok((site / "simulationsmcp/v1/modeling_guides.json").read_bytes() == (FIX / "simulationsmcp/v1/modeling_guides.json").read_bytes(), "JSON byte-identisk")
    ok((site / "simulationsmcp/v1/guides/index.html").is_file(), "guidestartsidan byggd")
    ok((innehall / "simulationsmcp/v1/guides/queuing/index.html").is_file(), "innehållsfil sparad")
    robots = (site / "robots.txt").read_text(encoding="utf-8")
    ok("User-agent: *\nDisallow: /simulationsmcp/v1/" in robots and "User-agent: GPTBot" in robots, "robots.txt")
    fel = L.kontrollera(plan, ingest, site, webblasare=False)
    ok(fel == [], f"kontroll utan fel ({fel})")

    # 5. Ny plan efter bygget: allt oförändrat, robots läggs inte till två gånger
    plan2 = L.planera(ingest, site, innehall, REGLER)
    ok(all(p.status == "oforandrad" for p in plan2.poster), "andra körningen: allt oförändrat")
    L.bygg(plan2, ingest, site, innehall)
    ok((site / "robots.txt").read_text(encoding="utf-8").count("User-agent: *") == 1, "robots.txt inte dubblerad")

    # 6. Kontrollen hittar inlänkar och [object Object]
    idx = site / "index.html"
    idx.write_bytes(idx.read_bytes().replace(b"</footer>", b'<a href="simulationsmcp/v1/guides/">x</a></footer>', 1))
    (site / "simulationsmcp/v1/guides/flow/index.html").write_bytes(b"<p>[object Object]</p>")
    fel = L.kontrollera(plan, ingest, site, webblasare=False)
    ok(any("index.html" in f and "länkar in" in f for f in fel), "inlänk från index.html upptäcks")
    ok(any("[object Object]" in f for f in fel), "[object Object] upptäcks")

# 7. Delleverans: bara en guide + styrfiler; övriga finns redan → inte "saknas"
with tempfile.TemporaryDirectory() as tmp:
    ingest, site, innehall = ny_miljo(Path(tmp))
    L.bygg(L.planera(ingest, site, innehall, REGLER), ingest, site, innehall)
    for p in list(ingest.rglob("*")):
        if p.is_file() and p.name not in ("UPLOAD.txt", "urls.json") and "simple-queue" not in p.as_posix():
            p.unlink()
    plan = L.planera(ingest, site, innehall, REGLER)
    ok(len(plan.poster) == 1 and plan.saknas == [], f"delleverans: 1 post, inget saknas ({len(plan.poster)}, {plan.saknas})")

# 8. Fel kontrollsumma stoppar; fil utan adress stoppar; saknad adress rapporteras
with tempfile.TemporaryDirectory() as tmp:
    ingest, site, innehall = ny_miljo(Path(tmp))
    j = ingest / "simulationsmcp/v1/modeling_guides.json"
    j.write_bytes(j.read_bytes() + b" ")
    (ingest / "guides/extra").mkdir()
    (ingest / "guides/extra/index.html").write_text("<p>x</p>", encoding="utf-8")
    u = json.loads((ingest / "urls.json").read_text(encoding="utf-8")) + ["/guides/finns-inte/"]
    (ingest / "urls.json").write_text(json.dumps(u), encoding="utf-8")
    plan = L.planera(ingest, site, innehall, REGLER)
    ok(any("kontrollsumma" in s for s in plan.stopp), "fel kontrollsumma stoppar")
    ok(plan.utan_adress == ["guides/extra/index.html"] and any("utan adress" in s for s in plan.stopp), "fil utan adress stoppar")
    ok(plan.saknas == ["/simulationsmcp/v1/guides/finns-inte/"], f"saknad adress ({plan.saknas})")

# 9. Källan rättad: adresser redan under /simulationsmcp/v1/guides/ → regeln används inte
with tempfile.TemporaryDirectory() as tmp:
    ingest, site, innehall = ny_miljo(Path(tmp))
    (ingest / "simulationsmcp/v1/guides").parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(ingest / "guides"), str(ingest / "simulationsmcp/v1/guides"))
    u = [L.skriv_om(a, REGLER) for a in json.loads((ingest / "urls.json").read_text(encoding="utf-8"))]
    (ingest / "urls.json").write_text(json.dumps(u), encoding="utf-8")
    plan = L.planera(ingest, site, innehall, REGLER)
    ok(not plan.regler_anvanda and plan.stopp == [] and len(plan.poster) == 21, "rättad källa: regeln används inte, 21 poster")
    ok("regeln användes inte" in L.beskriv(plan), "planen säger att regeln inte användes")

# 10. Arkivering
with tempfile.TemporaryDirectory() as tmp:
    ingest, _, _ = ny_miljo(Path(tmp))
    (ingest / "_importerat").mkdir()
    (ingest / "_importerat" / ".gitkeep").write_bytes(b"")
    a1 = L.arkivera(ingest, "2026-09-26")
    ok(a1.name == "2026-09-26" and (a1 / "urls.json").is_file() and (a1 / "guides/index.html").is_file(), "arkiv 1")
    ok(sorted(p.name for p in ingest.iterdir()) == ["_importerat"], "inkorgen tom efter arkivering")
    (ingest / "urls.json").write_text("[]", encoding="utf-8")
    a2 = L.arkivera(ingest, "2026-09-26")
    ok(a2.name == "2026-09-26-2", "samma dag → -2")

print("Alla test OK" if fel_antal == 0 else f"{fel_antal} test fallerade")
sys.exit(1 if fel_antal else 0)
