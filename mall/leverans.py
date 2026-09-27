"""Ingest av leveranser: UPLOAD.txt + urls.json + material → site/.

  python mall/leverans.py plan          visar planen (skriver inget)
  python mall/leverans.py bygg          kopierar, konverterar guider, bygger sidor, uppdaterar robots.txt
  python mall/leverans.py kontrollera   facit, kontrollsummor, inlänkar, [object Object], noindex, verifiera.py
  python mall/leverans.py arkivera      flyttar leveransen till ingest/_importerat/<datum>/

Se docs/superpowers/specs/2026-09-26-ingest-leveranser-design.md.
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlsplit

import guider

MALL = Path(__file__).resolve().parent
ROT = MALL.parent
STYRFILER = {"UPLOAD.txt", "urls.json"}
HEX64 = re.compile(r"^\s*([0-9a-f]{64})\s*$")
HEX_I_RAD = re.compile(r"\b([0-9a-f]{64})\b")
EXTERNT = re.compile(r"^(https?:|mailto:|tel:|javascript:|#)", re.I)
AI_ROBOTAR = ["GPTBot", "ClaudeBot", "CCBot", "Google-Extended", "PerplexityBot", "Bytespider"]


# ─── Adresser ────────────────────────────────────────────────────────────────

def las_regler(fil=MALL / "adressregler.json"):
    return json.loads(Path(fil).read_text(encoding="utf-8"))["prefix"]


def las_tillatna(fil=MALL / "adressregler.json"):
    """Mappar där en leverans får publicera. Allt i en leverans döljs i robots.txt, så '/' får aldrig bli en rotmapp."""
    return json.loads(Path(fil).read_text(encoding="utf-8"))["tillatna_rotmappar"]


def skriv_om(adress, regler):
    for r in regler:
        if adress.startswith(r["till"]):
            return adress
        if adress.startswith(r["fran"]):
            return r["till"] + adress[len(r["fran"]):]
    return adress


def adress_for_fil(rel):
    if rel == "index.html" or rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def fil_for_adress(adress):
    a = adress.lstrip("/")
    return a + "index.html" if (a == "" or a.endswith("/")) else a


def rotmappar(facit):
    """Minsta mängd mappar som innehåller alla facit-adresser, t.ex. ['/simulationsmcp/v1/']."""
    mappar = sorted({str(PurePosixPath(fil_for_adress(a)).parent) for a in facit}, key=len)
    valda = []
    for m in mappar:
        if not any(m == v or m.startswith(v + "/") for v in valda):
            valda.append(m)
    return ["/" + m + "/" if m != "." else "/" for m in valda]


# ─── UPLOAD.txt ─────────────────────────────────────────────────────────────

@dataclass
class Upload:
    version: str = None
    datum: str = None
    summor: dict = field(default_factory=dict)
    must: set = field(default_factory=set)
    varningar: list = field(default_factory=list)


def las_upload(text, filer):
    up = Upload()
    m = re.search(r"built (\d{4}-\d{2}-\d{2}), \w+ v(\d+\.\d+\.\d+)", text)
    if m:
        up.datum, up.version = m.groups()
    else:
        up.varningar.append("Hittar inte 'built <datum>, … v<version>' i UPLOAD.txt")
    senaste, i_must = None, False
    for rad in text.splitlines():
        rubrik = re.match(r"^\s*\d+\.\s+(.*)", rad)
        if rubrik:
            i_must = "MUST" in rubrik.group(1)
        namnda = [f for f in filer if f in rad]
        if i_must:
            up.must.update(namnda)
        if namnda and re.search(r"curl|Invoke-WebRequest", rad):
            senaste = max(namnda, key=len)
        for h in HEX_I_RAD.findall(rad):
            if namnda:
                up.summor[max(namnda, key=len)] = h
            elif HEX64.match(rad) and senaste:
                up.summor[senaste] = h
            else:
                up.varningar.append(f"Kontrollsumma utan fil i UPLOAD.txt: {h[:12]}…")
    for f in sorted(up.must - set(up.summor)):
        up.varningar.append(f"MUST-fil utan kontrollsumma i UPLOAD.txt: {f}")
    return up


# ─── Plan ───────────────────────────────────────────────────────────────────

@dataclass
class Post:
    kalla: str
    adress: str
    mal: str
    spar: str
    status: str
    summa: str = None
    must: bool = False


@dataclass
class Plan:
    version: str = None
    datum: str = None
    poster: list = field(default_factory=list)
    facit: list = field(default_factory=list)
    saknas: list = field(default_factory=list)
    utan_adress: list = field(default_factory=list)
    overblivna: list = field(default_factory=list)
    regler_anvanda: bool = False
    rotmappar: list = field(default_factory=list)
    varningar: list = field(default_factory=list)
    stopp: list = field(default_factory=list)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _leveransfiler(ingest):
    ut = []
    for p in sorted(ingest.rglob("*")):
        rel = p.relative_to(ingest).as_posix()
        if p.is_file() and not rel.startswith("_importerat/") and rel not in STYRFILER and p.name != ".gitkeep":
            ut.append(rel)
    return ut


def _katalog(ingest, site, facit):
    for kalla in (ingest / "simulationsmcp/v1/modeling_guides.json", site / "simulationsmcp/v1/modeling_guides.json"):
        if kalla.is_file():
            return guider.Katalog(json.loads(kalla.read_text(encoding="utf-8")), facit)
    return guider.Katalog({"scenarios": {}, "categories": {}}, facit)


def planera(ingest, site, innehall, regler):
    ingest, site, innehall = Path(ingest), Path(site), Path(innehall)
    plan = Plan()
    if not (ingest / "urls.json").is_file():
        plan.stopp.append("urls.json saknas – det här är ingen leverans")
        return plan
    radata = json.loads((ingest / "urls.json").read_text(encoding="utf-8"))
    plan.facit = [skriv_om(a, regler) for a in radata]
    plan.regler_anvanda = any(skriv_om(a, regler) != a for a in radata)
    plan.rotmappar = rotmappar(plan.facit)
    tillatna = las_tillatna()
    for rm in plan.rotmappar:
        if not any(rm.startswith(t) for t in tillatna):
            plan.stopp.append(f"Rotmapp {rm} ligger utanför tillåtna {tillatna} – den skulle stängas i robots.txt")
    filer = _leveransfiler(ingest)

    if (ingest / "UPLOAD.txt").is_file():
        up = las_upload((ingest / "UPLOAD.txt").read_text(encoding="utf-8"), set(filer))
    else:
        up = Upload(varningar=["UPLOAD.txt saknas"])
    plan.version, plan.datum = up.version, up.datum
    plan.varningar += up.varningar

    facit = set(plan.facit)
    katalog = _katalog(ingest, site, plan.facit)
    for rel in filer:
        adress = skriv_om(adress_for_fil(rel), regler)
        if adress not in facit:
            plan.utan_adress.append(rel)
            plan.stopp.append(f"Fil utan adress i urls.json: {rel}")
            continue
        mal = fil_for_adress(adress)
        data = (ingest / rel).read_bytes()
        befintlig = site / mal
        if not rel.endswith(".html"):
            spar = "kopia"
            status = "ny" if not befintlig.is_file() else ("oforandrad" if befintlig.read_bytes() == data else "andrad")
        else:
            text = data.decode("utf-8")
            if guider.ar_guide(text):
                spar = "guide"
                try:
                    ny = guider.konvertera(text, adress, katalog, lambda a: skriv_om(a, regler))
                except guider.OkandStruktur as e:
                    plan.stopp.append(f"Guiden kan inte konverteras: {e}")
                    ny = None
                gammal = innehall / mal
                status = ("ny" if not gammal.is_file()
                          else "oforandrad" if ny is not None and gammal.read_text(encoding="utf-8") == ny
                          else "andrad")
            else:
                spar, status = "sida", ("finns" if befintlig.is_file() else "ny")
        summa = up.summor.get(rel)
        if summa and _sha(data) != summa:
            plan.stopp.append(f"Fel kontrollsumma för {rel}: {_sha(data)[:12]}… ≠ UPLOAD.txt {summa[:12]}…")
        plan.poster.append(Post(rel, adress, mal, spar, status, summa, rel in up.must))

    hanterade = {p.adress for p in plan.poster}
    plan.saknas = [a for a in plan.facit if a not in hanterade and not (site / fil_for_adress(a)).is_file()]
    mal_i_facit = {fil_for_adress(a) for a in plan.facit}
    for rm in plan.rotmappar:
        mapp = site / rm.strip("/")
        if mapp.is_dir():
            for p in sorted(mapp.rglob("*")):
                rel = p.relative_to(site).as_posix()
                if p.is_file() and rel not in mal_i_facit:
                    plan.overblivna.append(rel)
    return plan


def beskriv(plan):
    rader = [f"Leverans: version {plan.version or '?'}, byggd {plan.datum or '?'}"]
    for spar, namn in (("kopia", "Exakta kopior"), ("guide", "Guider"), ("sida", "Vanliga sidor (hanteras med omdöme)")):
        poster = [p for p in plan.poster if p.spar == spar]
        if not poster:
            continue
        rakna = {s: sum(p.status == s for p in poster) for s in ("ny", "andrad", "oforandrad", "finns")}
        rader.append(f"\n{namn}: {len(poster)} st – " + ", ".join(f"{k} {v}" for k, v in rakna.items() if v))
        for p in sorted(poster, key=lambda p: (not p.must, p.mal)):
            extra = (" MUST" if p.must else "") + (f" sha256 {p.summa[:12]}…" if p.summa else "")
            rader.append(f"  [{p.status}] {p.kalla} → site/{p.mal}{extra}")
    rader.append("\nAdressregel /guides/ → /simulationsmcp/v1/guides/: " + ("användes" if plan.regler_anvanda else "regeln användes inte"))
    rader.append("Dolt för robotar: " + ", ".join(plan.rotmappar))
    for rubrik, lista in (("Saknas (i facit men varken levererad eller i site/)", plan.saknas),
                          ("Överblivna i site/ (inte i facit – tas INTE bort)", plan.overblivna),
                          ("Varningar", plan.varningar), ("STOPP", plan.stopp)):
        if lista:
            rader.append(f"\n{rubrik}:")
            rader += [f"  - {x}" for x in lista]
    return "\n".join(rader)


# ─── Bygg ───────────────────────────────────────────────────────────────────

def sakra_robots(site, rotmappar):
    fil = Path(site) / "robots.txt"
    text = fil.read_text(encoding="utf-8") if fil.is_file() else ""
    nya = [m for m in rotmappar if f"Disallow: {m}" not in text]
    if not nya:
        return False
    block = []
    for m in nya:
        block += ["User-agent: *", f"Disallow: {m}", ""]
        block += [f"User-agent: {r}" for r in AI_ROBOTAR] + [f"Disallow: {m}", ""]
    ny = (text.rstrip("\n") + "\n\n" if text.strip() else "") + "\n".join(block)
    fil.write_bytes(ny.encode("utf-8"))
    return True


def bygg(plan, ingest, site, innehall):
    ingest, site, innehall = Path(ingest), Path(site), Path(innehall)
    if plan.stopp:
        raise RuntimeError("Planen har STOPP – bygger inte:\n" + "\n".join(plan.stopp))
    regler = las_regler()
    katalog = _katalog(ingest, site, plan.facit)
    byggda = []
    for p in plan.poster:
        if p.spar == "kopia":
            ut = site / p.mal
            ut.parent.mkdir(parents=True, exist_ok=True)
            ut.write_bytes((ingest / p.kalla).read_bytes())
            byggda.append(p.mal)
        elif p.spar == "guide":
            text = guider.konvertera((ingest / p.kalla).read_text(encoding="utf-8"), p.adress, katalog, lambda a: skriv_om(a, regler))
            fil = innehall / p.mal
            fil.parent.mkdir(parents=True, exist_ok=True)
            fil.write_bytes(text.encode("utf-8"))
            subprocess.run(["pwsh", "-NoProfile", "-File", str(MALL / "bygg-sida.ps1"), "-Innehall", str(fil),
                            "-Sokvag", p.mal, "-Ut", str(site)], check=True, capture_output=True)
            byggda.append(p.mal)
    sakra_robots(site, plan.rotmappar)
    return byggda


# ─── Kontroll ───────────────────────────────────────────────────────────────

def _inlankar(site, rotmappar):
    fel = []
    for f in sorted(Path(site).rglob("*.html")):
        rel = f.relative_to(site).as_posix()
        if any(("/" + rel).startswith(rm) for rm in rotmappar):
            continue
        for href in re.findall(r'href="([^"]*)"', f.read_text(encoding="utf-8")):
            if EXTERNT.match(href):
                continue
            vag = unquote(urlsplit(urljoin("/" + rel, href)).path)
            if any(vag.startswith(rm) or vag + "/" == rm for rm in rotmappar):
                fel.append(f"{rel} länkar in i dolda delen: {href}")
    return fel


def git_binar(repo, vag):
    """True om git aldrig ändrar radslut i filen (attributet text är unset)."""
    r = subprocess.run(["git", "-C", str(repo), "check-attr", "text", "--", vag], capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip().endswith(": text: unset")


def kontrollera(plan, ingest, site, webblasare=True):
    ingest, site = Path(ingest), Path(site)
    fel = []
    for a in plan.facit:
        if not (site / fil_for_adress(a)).is_file():
            fel.append(f"Adressen {a} saknas i site/ ({fil_for_adress(a)})")
    for p in plan.poster:
        if p.spar != "kopia":
            continue
        ut = site / p.mal
        if not ut.is_file() or ut.read_bytes() != (ingest / p.kalla).read_bytes():
            fel.append(f"{p.mal} är inte byte-identisk med leveransen")
        elif p.summa and _sha(ut.read_bytes()) != p.summa:
            fel.append(f"{p.mal}: kontrollsumman stämmer inte med UPLOAD.txt")
        try:
            i_repo = ut.resolve().relative_to(ROT).as_posix()
        except ValueError:
            i_repo = None
        if i_repo and not git_binar(ROT, i_repo):
            fel.append(f"{i_repo}: git kan ändra radslut (lägg sökvägen som -text i .gitattributes)")
    fel += _inlankar(site, plan.rotmappar)
    robots = (site / "robots.txt").read_text(encoding="utf-8") if (site / "robots.txt").is_file() else ""
    for rm in plan.rotmappar:
        if f"Disallow: {rm}" not in robots:
            fel.append(f"robots.txt stänger inte {rm}")
    for f in sorted(site.rglob("*.html")):
        if "[object Object]" in f.read_text(encoding="utf-8"):
            fel.append(f"{f.relative_to(site).as_posix()} innehåller [object Object]")
    guidemal = [p.mal for p in plan.poster if p.spar == "guide"]
    for mal in guidemal:
        if '<meta name="robots" content="noindex, nofollow">' not in (site / mal).read_text(encoding="utf-8"):
            fel.append(f"{mal} saknar noindex")
    if webblasare and guidemal:
        from verifiera import verifiera
        for mal in guidemal:
            fel += [f"{mal}: {f}" for f in verifiera(site, mal, None, None, forvantat_sprak="en")]
    return fel


def deploy_noter(plan):
    must = [p for p in plan.poster if p.must]
    rader = ["Deploy (görs av dig):",
             "  - Ladda upp hela site/ med mappstrukturen. Filer som inte är HTML i BINÄRT läge."]
    if must:
        rader.append("  - MUST före nästa serverrelease: " + ", ".join(p.mal for p in must))
    for p in plan.poster:
        if p.summa:
            rader.append(f"  - curl -s https://duke.se/{p.mal} | sha256sum   # = {p.summa}")
        if p.spar == "kopia":
            rader.append(f"  - curl -sI https://duke.se/{p.mal}   # 200, ingen Location:")
    rader.append("  - curl -sI https://duke.se/simulationsmcp.html   # produktsidan orörd (krockrisk med mappen simulationsmcp/)")
    return "\n".join(rader)


# ─── Arkiv ──────────────────────────────────────────────────────────────────

def arkivera(ingest, datum):
    ingest = Path(ingest)
    arkiv = ingest / "_importerat" / datum
    n = 2
    while arkiv.exists():
        arkiv = ingest / "_importerat" / f"{datum}-{n}"
        n += 1
    arkiv.mkdir(parents=True)
    for p in list(ingest.iterdir()):
        if p.name in ("_importerat", ".gitkeep"):
            continue
        shutil.move(str(p), str(arkiv / p.name))
    return arkiv


# ─── CLI ────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description="Ingest av leveranser (UPLOAD.txt + urls.json).")
    ap.add_argument("steg", choices=["plan", "bygg", "kontrollera", "arkivera"])
    ap.add_argument("--ingest", type=Path, default=ROT / "ingest")
    ap.add_argument("--site", type=Path, default=ROT / "site")
    ap.add_argument("--innehall", type=Path, default=MALL / "innehall")
    ap.add_argument("--utan-webblasare", action="store_true")
    ap.add_argument("--datum", default=datetime.date.today().isoformat())
    a = ap.parse_args(argv)
    if a.steg == "arkivera":
        print(f"Arkiverad till {arkivera(a.ingest, a.datum)}")
        return 0
    plan = planera(a.ingest, a.site, a.innehall, las_regler())
    if a.steg == "plan":
        print(beskriv(plan))
        return 1 if plan.stopp else 0
    if a.steg == "bygg":
        if plan.stopp:
            print(beskriv(plan))
            return 1
        for m in bygg(plan, a.ingest, a.site, a.innehall):
            print(f"byggd: site/{m}")
        sidor = [p.kalla for p in plan.poster if p.spar == "sida"]
        if sidor:
            print("Vanliga sidor att hantera med omdöme (SKILL steg 2–5): " + ", ".join(sidor))
        return 0
    if plan.stopp:
        print(beskriv(plan))
        print("Kan inte kontrollera: planen har STOPP (ingen eller trasig leverans i ingest/).")
        return 1
    fel = kontrollera(plan, a.ingest, a.site, webblasare=not a.utan_webblasare)
    for f in fel:
        print("FEL:", f)
    print("OK" if not fel else f"{len(fel)} fel")
    print("\n" + deploy_noter(plan))
    return 1 if fel else 0


if __name__ == "__main__":
    sys.exit(main())
