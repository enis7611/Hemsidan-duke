# Ingest av leveranser – implementationsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/ingest` ska kunna ta emot en leverans (`UPLOAD.txt` + `urls.json` + material). JSON-filer kopieras byte för byte. Guidesidor konverteras deterministiskt till Duke-design under `/simulationsmcp/v1/guides/`, dolda för sökrobotar. Allt kontrolleras mot facit.

**Architecture:**
- `mall/leverans.py` är motorn, med underkommandona `plan`, `bygg`, `kontrollera` och `arkivera`. Den läser styrfilerna, skriver om adresser enligt `mall/adressregler.json`, parar ihop filer med adresser, klassar filer (kopia/guide/sida), bygger och kontrollerar.
- `mall/guider.py` översätter generatorns HTML till innehållsfiler.
- `mall/bygg-sida.ps1` lär sig undersidor i mappar (`{{ROOT}}`), `lang: en` och `robots:`.
- `mall/verifiera.py` lär sig `/`-länkar, länkar som slutar med `/` och kontroll av EN-start.
- Skillen styr flödet och stannar för godkännande.

**Tech Stack:** Python 3.13 stdlib (`html.parser`, `hashlib`, `json`) + Playwright (finns), PowerShell 7. Inga nya beroenden. Testerna är fristående skript med asserts (samma stil som idag).

**Spec:** `docs/superpowers/specs/2026-09-26-ingest-leveranser-design.md` (bygger på `2026-09-23-ingest-arbetsflode-design.md`).

## Global Constraints

- Adressregel: `/guides/` → `/simulationsmcp/v1/guides/`. En adress som redan börjar med `/simulationsmcp/v1/guides/` lämnas orörd.
- JSON- och andra icke-HTML-filer kopieras **byte för byte**. Kontrollsumman (sha256) ska stämma mot `UPLOAD.txt`.
- Guider: innehållet bara på engelska (inga `data-sv`/`data-en` i guidetext). Ramen (header, footer, K10 CTA) är tvåspråkig. Sidan startar i EN-läge och har `<meta name="robots" content="noindex, nofollow">`.
- Ingen sida utanför `/simulationsmcp/v1/` får länka dit.
- `site/robots.txt` stänger `/simulationsmcp/v1/` för `*` och för GPTBot, ClaudeBot, CCBot, Google-Extended, PerplexityBot och Bytespider.
- Befintliga sidor (`extendmqtt`, `simulationsmcp`, `simulationsmcp-build`) ska byggas **byte-identiskt** efter mallens ändringar.
- Filer: UTF-8 utan BOM, LF. `.gitattributes`: `*.json -text`.
- Mapp- och filnamn i `site/`: segment `^[a-z0-9-]+$`, fil `^[a-z0-9-]+\.html$`. `index.html` är tillåten i undermappar, aldrig i roten.
- Borttagning sker aldrig automatiskt. Ingen commit i själva ingest-flödet.
- Plattform: Windows 11, `pwsh`, `python`. Sätt `PYTHONIOENCODING=utf-8` vid körning från bash.

## Review Focus

1. **JSON genom git med `core.autocrlf=true`:** kontrollsumman måste hålla efter commit och utcheckning. Testas i Task 1 (`git check-attr`) och Task 4 (kontrollsumma mot fixturen i git).
2. **Befintliga rotsidor efter platshållarna `{{ROOT}}`, `{{LANG}}`, `{{ROBOTS}}` och `{{EN_START}}`:** de ska fortfarande vara byte-identiska. Testas i Task 1.
3. **Header- och footerlänkar på nivå 3 och 4:** `index.html#mcp` måste bli `../../../index.html#mcp` och faktiskt fungera. Testas i Task 1 (sträng) och Task 2 (verifieraren löser upp länken).
4. **Leverans med bara några ändrade filer:** en adress i facit utan fil i leveransen, men som redan finns i `site/`, är inte "saknas". Testas i Task 4.
5. **Källan rättad** (adresserna kommer redan som `/simulationsmcp/v1/guides/`): regeln ska inte göra något och planen ska säga "regeln användes inte". Testas i Task 4.

---

## Filstruktur

| Fil | Ansvar |
|---|---|
| `.gitattributes` | + `*.json -text` |
| `mall/prefix.html`, `mall/suffix.html` | + `{{ROOT}}`, `{{LANG}}`, `{{ROBOTS}}`, `{{EN_START}}` |
| `mall/bygg-sida.ps1` | + `-Sokvag`, undermappar, nya metadatarader |
| `mall/verifiera.py` | + `/`-länkar, länkar som slutar med `/`, `%`-avkodning, relativa länkar från undermapp, `forvantat_sprak` |
| `mall/guider.py` | Generatorns HTML → innehållsfil |
| `mall/leverans.py` | Manifest, regler, plan, bygg, kontroll, arkiv (CLI + API) |
| `mall/adressregler.json` | Omskrivningsregler |
| `mall/test/fixtures/leverans-2026-09-26/` | Kopia av dagens leverans (testdata) |
| `mall/test/test_guider.py`, `mall/test/test_leverans.py` | Nya tester |
| `mall/test/test-bygg-sida.ps1`, `mall/test/test_verifiera.py` | Utökade tester |
| `.claude/skills/ingest/SKILL.md` | + leveransflödet |
| `mall/komponenter.md`, `CLAUDE.md`, `docs/HANDOFF_CONTEXT.md` | Dokumentation |

---

### Task 1: Mall och byggskript för undersidor i mappar, `lang` och `robots`

**Files:**
- Modify: `.gitattributes`, `mall/prefix.html`, `mall/suffix.html`, `mall/bygg-sida.ps1`
- Create: `mall/test/fixtures/leverans-2026-09-26/` (kopia av `ingest/` utan `_importerat`)
- Test: `mall/test/test-bygg-sida.ps1`

**Interfaces:**
- Produces:
  - `pwsh -File mall/bygg-sida.ps1 -Innehall <fil> [-Sokvag <rel/sökväg.html>] [-Ut <katalog>]`.
    - `-Sokvag` anger utfilens väg relativt `-Ut`, till exempel `simulationsmcp/v1/guides/queuing/index.html`.
    - Utan `-Sokvag` gäller: om filen ligger under `mall/innehall/` används vägen relativt den mappen, annars filnamnet.
    - Skriptet skriver ut utfilens sökväg.
  - Innehållsfilens metadata, där `lang` och `robots` är valfria och i den ordningen, före `page-css:`:
    ```
    <!--
    title: …
    description: …
    lang: en
    robots: noindex, nofollow
    page-css:
    <css-rader>
    -->
    ```

- [ ] **Step 1: Lås JSON i git och kopiera fixturen**

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
printf '*.json -text\n' >> .gitattributes
git check-attr text -- ingest/simulationsmcp/v1/modeling_guides.json   # förväntat: "text: unset"
mkdir -p mall/test/fixtures/leverans-2026-09-26
cp -r ingest/UPLOAD.txt ingest/urls.json ingest/guides ingest/simulationsmcp mall/test/fixtures/leverans-2026-09-26/
sha256sum mall/test/fixtures/leverans-2026-09-26/simulationsmcp/v1/modeling_guides.json   # a923b679…d207425
```

- [ ] **Step 2: Skriv de fallerande testerna**

Lägg till i `mall/test/test-bygg-sida.ps1`, före raden `Remove-Item -Recurse -Force $tmp`:

```powershell
# 10. Undersida i mapp: header-/footerlänkar får ../ per nivå, filen hamnar i rätt mapp
$p = Skriv 'djup.html' $giltig
& $bygg -Innehall $p -Sokvag 'a/b/c/index.html' -Ut $ut | Out-Null
$s = [IO.File]::ReadAllText((Join-Path $ut 'a\b\c\index.html'))
Ok ($s.Contains('href="../../../index.html#mcp"')) "nivå 3: länk till startsidan får ../../../"
Ok (-not ($s -match 'href="index\.html#')) "nivå 3: inga länkar kvar relativt fel mapp"
Ok ($s.Contains('<html lang="sv">')) "utan lang-rad: lang=sv"
Ok (-not $s.Contains('name="robots"')) "utan robots-rad: ingen robots-meta"
Ok (-not $s.Contains('{{')) "inga platshållare kvar (nivå 3)"

# 11. lang: en + robots → <html lang="en">, robots-meta, EN-start
$en = "<!--`ntitle: Guide`ndescription: Beskrivning`nlang: en`nrobots: noindex, nofollow`npage-css:`n-->`n<section>Hi</section>`n"
$p = Skriv 'guide.html' $en
& $bygg -Innehall $p -Sokvag 'g/index.html' -Ut $ut | Out-Null
$s = [IO.File]::ReadAllText((Join-Path $ut 'g\index.html'))
Ok ($s.Contains('<html lang="en">')) "lang: en ger <html lang=`"en`">"
Ok ($s.Contains("<title>Guide</title>`n<meta name=`"robots`" content=`"noindex, nofollow`">")) "robots-meta direkt efter title"
Ok ($s.Contains("<script>toggleLang();</script>`n</body>")) "EN-start före </body>"
Ok ($s.Contains('<section>Hi</section>')) "innehåll med lang/robots-rader på plats"

# 12. Otillåtna värden och sökvägar
$p = Skriv 'fellang.html' ($en.Replace('lang: en', 'lang: de'))
Kastar { & $bygg -Innehall $p -Sokvag 'x.html' -Ut $ut } "lang annat än sv/en avvisas"
$p = Skriv 'ok.html' $giltig
Kastar { & $bygg -Innehall $p -Sokvag 'Guides/x.html' -Ut $ut } "mappnamn med versal avvisas"
Kastar { & $bygg -Innehall $p -Sokvag 'a/../x.html' -Ut $ut } "'..' i sökväg avvisas"
Kastar { & $bygg -Innehall $p -Sokvag 'index.html' -Ut $ut } "index.html i roten avvisas via -Sokvag"
& $bygg -Innehall $p -Sokvag 'sub/index.html' -Ut $ut | Out-Null
Ok (Test-Path (Join-Path $ut 'sub\index.html')) "index.html i undermapp tillåts"
```

- [ ] **Step 3: Kör och se dem fallera**

Run: `pwsh -File mall/test/test-bygg-sida.ps1`
Expected: FEL på punkterna 10–12 (`-Sokvag` är okänd parameter). Punkterna 1–9 är fortfarande OK.

- [ ] **Step 4: Lägg in platshållarna i mallen**

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
python - <<'EOF'
from pathlib import Path
p = Path('mall/prefix.html'); s = p.read_bytes().decode('utf-8')
assert s.count('<html lang="sv">') == 1 and s.count('<title>{{TITLE}}</title>') == 1
s = s.replace('<html lang="sv">', '<html lang="{{LANG}}">').replace('<title>{{TITLE}}</title>', '<title>{{TITLE}}</title>{{ROBOTS}}')
s = s.replace('href="index.html', 'href="{{ROOT}}index.html')
p.write_bytes(s.encode('utf-8'))
p = Path('mall/suffix.html'); s = p.read_bytes().decode('utf-8')
assert s.endswith('</script>\n</body>\n</html>\n')
s = s.replace('href="index.html', 'href="{{ROOT}}index.html')
s = s[:-len('</body>\n</html>\n')] + '{{EN_START}}</body>\n</html>\n'
p.write_bytes(s.encode('utf-8'))
EOF
grep -c '{{ROOT}}' mall/prefix.html mall/suffix.html   # 14 resp. 13 rader
```

- [ ] **Step 5: Uppdatera `mall/bygg-sida.ps1`**

Ersätt parametrarna och allt från `$namn = [IO.Path]::GetFileName($Innehall)` till och med `$css = …` samt slutet av filen med följande. Funktionen `Las-Lf` och mojibake-kontrollen behålls oförändrade, och mojibake-kontrollen ligger kvar direkt efter `$raw = Las-Lf $Innehall`:

```powershell
param(
  [Parameter(Mandatory)][string]$Innehall,
  [string]$Sokvag,
  [string]$Ut = (Join-Path $PSScriptRoot '..\site')
)
```

```powershell
# Utfilens väg relativt -Ut: -Sokvag, annars vägen under mall/innehall/, annars filnamnet.
if (-not $Sokvag) {
  $innehallRot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'innehall')) + [IO.Path]::DirectorySeparatorChar
  $full = [IO.Path]::GetFullPath($Innehall)
  $Sokvag = if ($full.StartsWith($innehallRot, [StringComparison]::OrdinalIgnoreCase)) { $full.Substring($innehallRot.Length) } else { [IO.Path]::GetFileName($full) }
}
$Sokvag = $Sokvag.Replace('\', '/')
if ($Sokvag -eq 'index.html') { throw 'index.html i roten är handredigerad och byggs aldrig av bygg-sida.ps1' }
$delar = $Sokvag.Split('/')
$namn = $delar[-1]
foreach ($d in ($delar | Select-Object -SkipLast 1)) {
  if ($d -cnotmatch '^[a-z0-9-]+$') { throw "Otillåtet mappnamn '$d' i '$Sokvag': bara a-z, 0-9 och bindestreck" }
}
if ($namn -cnotmatch '^[a-z0-9-]+\.html$') { throw "Otillåtet filnamn '$namn': bara a-z, 0-9 och bindestreck (å/ä/ö → a/a/o)" }
$rotvag = '../' * ($delar.Count - 1)
```

```powershell
$raw = Las-Lf $Innehall
# (mojibake-kontrollen står kvar här, oförändrad)
if (-not $raw.StartsWith("<!--`n")) { throw "Innehållsfilen saknar metadata-kommentar överst: $Innehall" }
$slut = $raw.IndexOf("`n-->`n")
if ($slut -lt 5) { throw "Metadata-kommentaren stängs inte med en egen rad '-->': $Innehall" }
$huvud = $raw.Substring(5, $slut - 5).Split("`n")
$kropp = $raw.Substring($slut + 5)

if ($huvud.Count -lt 3 -or -not $huvud[0].StartsWith('title:') -or -not $huvud[1].StartsWith('description:')) {
  throw "Metadata måste börja med raderna 'title:' och 'description:': $Innehall"
}
$titel = $huvud[0].Substring(6).Trim()
$beskr = $huvud[1].Substring(12).Trim()
if (-not $titel) { throw "title saknar värde: $Innehall" }
if (-not $beskr) { throw "description saknar värde: $Innehall" }
if ($beskr.Contains('"')) { throw ('description får inte innehålla citattecken ("): ' + $Innehall) }

# Valfria rader före page-css:, i ordningen lang, robots
$lang = 'sv'; $robots = ''
$i = 2
if ($huvud[$i] -and $huvud[$i].StartsWith('lang:')) { $lang = $huvud[$i].Substring(5).Trim(); $i++ }
if ($huvud[$i] -and $huvud[$i].StartsWith('robots:')) { $robots = $huvud[$i].Substring(7).Trim(); $i++ }
if ($lang -cnotin 'sv', 'en') { throw "lang måste vara sv eller en (fick '$lang'): $Innehall" }
if ($robots -and $robots -cnotmatch '^[a-z]+(, ?[a-z]+)*$') { throw "Ogiltigt robots-värde '$robots': $Innehall" }
if ($huvud[$i] -ne 'page-css:') { throw "Metadata: efter title/description (och ev. lang, robots) ska raden 'page-css:' komma: $Innehall" }
$cssRader = if ($huvud.Count -gt $i + 1) { $huvud[($i + 1)..($huvud.Count - 1)] } else { @() }
$css = if (($cssRader -join '').Trim()) { ($cssRader -join "`n") + "`n" } else { '' }

$robotsMeta = if ($robots) { "`n<meta name=`"robots`" content=`"$robots`">" } else { '' }
$enStart = if ($lang -eq 'en') { "<script>toggleLang();</script>`n" } else { '' }

# String.Replace är ordagrann (ingen regex). TITLE sist så att en titel med "{{…}}" aldrig tolkas.
$prefix = (Las-Lf (Join-Path $PSScriptRoot 'prefix.html')).Replace('{{PAGE_CSS}}', $css).Replace('{{ROOT}}', $rotvag).Replace('{{LANG}}', $lang).Replace('{{ROBOTS}}', $robotsMeta).Replace('{{DESCRIPTION}}', $beskr).Replace('{{TITLE}}', $titel)
$suffix = (Las-Lf (Join-Path $PSScriptRoot 'suffix.html')).Replace('{{ROOT}}', $rotvag).Replace('{{EN_START}}', $enStart)

New-Item -ItemType Directory -Force $Ut | Out-Null
$utfil = Join-Path (Resolve-Path $Ut).Path ($Sokvag.Replace('/', [IO.Path]::DirectorySeparatorChar))
New-Item -ItemType Directory -Force (Split-Path $utfil) | Out-Null
[IO.File]::WriteAllText($utfil, $prefix + $kropp + $suffix, $utf8)
$utfil
```

Obs:
- `'..'` avvisas av mappnamnsregeln, eftersom punkt inte är tillåten.
- Kontrollen `$slut -lt 5` rättar granskningsfyndet om metadata som bara är `<!--\n-->` och tidigare gav ett rått .NET-fel.

- [ ] **Step 6: Kör testerna och se dem passera**

Run: `pwsh -File mall/test/test-bygg-sida.ps1`
Expected: alla OK, inklusive punkt 1 (de tre befintliga sidorna byggs fortfarande byte-identiskt). Sista raden är `Alla test OK`.

- [ ] **Step 7: Bygg om `site/` och kontrollera att inget ändrats**

```bash
for n in extendmqtt simulationsmcp simulationsmcp-build; do pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/$n.html >/dev/null; done
git status --short site/   # förväntat: tomt
```

- [ ] **Step 8: Commit**

```bash
git add .gitattributes mall/prefix.html mall/suffix.html mall/bygg-sida.ps1 mall/test/test-bygg-sida.ps1 mall/test/fixtures/leverans-2026-09-26
git commit -m "Byggskript: undersidor i mappar, lang och robots; testfixtur för leverans"
```

---

### Task 2: `verifiera.py` för sidor i mappar och EN-start

**Files:**
- Modify: `mall/verifiera.py`
- Test: `mall/test/test_verifiera.py`

**Interfaces:**
- Consumes: `bygg-sida.ps1 -Sokvag` (Task 1).
- Produces:
  - `verifiera(rot, sida, fran=None, skarmdumpar=None, forvantat_sprak=None) -> list[str]`, där `sida` får vara en sökväg (`a/b/index.html`).
  - CLI: `--sprak en`.
  - Skärmdumpsnamnet: sökvägen med `/` → `_` utan `.html`, till exempel `a_b_index-sv-desktop.png`.

- [ ] **Step 1: Skriv de fallerande testerna**

Lägg till i `mall/test/test_verifiera.py`, före `print("Alla test OK" …`:

```python
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
```

- [ ] **Step 2: Kör och se dem fallera**

Run: `PYTHONIOENCODING=utf-8 python mall/test/test_verifiera.py`
Expected: `TypeError: verifiera() got an unexpected keyword argument 'forvantat_sprak'`.

- [ ] **Step 3: Implementera**

I `mall/verifiera.py`:

1. Lägg till importen `from urllib.parse import unquote, urlsplit` (ersätter `from urllib.parse import urlsplit`).
2. Ersätt `kontrollera_lankar` med:

```python
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
                finns = re.search(r'id=["\']%s["\']' % re.escape(delar.fragment), mal.read_text(encoding="utf-8")) is not None
            if not finns:
                fel.append(f"Länken {href} pekar på ett ankare som saknas")
    return fel
```

3. I `verifiera`, lägg till parametern `forvantat_sprak=None` sist. Byt `namn = Path(sida).stem` mot `namn = sida[:-5].replace("/", "_") if sida.endswith(".html") else sida.replace("/", "_")`. Lägg till direkt efter `page.goto(...)` på desktopsidan:

```python
            if forvantat_sprak and page.evaluate("document.documentElement.lang") != forvantat_sprak:
                fel.append(f"Sidan startar inte i {forvantat_sprak.upper()}-läge")
```

4. I mobildelen, ersätt `mobil.evaluate("toggleLang()")` med `mobil.evaluate("if (currentLang !== 'en') toggleLang()")`.
5. I `main`: `ap.add_argument("--sprak", choices=["sv", "en"], help="förväntat startspråk")`, och skicka `a.sprak` som `forvantat_sprak`.

- [ ] **Step 4: Kör testerna**

Run: `PYTHONIOENCODING=utf-8 python mall/test/test_verifiera.py`
Expected: alla OK, `Alla test OK`.

- [ ] **Step 5: Regressionskontroll av riktiga sidor**

```bash
export PYTHONIOENCODING=utf-8
python mall/verifiera.py extendmqtt.html --fran index.html      # OK
python mall/verifiera.py simulationsmcp-build.html               # OK
python mall/verifiera.py simulationsmcp.html | tail -1           # "3 fel" (kända <br>-fynd, oförändrat)
```

- [ ] **Step 6: Commit**

```bash
git add mall/verifiera.py mall/test/test_verifiera.py
git commit -m "verifiera.py: sidor i mappar, /-länkar och kontroll av startspråk"
```

---

### Task 3: Guidekonverteraren `mall/guider.py`

**Files:**
- Create: `mall/guider.py`
- Test: `mall/test/test_guider.py`

**Interfaces:**
- Consumes: fixturen (Task 1). Metadataformatet med `lang`/`robots` (Task 1).
- Produces:
  - `class OkandStruktur(Exception)`
  - `@dataclass Katalog(guider: dict, adresser: list[str])` med `scenario_id(adress) -> str|None` och `adress_for_scenario(sid) -> str|None`
  - `konvertera(html_text: str, adress: str, katalog: Katalog, skriv_om: Callable[[str], str]) -> str`, som returnerar hela innehållsfilen (metadata + kropp)
  - `ar_guide(html_text: str) -> bool`

- [ ] **Step 1: Skriv det fallerande testet** `mall/test/test_guider.py`

```python
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
```

- [ ] **Step 2: Kör och se det fallera**

Run: `PYTHONIOENCODING=utf-8 python mall/test/test_guider.py`
Expected: `ModuleNotFoundError: No module named 'guider'`.

- [ ] **Step 3: Skriv `mall/guider.py`**

```python
"""Konverterar generatorns guidesidor (<main class="guide-content">) till innehållsfiler för mall/bygg-sida.ps1.

Används av mall/leverans.py. Okänd struktur ger OkandStruktur – konverteraren gissar aldrig.
"""
import re
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
MORK_BG = "linear-gradient(160deg,#1B4F4F 0%,#1E5A5A 50%,#236060 100%)"
LJUSA_BG = ["var(--white)", "var(--bg)"]
TABELL_CSS = (
    "  .duke-table{width:100%;max-width:820px;margin:0 auto;border-collapse:collapse;font-size:0.92rem;}\n"
    "  .duke-table th{font-family:var(--mono);font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--teal);text-align:left;padding:0.75rem 1rem;border-bottom:2px solid var(--teal);}\n"
    "  .duke-table td{padding:0.75rem 1rem;border-bottom:1px solid var(--border);color:var(--navy);vertical-align:top;}\n"
    "  .duke-table tr:last-child td{border-bottom:none;}\n"
    "  .duke-table-wrap{overflow-x:auto;}\n"
)
CTA = (
    '<!-- ─── CTA ──────────────────────────────────────────────── -->\n'
    '<section style="background:linear-gradient(135deg,#1B4F4F 0%,#236060 50%,#287070 100%);padding:80px 0;text-align:center;">\n'
    '  <div class="container" style="position:relative;z-index:2;">\n'
    '    <h2 style="color:#fff;margin-bottom:1rem;" data-sv="Behöver du hjälp med din modell?" data-en="Need help with your model?">Behöver du hjälp med din modell?</h2>\n'
    '    <p style="color:rgba(255,255,255,0.75);max-width:480px;margin:0 auto 2.5rem;" data-sv="Duke Systems har arbetat med ExtendSim sedan 1988." data-en="Duke Systems has worked with ExtendSim since 1988.">Duke Systems har arbetat med ExtendSim sedan 1988.</p>\n'
    '    <a href="/index.html#kontakt" class="btn btn-primary" data-sv="Berätta om ditt problem" data-en="Tell us about your problem">Berätta om ditt problem</a>\n'
    '  </div>\n'
    '</section>\n\n'
)


class OkandStruktur(Exception):
    pass


class Nod:
    def __init__(self, tag, attrs=None):
        self.tag, self.attrs, self.barn = tag, dict(attrs or {}), []

    @property
    def klass(self):
        return self.attrs.get("class") or ""

    def text(self):
        delar = [b if isinstance(b, str) else b.text() for b in self.barn]
        return re.sub(r"\s+", " ", "".join(delar)).strip()

    def element(self):
        return [b for b in self.barn if isinstance(b, Nod)]

    def alla(self, tag):
        for b in self.element():
            if b.tag == tag:
                yield b
            yield from b.alla(tag)

    def forsta(self, tag, klass=None):
        return next((n for n in self.alla(tag) if klass is None or n.klass == klass), None)


class _Byggare(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rot = Nod("#rot")
        self.stack = [self.rot]

    def handle_starttag(self, tag, attrs):
        nod = Nod(tag, attrs)
        self.stack[-1].barn.append(nod)
        if tag not in VOID:
            self.stack.append(nod)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].barn.append(Nod(tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].barn.append(data)


def tolka(html_text):
    b = _Byggare()
    b.feed(html_text)
    b.close()
    return b.rot


def ar_guide(html_text):
    return tolka(html_text).forsta("main", "guide-content") is not None


@dataclass
class Katalog:
    guider: dict
    adresser: list

    def scenario_id(self, adress):
        """'/…/guides/queuing/simple-queue/' → 'simple_queue' om kategori och scenario finns i modeling_guides.json."""
        delar = [d for d in adress.split("/") if d]
        if len(delar) < 2:
            return None
        kat, sid = delar[-2], delar[-1].replace("-", "_")
        s = self.guider.get("scenarios", {}).get(sid)
        return sid if s and s.get("category") == kat else None

    def adress_for_scenario(self, sid):
        return next((a for a in self.adresser if self.scenario_id(a) == sid), None)


# ─── Komponenter (samma markup som mall/komponenter.md) ─────────────────────

def _hero(etikett, rubrik, sammanfattning, tillbaka):
    back = ""
    if tillbaka:
        href, text = tillbaka
        back = (f'    <a href="{escape(href)}" style="display:inline-flex;align-items:center;gap:0.4rem;font-family:var(--mono);'
                'font-size:0.72rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--steel-lt);text-decoration:none;'
                f'margin-bottom:1.5rem;">← {escape(text)}</a>\n')
    return (
        '<!-- ─── PRODUKT-HERO ─────────────────────────────────────── -->\n'
        '<section id="top" style="background:linear-gradient(135deg,#1B4F4F 0%,#236060 45%,#2d7a7a 100%);padding:140px 0 80px;position:relative;overflow:hidden;">\n'
        '  <div class="hero-grid-bg"></div>\n'
        '  <div class="hero-glow"></div>\n'
        '  <div class="container" style="position:relative;z-index:2;">\n'
        + back +
        '    <div style="display:inline-flex;align-items:center;gap:0.6rem;margin-bottom:1rem;flex-wrap:wrap;">\n'
        '      <span style="font-size:2rem;">🧭</span>\n'
        f'      <span class="section-label" style="color:var(--steel-lt);margin:0;">{escape(etikett)}</span>\n'
        '    </div>\n'
        f'    <h1 style="color:#fff;margin-bottom:1.25rem;">{escape(rubrik)}</h1>\n'
        + (f'    <p style="font-size:1.15rem;color:rgba(255,255,255,0.8);max-width:640px;">{escape(sammanfattning)}</p>\n'
           if sammanfattning else "") +
        '  </div>\n'
        '</section>\n\n'
    )


def _sektion(etikett, rubrik, inre, mork, ljus_bg):
    if mork:
        return (f'<section style="background:{MORK_BG};position:relative;overflow:hidden;">\n'
                '  <div class="mcp-bg-pattern"></div>\n'
                '  <div class="container" style="position:relative;z-index:2;">\n'
                '    <div class="section-header reveal">\n'
                f'      <span class="section-label" style="color:var(--teal);">{escape(etikett)}</span>\n'
                f'      <h2 style="color:#fff;">{escape(rubrik)}</h2>\n'
                '    </div>\n' + inre + '  </div>\n</section>\n\n')
    return (f'<section style="background:{ljus_bg};">\n'
            '  <div class="container">\n'
            '    <div class="section-header reveal">\n'
            f'      <span class="section-label">{escape(etikett)}</span>\n'
            f'      <h2 style="color:var(--navy);">{escape(rubrik)}</h2>\n'
            '    </div>\n' + inre + '  </div>\n</section>\n\n')


def _lista(punkter, ikon=None):
    stil = "margin-bottom:0.6rem;" + ("list-style:none;" if ikon else "")
    rader = "".join(f'      <li style="{stil}">{(ikon + " ") if ikon else ""}{escape(p)}</li>\n' for p in punkter)
    return ('    <ul class="reveal" style="max-width:720px;margin:0 auto;padding-left:1.2rem;line-height:1.7;color:var(--text);">\n'
            + rader + '    </ul>\n')


def _tabell(tabell):
    rubriker = [th.text() for th in tabell.alla("th")]
    rader = [r for r in ([td.text() for td in tr.alla("td")] for tr in tabell.alla("tr")) if r]
    thead = "<tr>" + "".join(f"<th>{escape(r)}</th>" for r in rubriker) + "</tr>"
    tbody = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in rad) + "</tr>" for rad in rader)
    return ('    <div class="duke-table-wrap reveal">\n'
            '      <table class="duke-table">\n'
            f'        <thead>{thead}</thead>\n'
            f'        <tbody>{tbody}</tbody>\n'
            '      </table>\n'
            '    </div>\n')


def _terminal(titel, rader):
    linjer = "".join(f'        <div class="terminal-line"><span class="terminal-result">{escape(r)}</span></div>\n' for r in rader)
    return ('    <div class="mcp-terminal reveal" style="background:rgba(0,0,0,0.4);max-width:720px;margin:0 auto;">\n'
            '      <div class="terminal-bar">\n'
            '        <div class="terminal-dot"></div><div class="terminal-dot"></div><div class="terminal-dot"></div>\n'
            f'        <span class="terminal-title">{escape(titel)}</span>\n'
            '      </div>\n'
            '      <div class="terminal-body">\n' + linjer +
            '      </div>\n'
            '    </div>\n')


def _pelare(punkter, ikon):
    kort = "".join(
        f'      <div class="pillar reveal reveal-delay-{i % 4 + 1}"><div style="font-size:1.8rem;margin-bottom:0.75rem;">{ikon}</div><p>{escape(p)}</p></div>\n'
        for i, p in enumerate(punkter))
    return '    <div class="pillars">\n' + kort + '    </div>\n'


def _kort(kort, ikon):
    rader = []
    for i, (rubrik, href, text) in enumerate(kort):
        h3 = (f'<a href="{escape(href)}" style="color:inherit;text-decoration:none;">{escape(rubrik)} →</a>'
              if href else escape(rubrik))
        rader.append(f'      <div class="service-card reveal reveal-delay-{i % 3 + 1}"><div class="card-icon teal">{ikon}</div>'
                     f'<h3>{h3}</h3><p>{escape(text)}</p></div>\n')
    return '    <div class="services-grid">\n' + "".join(rader) + '    </div>\n'


# ─── Konvertering ────────────────────────────────────────────────────────────

def _punkter(sektion):
    return [li.text() for li in sektion.alla("li")]


def konvertera(html_text, adress, katalog, skriv_om):
    rot = tolka(html_text)
    main = rot.forsta("main", "guide-content")
    if main is None:
        raise OkandStruktur(f'{adress}: saknar <main class="guide-content">')
    titel_nod = rot.forsta("title")
    titel = titel_nod.text() if titel_nod else ""
    if not titel:
        raise OkandStruktur(f"{adress}: saknar <title>")
    beskr_nod = next((m for m in rot.alla("meta") if m.attrs.get("name") == "description"), None)
    beskr = (beskr_nod.attrs.get("content") or "").strip() if beskr_nod else titel

    sid = katalog.scenario_id(adress)
    kategori = katalog.guider["categories"][katalog.guider["scenarios"][sid]["category"]]["label"] if sid else None

    rubrik, sammanfattning, tillbaka = None, "", None
    delar = []          # (mork: bool, etikett, rubrik, inre)
    kategorikort = []   # startsidans section.category samlas till ett kortrutnät
    har_tabell = False

    for el in main.element():
        k = el.klass
        h2 = el.forsta("h2")
        sektionsrubrik = h2.text() if h2 else ""
        if el.tag == "nav" and k == "breadcrumb":
            lankar = [(skriv_om(a.attrs.get("href") or ""), a.text()) for a in el.alla("a")]
            tillbaka = lankar[-1] if lankar else None
        elif el.tag == "h1":
            rubrik = el.text()
        elif el.tag == "p" and k == "summary":
            sammanfattning = el.text()
        elif el.tag == "section" and k == "use-when":
            delar.append((False, sektionsrubrik, _lista(_punkter(el))))
        elif el.tag == "section" and k in ("blocks", "key-parameters"):
            tabell = el.forsta("table")
            if tabell is None:
                raise OkandStruktur(f'{adress}: <section class="{k}"> saknar tabell')
            har_tabell = True
            delar.append((False, sektionsrubrik, _tabell(tabell)))
        elif el.tag == "section" and k == "connections":
            delar.append((True, sektionsrubrik, _terminal(sektionsrubrik, _punkter(el))))
        elif el.tag == "section" and k == "common-mistakes":
            delar.append((False, sektionsrubrik, _lista(_punkter(el), "⚠️")))
        elif el.tag == "section" and k == "key-metrics":
            delar.append((True, sektionsrubrik, _pelare(_punkter(el), "📊")))
        elif el.tag == "section" and k == "variations":
            if sid is None:
                raise OkandStruktur(f"{adress}: 'variations' på en sida som inte är ett scenario i modeling_guides.json")
            kort = []
            for v in katalog.guider["scenarios"][sid].get("variations", []):
                href = None
                if v.get("scenario"):
                    href = katalog.adress_for_scenario(v["scenario"])
                    if href is None:
                        raise OkandStruktur(f"{adress}: varianten '{v.get('name')}' pekar på scenario '{v['scenario']}' som saknar adress")
                kort.append((v.get("name", ""), href, v.get("change", "")))
            delar.append((False, sektionsrubrik, _kort(kort, "🔀")))
        elif el.tag == "section" and k == "category":
            a = h2.forsta("a") if h2 else None
            if a is None:
                raise OkandStruktur(f'{adress}: <section class="category"> saknar <h2><a>')
            guider = " · ".join(li.text() for li in el.alla("li"))
            kategorikort.append((a.text(), skriv_om(a.attrs.get("href") or ""), guider))
        elif el.tag == "section" and k == "guide-list":
            kort = []
            for li in el.alla("li"):
                a = li.forsta("a")
                if a is None:
                    raise OkandStruktur(f'{adress}: <section class="guide-list"> har <li> utan länk')
                text = li.text()[len(a.text()):].lstrip(" —-").strip()
                kort.append((a.text(), skriv_om(a.attrs.get("href") or ""), text))
            delar.append((False, "Guides", _kort(kort, "📘")))
        else:
            raise OkandStruktur(f'{adress}: okänt element <{el.tag} class="{k}">')

    if not rubrik:
        raise OkandStruktur(f"{adress}: saknar <h1>")
    if kategorikort:
        delar.insert(0, (False, "Categories", _kort(kategorikort, "📂")))

    etikett = kategori or (tillbaka[1] if tillbaka else "SimulationsMCP")
    kropp = _hero(etikett, rubrik, sammanfattning, tillbaka)
    nr_ljus = 0
    for mork, srubrik, inre in delar:
        kropp += _sektion(etikett, srubrik, inre, mork, LJUSA_BG[nr_ljus % 2])
        if not mork:
            nr_ljus += 1
    kropp += CTA

    meta = ("<!--\n"
            f"title: {escape(titel, quote=False)} | Duke Systems AB\n"
            f"description: {escape(beskr)}\n"
            "lang: en\n"
            "robots: noindex, nofollow\n"
            "page-css:\n"
            + (TABELL_CSS if har_tabell else "") +
            "-->\n")
    return meta + kropp
```

Obs:
- CTA-länken `/index.html#kontakt` är rot-absolut, eftersom guiderna ligger djupt. Den löses upp mot `--rot` i verifieraren (Task 2).
- `escape(beskr)` gör om `"` till `&quot;`, så bygg-sida vägrar inte.
- Alla sektioner är ljusa utom `connections` och `key-metrics`, som alltid omges av ljusa sektioner i generatorns ordning. Sista sektionen före CTA (`variations`) är ljus.

- [ ] **Step 4: Kör testet**

Run: `PYTHONIOENCODING=utf-8 python mall/test/test_guider.py`
Expected: alla OK, `Alla test OK`.

- [ ] **Step 5: Commit**

```bash
git add mall/guider.py mall/test/test_guider.py
git commit -m "guider.py: konverterar generatorns guidesidor till Duke-design"
```

---

### Task 4: Leveransmotorn `mall/leverans.py` + `adressregler.json` + `robots.txt`

**Files:**
- Create: `mall/leverans.py`, `mall/adressregler.json`
- Test: `mall/test/test_leverans.py`

**Interfaces:**
- Consumes:
  - `guider.konvertera`, `guider.ar_guide`, `guider.Katalog`, `guider.OkandStruktur` (Task 3)
  - `bygg-sida.ps1 -Innehall -Sokvag -Ut` (Task 1)
  - `verifiera.verifiera(..., forvantat_sprak=)` (Task 2)
- Produces:
  - CLI: `python mall/leverans.py plan|bygg|kontrollera|arkivera [--ingest DIR] [--site DIR] [--innehall DIR] [--utan-webblasare] [--datum ÅÅÅÅ-MM-DD]`. Exit 0 om OK, 1 om fel eller stopp.
  - API:
    - `planera(ingest, site, innehall, regler) -> Plan`
    - `bygg(plan, ingest, site, innehall) -> list[str]` (byggda målvägar)
    - `kontrollera(plan, ingest, site, webblasare=True) -> list[str]` (fel)
    - `arkivera(ingest, datum) -> Path`
    - `skriv_om(adress, regler) -> str`
    - `beskriv(plan) -> str`
  - `Plan`-fält: `version`, `datum`, `poster: list[Post]`, `facit: list[str]`, `saknas`, `utan_adress`, `overblivna`, `regler_anvanda: bool`, `rotmappar: list[str]` (t.ex. `["/simulationsmcp/v1/"]`), `varningar`, `stopp` (blockerande fel).
  - `Post`-fält: `kalla`, `adress`, `mal`, `spar` (`"kopia"|"guide"|"sida"`), `status` (`"ny"|"andrad"|"oforandrad"|"finns"`), `summa` (förväntad sha256 eller None), `must: bool`.

- [ ] **Step 1: Skriv `mall/adressregler.json`**

```json
{
  "prefix": [
    { "fran": "/guides/", "till": "/simulationsmcp/v1/guides/" }
  ]
}
```

- [ ] **Step 2: Skriv det fallerande testet** `mall/test/test_leverans.py`

```python
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
```

- [ ] **Step 3: Kör och se det fallera**

Run: `PYTHONIOENCODING=utf-8 python mall/test/test_leverans.py`
Expected: `ModuleNotFoundError: No module named 'leverans'`.

- [ ] **Step 4: Skriv `mall/leverans.py`**

```python
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
EXTERNT = re.compile(r"^(https?:|mailto:|tel:|javascript:|#)", re.I)
AI_ROBOTAR = ["GPTBot", "ClaudeBot", "CCBot", "Google-Extended", "PerplexityBot", "Bytespider"]


# ─── Adresser ────────────────────────────────────────────────────────────────

def las_regler(fil=MALL / "adressregler.json"):
    return json.loads(Path(fil).read_text(encoding="utf-8"))["prefix"]


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
        h = HEX64.match(rad)
        if h:
            if senaste:
                up.summor[senaste] = h.group(1)
            else:
                up.varningar.append(f"Kontrollsumma utan fil i UPLOAD.txt: {h.group(1)[:12]}…")
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
    fel = kontrollera(plan, a.ingest, a.site, webblasare=not a.utan_webblasare)
    for f in fel:
        print("FEL:", f)
    print("OK" if not fel else f"{len(fel)} fel")
    print("\n" + deploy_noter(plan))
    return 1 if fel else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Kör testet**

Run: `PYTHONIOENCODING=utf-8 python mall/test/test_leverans.py`
Expected: alla OK, `Alla test OK`.

- [ ] **Step 6: Kontroll i webbläsare av tre konverterade guider** (bevisar att verifieraren och konverteraren fungerar tillsammans)

```bash
export PYTHONIOENCODING=utf-8
T=$(mktemp -d) && cp -r site "$T/site" && cp -r mall/test/fixtures/leverans-2026-09-26 "$T/ingest" && mkdir "$T/innehall"
python mall/leverans.py bygg --ingest "$T/ingest" --site "$T/site" --innehall "$T/innehall" | tail -2
python mall/leverans.py kontrollera --ingest "$T/ingest" --site "$T/site" --innehall "$T/innehall" | head -5
for s in simulationsmcp/v1/guides/index.html simulationsmcp/v1/guides/queuing/index.html simulationsmcp/v1/guides/queuing/simple-queue/index.html; do
  python mall/verifiera.py "$s" --rot "$T/site" --sprak en --skarmdumpar "$T/dumpar"; done
ls "$T/dumpar"
```
Expected: `kontrollera` skriver `OK`. Varje `verifiera` skriver `OK`. Sex skärmdumpar finns.

Öppna `…simple-queue_index-sv-desktop.png` och `…-en-mobil.png` med Read-verktyget. Kontrollera:
- att sidan ser ut som en produktsida
- att tabellerna inte spräcker mobilbredden
- att terminalen syns i mörk sektion
- att varianterna är kort med länkar

Om något ser fel ut: rätta markupen i `guider.py`, kör om Step 5 och Step 6.

- [ ] **Step 7: Commit**

```bash
git add mall/leverans.py mall/adressregler.json mall/test/test_leverans.py
git commit -m "leverans.py: manifeststyrd ingest med facit, kontrollsummor och robots.txt"
```

---

### Task 5: Skill och dokumentation

**Files:**
- Modify: `.claude/skills/ingest/SKILL.md`, `mall/komponenter.md`, `CLAUDE.md`, `docs/HANDOFF_CONTEXT.md`

**Interfaces:**
- Consumes: `python mall/leverans.py plan|bygg|kontrollera|arkivera` (Task 4).

- [ ] **Step 1: Leveransflödet i skillen**

I `.claude/skills/ingest/SKILL.md`, lägg in ett nytt avsnitt direkt efter raden `Läs först: …` och före `## Steg 1: Inventera`:

````markdown
## Leverans eller lösa sidor?

**Finns `ingest/urls.json` är det en leverans.** Följ "Leveransflöde" nedan och hoppa över steg 1–6.
Annars: lösa sidor, steg 1–6.

## Leveransflöde

En leverans = `UPLOAD.txt` + `urls.json` (styrfiler, publiceras aldrig) + material. `urls.json` är facit.
Adresser skrivs om enligt `mall/adressregler.json` (`/guides/` → `/simulationsmcp/v1/guides/`).
Spec: `docs/superpowers/specs/2026-09-26-ingest-leveranser-design.md`.

1. **Plan:** `PYTHONIOENCODING=utf-8 python mall/leverans.py plan`
   - Läs även `ingest/UPLOAD.txt` själv och notera sådant som skriptet inte tolkar (nya krav, deadlines).
   - Visa användaren: planens utskrift (version, MUST-filer med kontrollsumma, antal nya/ändrade/oförändrade per spår, adressregel, saknade/överblivna, varningar) + egna noteringar.
   - **STOPP** vid rader under "STOPP". Förklara och bygg inte.
   - Fråga: **"Ja för att bygga?"** Vänta på svar.
2. **Bygg:** `PYTHONIOENCODING=utf-8 python mall/leverans.py bygg`
   - Listas "Vanliga sidor att hantera med omdöme": gör steg 2–5 nedan för just dem. Bygg med `pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/<mål> -Sokvag <mål>`.
3. **Kontrollera:** `PYTHONIOENCODING=utf-8 python mall/leverans.py kontrollera`
   - Ska ge `OK`.
   - Vid `FEL:`: rätta orsaken (i `mall/guider.py` om konverteringen är fel, aldrig för hand i `site/`) och kör 2–3 igen.
4. **Titta:** ta skärmdumpar av guidestartsidan, en kategorisida och en ändrad eller ny guide:
   `python mall/verifiera.py <mål> --sprak en --skarmdumpar <scratchpad>/ingest-dumpar`.
   Öppna SV desktop och EN mobil med Read-verktyget.
5. **Arkivera:** `python mall/leverans.py arkivera` flyttar hela leveransen, inklusive styrfilerna, till `ingest/_importerat/<datum>[-n]/`.
6. **Rapportera:**
   - byggda filer per spår
   - varningar
   - skärmdumpar
   - **deploy-noterna** som `kontrollera` skrev ut (binär uppladdning, MUST före serverrelease, `curl`-kontroller, krockrisken `simulationsmcp.html` ↔ `simulationsmcp/`)
   - Avsluta med: "Inget är committat. Titta i `site/` och säg till när jag ska committa."

Guidesidor ändras aldrig för hand i `site/` eller `mall/innehall/`. De genereras av `mall/guider.py` vid varje leverans.
Om `guider.py` stannar med "okänd sektion" har generatorn ändrats. Visa felet för användaren och föreslå en mappning i `guider.py`.
````

- [ ] **Step 2: Metadataformatet i `mall/komponenter.md`** (rättar ett uppskjutet granskningsfynd)

Lägg till efter avsnittet `## Tvåspråkighet – regler för varje textelement`:

````markdown
## Metadata överst i innehållsfilen

```
<!--
title: Sidans titel | Duke Systems AB
description: En mening utan raka citattecken.
lang: en                      (valfri; sv är standard – en = sidan startar i EN-läge)
robots: noindex, nofollow     (valfri; ger <meta name="robots">)
page-css:
  .klass{…}                   (noll eller flera rader sid-CSS)
-->
```

Raderna kommer i exakt den ordningen. `-->` står på en egen rad. Sidor i undermappar byggs med
`pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/<väg>/index.html` (vägen under `mall/innehall/` blir vägen i `site/`).
````

Och i K11:s "Sid-CSS" samt i `## Regler`: lägg till raden `code{font-family:var(--mono);font-size:0.88em;}` som sid-CSS för `<code>` (rättar ett uppskjutet granskningsfynd).

- [ ] **Step 3: `CLAUDE.md`**

I avsnittet `## Subpages, template and ingest`, efter stycket som börjar `**Ingest:**`, lägg till:

```markdown
**Deliveries:** when `ingest/urls.json` exists, `/ingest` runs the delivery flow via `python mall/leverans.py plan|bygg|kontrollera|arkivera`. `urls.json` is the answer key. Non-HTML files (e.g. `simulationsmcp/v1/modeling_guides.json`, fetched byte-for-byte by installed SimulationsMCP servers) are copied verbatim and hash-checked against `UPLOAD.txt`. Generator guide pages (`<main class="guide-content">`) are converted by `mall/guider.py` and published under `/simulationsmcp/v1/guides/` (`mall/adressregler.json` rewrites `/guides/`), English-only content, `noindex`, never linked from the rest of the site, and blocked in `site/robots.txt`. Never hand-edit generated guide pages. Tests: `python mall/test/test_guider.py`, `python mall/test/test_leverans.py`.

`site/` now has subdirectories: `bygg-sida.ps1` derives the output path from the content file's path under `mall/innehall/` (or `-Sokvag`), and `{{ROOT}}` makes header/footer links work at any depth.
```

- [ ] **Step 4: `docs/HANDOFF_CONTEXT.md`**

Lägg till sist:

```markdown
## Leveranser och SimulationsMCP-data (2026-09-26)

MCP-serverns fasta basadress är `https://duke.se/simulationsmcp/v1/`. Där ligger `modeling_guides.json` och
`guide-schema.json` (byte för byte, hämtas av installerade servrar) och modelleringsguiderna under `guides/`.
Guiderna är dolda: inga länkar från sajten, `noindex` och `robots.txt`. Leveranser kommer som `UPLOAD.txt` + `urls.json`
+ material i `ingest/` och importeras med `/ingest`. Deploy: ladda upp hela `site/`, JSON binärt, kontrollera med `curl`
att adressen ger 200 utan omdirigering. Spec: `docs/superpowers/specs/2026-09-26-ingest-leveranser-design.md`.
```

- [ ] **Step 5: Kör alla tester**

```bash
export PYTHONIOENCODING=utf-8
pwsh -File mall/test/test-bygg-sida.ps1 | tail -1 && python mall/test/test_verifiera.py | tail -1 && python mall/test/test_guider.py | tail -1 && python mall/test/test_leverans.py | tail -1
```
Expected: `Alla test OK` fyra gånger.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/ingest/SKILL.md mall/komponenter.md CLAUDE.md docs/HANDOFF_CONTEXT.md
git commit -m "Dokumentera leveransflödet i skill, katalog, CLAUDE.md och HANDOFF"
```

---

### Task 6: Importera dagens leverans (skarpt)

**Files:**
- Create (genererat): `site/simulationsmcp/v1/**`, `site/robots.txt`, `mall/innehall/simulationsmcp/v1/guides/**`
- Move: `ingest/*` → `ingest/_importerat/<datum>/`

**Interfaces:**
- Consumes: `/ingest`-skillens leveransflöde (Task 5).

- [ ] **Step 1: Kör skillens leveransflöde, steg 1 (plan)**

Förväntat i planen:
- version 1.13.0
- 2 exakta kopior (MUST, kontrollsumman a923b679…)
- 19 guider, alla `ny`
- "Adressregel … användes"
- dolt för `/simulationsmcp/v1/`
- inga STOPP

**Visa planen för användaren och vänta på ja.**

- [ ] **Step 2: Steg 2–5 (bygg, kontrollera, titta, arkivera)**

Förväntat:
- `kontrollera` ger `OK`
- skärmdumparna ser ut som produktsidor
- `ingest/` innehåller bara `_importerat/`

- [ ] **Step 3: Steg 6, rapport + deploy-noter.** Fråga användaren om committen (ingest committar aldrig automatiskt).
