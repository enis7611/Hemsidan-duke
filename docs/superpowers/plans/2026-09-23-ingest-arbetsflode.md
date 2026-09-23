# Ingest-arbetsflöde – implementationsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ett arbetsflöde (`/ingest`) som tar rena HTML-filer från `ingest/`, klär på dem med Duke-designen, gör dem tvåspråkiga och lägger dem i `site/`, redo att deploya.

**Architecture:**
- Den mekaniska delen är deterministisk. `mall/bygg-sida.ps1` sätter ihop `mall/prefix.html` + en innehållsfil + `mall/suffix.html`.
- `mall/verifiera.py` kontrollerar resultatet i en riktig webbläsare.
- Omdömesdelen (tolkning, komponentval, översättning, placering) beskrivs som en projektskill, `.claude/skills/ingest/SKILL.md`, med regelboken `mall/komponenter.md`.

**Tech Stack:** PowerShell 7 (pwsh), Python 3.13 + Playwright (redan installerat), ren HTML/CSS/JS. Inga nya beroenden, inget testramverk. Testerna är fristående skript med asserts.

**Spec:** `docs/superpowers/specs/2026-09-23-ingest-arbetsflode-design.md`

## Global Constraints

- Deploy-katalog: `site/` (flyttad med `git mv` från `src/release-2026-06-13/`). `src/index.html` och `src/variants/` rörs inte.
- Mallen ligger i `mall/` i rotkatalogen, aldrig i `site/`.
- `site/index.html` byggs aldrig av skriptet. Den är handredigerad.
- Alla filer skrivs som UTF-8 **utan BOM** och med **LF**-radslut (befintliga sidor är LF).
- Filnamn för sidor: `^[a-z0-9-]+\.html$` (gemener, siffror, bindestreck, å/ä/ö → a/a/o).
- Tvåspråkighet i innehåll görs med `data-sv`/`data-en` på **löv-element** (element utan barn-element). `applyLang()` sätter `textContent` och raderar all inre markup.
- Innehållsregler (HANDOFF §1):
  - Förbjudna ord: NetApp, Bridgeworks, Spectra Logic, ForecastPRO, Komprise, Office 365-konsult, Visma, RPA, generell IT-support, TeamViewer.
  - Produktnamn: SimulationsMCP / SimulationsMCP Build / ExtendMQTT, aldrig "ExtendSim MCP".
  - Taglinen är låst: "Vi löser problemet. Sedan 1988."
  - CTA-text: "Berätta om ditt problem".
- Bara CSS-variabler från `:root`. Inga nya hårdkodade färger (heroernas och de mörka sektionernas befintliga gradienter undantagna).
- Ingen automatisk commit i själva ingest-flödet. (Planens egna commit-steg gäller byggandet av verktyget.)
- Plattform: Windows 11. Kör PowerShell med `pwsh` och Python med `python`.

## Review Focus

1. **Innehållsfil sparad med CRLF och/eller BOM** (Windows-editor): utdata ska ändå bli LF utan BOM. Testas i Task 2.
2. **Råfil i Windows-1252** (å/ä/ö blir trasiga vid UTF-8-läsning): bygget ska avbryta med tydligt fel i stället för att publicera "Ã¥". Testas i Task 2.
3. **Titel eller beskrivning med `$`, `&` eller `{{`**: ska hamna ordagrant, utan regex-tolkning. Citattecken i description ska avvisas eftersom de bryter attributet. Testas i Task 2.
4. **`data-sv` på element med inre markup** (`<p data-sv="…">text <strong>x</strong></p>`): markupen försvinner tyst vid språkbyte. Verifieraren ska flagga det. Testas i Task 3.
5. **Otillåtet filnamn** (`försäkring.html`, `index.html`): bygget ska vägra i stället för att skriva över startsidan eller skapa en url med å. Testas i Task 2.

---

## Filstruktur

| Fil | Ansvar |
|---|---|
| `site/` | Deploy-katalog (flyttad) |
| `ingest/_importerat/.gitkeep` | Inkorgen och arkivet |
| `mall/prefix.html` | `<!DOCTYPE>` t.o.m. `<style>` för sid-CSS, med `{{TITLE}}`, `{{DESCRIPTION}}`, `{{PAGE_CSS}}` |
| `mall/suffix.html` | `<footer>` t.o.m. `</html>` |
| `mall/innehall/<namn>.html` | Metadata-kommentar + innehåll mellan header och footer |
| `mall/bygg-sida.ps1` | Sätter ihop en sida |
| `mall/verifiera.py` | Webbläsarkontroll av en byggd sida |
| `mall/komponenter.md` | Regelbok: ryggrad, komponenter, mappning |
| `mall/test/test-bygg-sida.ps1` | Tester för bygget |
| `mall/test/test_verifiera.py` | Tester för verifieraren |
| `mall/test/fixtures/trasig.html` | Innehållsfil med kända fel |
| `mall/test/komponent-demo.html` | Innehållsfil med alla komponenter (visuell kontroll) |
| `.claude/skills/ingest/SKILL.md` | Arbetsflödet |

### Hur en undersida är uppbyggd (uppmätt i `extendmqtt.html`, gäller alla tre)

- Rad 1–1402: head + global CSS + header + mobilmeny, identiska på alla sidor utom rad 6 (`<meta name="description" …>`) och rad 10 (`<title>…</title>`).
- Rad 1403: `<style>`, därefter sid-CSS, sedan `</style>` och en tomrad.
- Därefter innehåll (`<!-- ─── PRODUKT-HERO …` … CTA-sektionen), sedan tomrader.
- `<footer>` till och med `</html>\n`, identiskt på alla sidor.

---

### Task 1: Flytta den skarpa versionen till `site/` och skapa inkorgen

**Files:**
- Move: `src/release-2026-06-13/` → `site/`
- Create: `ingest/_importerat/.gitkeep`

**Interfaces:**
- Produces: `site/index.html`, `site/extendmqtt.html`, `site/simulationsmcp.html`, `site/simulationsmcp-build.html` (oförändrade), katalogen `ingest/`.

- [ ] **Step 1: Flytta med git**

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
git mv src/release-2026-06-13 site
mkdir -p ingest/_importerat && touch ingest/_importerat/.gitkeep
```

- [ ] **Step 2: Kontrollera att innehållet är orört och att länkarna mellan sidorna är relativa**

```bash
git status --short          # förväntat: bara R-rader (rename) + ny .gitkeep (+ ev. docs/TODO.md från användaren)
grep -c 'href="index.html#' site/extendmqtt.html   # > 0: undersidorna länkar relativt, flytten bryter inget
grep -n 'href="extendmqtt.html"\|href="simulationsmcp.html"\|href="simulationsmcp-build.html"' site/index.html   # 3 träffar
```

- [ ] **Step 3: Commit** (lägg INTE till `docs/TODO.md`, som är användarens ocommittade ändring)

```bash
git add site ingest/_importerat/.gitkeep
git commit -m "Flytta skarp version till site/ och skapa ingest/-inkorg"
```

---

### Task 2: Mall + `bygg-sida.ps1` (bygger om de tre undersidorna byte-identiskt)

**Files:**
- Create: `mall/prefix.html`, `mall/suffix.html`, `mall/innehall/extendmqtt.html`, `mall/innehall/simulationsmcp.html`, `mall/innehall/simulationsmcp-build.html`
- Create: `mall/bygg-sida.ps1`
- Test: `mall/test/test-bygg-sida.ps1`

**Interfaces:**
- Consumes: `site/*.html` från Task 1.
- Produces:
  - `pwsh -File mall/bygg-sida.ps1 -Innehall <sökväg> [-Ut <katalog>]` skriver `<Ut>/<filnamn>` (default `-Ut` = `site/`) och skriver ut sökvägen till stdout. Vid fel: `throw` med svensk text och exit ≠ 0.
  - Innehållsfilens format, exakt:
    ```
    <!--
    title: <titel>
    description: <beskrivning>
    page-css:
    <noll eller flera CSS-rader>
    -->
    <innehåll: allt mellan header och <footer>>
    ```

- [ ] **Step 1: Skriv det fallerande testet** `mall/test/test-bygg-sida.ps1`

```powershell
# Tester för mall/bygg-sida.ps1. Kör: pwsh -File mall/test/test-bygg-sida.ps1
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot\..\..").Path
$bygg = Join-Path $root 'mall\bygg-sida.ps1'
$tmp  = Join-Path ([IO.Path]::GetTempPath()) ("bygg-test-" + [guid]::NewGuid())
New-Item -ItemType Directory $tmp | Out-Null
$utf8 = [Text.UTF8Encoding]::new($false)
$script:fel = 0

function Ok($villkor, $text) {
  if ($villkor) { Write-Host "OK   $text" } else { Write-Host "FEL  $text" -ForegroundColor Red; $script:fel++ }
}
function Kastar([scriptblock]$block, $text) {
  try { & $block | Out-Null; Ok $false "$text (inget fel kastades)" } catch { Ok $true "$text [$($_.Exception.Message)]" }
}
function Skriv($namn, $text) { $p = Join-Path $tmp $namn; [IO.File]::WriteAllText($p, $text, $utf8); $p }

$giltig = "<!--`ntitle: Test | Duke Systems AB`ndescription: Beskrivning`npage-css:`n-->`n<section>Hej</section>`n"

# 1. De tre undersidorna byggs om byte-identiskt från sina innehållsfiler
$ut = Join-Path $tmp 'ut'; New-Item -ItemType Directory $ut | Out-Null
foreach ($n in 'extendmqtt', 'simulationsmcp', 'simulationsmcp-build') {
  & $bygg -Innehall (Join-Path $root "mall\innehall\$n.html") -Ut $ut | Out-Null
  $a = [IO.File]::ReadAllBytes((Join-Path $root "site\$n.html"))
  $b = [IO.File]::ReadAllBytes((Join-Path $ut "$n.html"))
  Ok ([Linq.Enumerable]::SequenceEqual($a, $b)) "$n.html byggs om byte-identiskt"
}

# 2. Tom page-css ger ett tomt <style>-block och platshållarna ersätts
$p = Skriv 'enkel.html' $giltig
& $bygg -Innehall $p -Ut $ut | Out-Null
$s = [IO.File]::ReadAllText((Join-Path $ut 'enkel.html'))
Ok ($s.Contains("<title>Test | Duke Systems AB</title>")) "titel ersatt"
Ok ($s.Contains('<meta name="description" content="Beskrivning">')) "beskrivning ersatt"
Ok ($s.Contains("<style>`n</style>`n`n<section>Hej</section>`n<footer>")) "tom sid-CSS + innehåll på rätt plats"
Ok (-not $s.Contains('{{')) "inga platshållare kvar"

# 3. CRLF + BOM i innehållsfilen → utdata LF utan BOM (Review Focus 1)
$p = Join-Path $tmp 'crlf.html'
[IO.File]::WriteAllText($p, $giltig.Replace("`n", "`r`n"), [Text.UTF8Encoding]::new($true))
& $bygg -Innehall $p -Ut $ut | Out-Null
$bytes = [IO.File]::ReadAllBytes((Join-Path $ut 'crlf.html'))
Ok (-not ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB)) "ingen BOM i utdata"
Ok ($bytes -notcontains 13) "inga CR i utdata"

# 4. Windows-1252-fil avvisas (Review Focus 2)
$p = Join-Path $tmp 'ansi.html'
# 0xE5 = 'å' i Windows-1252, ogiltig som ensam byte i UTF-8
[IO.File]::WriteAllBytes($p, [byte[]]($utf8.GetBytes($giltig) + [byte]0x70 + [byte]0xE5 + [byte]0x0A))
Kastar { & $bygg -Innehall $p -Ut $ut } "icke-UTF-8 avvisas"

# 5. Specialtecken ordagrant; citattecken i description avvisas (Review Focus 3)
$p = Skriv 'special.html' ($giltig.Replace('title: Test', 'title: Pris $1 & {{x}}'))
& $bygg -Innehall $p -Ut $ut | Out-Null
Ok ([IO.File]::ReadAllText((Join-Path $ut 'special.html')).Contains('<title>Pris $1 & {{x}} | Duke Systems AB</title>')) "titel med `$ & {{ ordagrant"
$p = Skriv 'citat.html' ($giltig.Replace('description: Beskrivning', 'description: Ett "citat"'))
Kastar { & $bygg -Innehall $p -Ut $ut } "citattecken i description avvisas"

# 6. Otillåtna filnamn (Review Focus 5)
$p = Skriv 'index.html' $giltig
Kastar { & $bygg -Innehall $p -Ut $ut } "index.html byggs aldrig"
$p = Skriv 'försäkring.html' $giltig
Kastar { & $bygg -Innehall $p -Ut $ut } "filnamn med å/ä/ö avvisas"

# 7. Trasig metadata
$p = Skriv 'utanmeta.html' "<section>Hej</section>`n"
Kastar { & $bygg -Innehall $p -Ut $ut } "saknad metadata-kommentar avvisas"
$p = Skriv 'tomtitel.html' ($giltig.Replace('title: Test | Duke Systems AB', 'title: '))
Kastar { & $bygg -Innehall $p -Ut $ut } "tom titel avvisas"
$p = Skriv 'ejstangd.html' "<!--`ntitle: T`ndescription: D`npage-css:`n<section>Hej</section>`n"
Kastar { & $bygg -Innehall $p -Ut $ut } "ostängd metadata avvisas"

Remove-Item -Recurse -Force $tmp
if ($script:fel) { Write-Host "$($script:fel) test fallerade" -ForegroundColor Red; exit 1 } else { Write-Host "Alla test OK"; exit 0 }
```

- [ ] **Step 2: Kör testet och se det fallera**

Run: `pwsh -File mall/test/test-bygg-sida.ps1`
Expected: FAIL (`mall\bygg-sida.ps1` och innehållsfilerna finns inte ännu).

- [ ] **Step 3: Klipp ut mallen och innehållsfilerna (engångskörning, sparas inte som fil)**

```powershell
$root = 'C:\Dev\CluadeCode\Hemsidan_duke_se'
$utf8 = [Text.UTF8Encoding]::new($false)
New-Item -ItemType Directory -Force "$root\mall\innehall" | Out-Null

$L = [IO.File]::ReadAllText("$root\site\extendmqtt.html").Split("`n")
if ($L[1402] -ne '<style>') { throw 'rad 1403 i extendmqtt.html är inte <style>' }
$p = $L[0..1402]
$p[5] = '<meta name="description" content="{{DESCRIPTION}}">'
$p[9] = '<title>{{TITLE}}</title>'
[IO.File]::WriteAllText("$root\mall\prefix.html", ($p -join "`n") + "`n{{PAGE_CSS}}</style>`n`n", $utf8)
$f = [Array]::IndexOf($L, '<footer>')
[IO.File]::WriteAllText("$root\mall\suffix.html", ($L[$f..($L.Count - 1)] -join "`n"), $utf8)

foreach ($n in 'extendmqtt', 'simulationsmcp', 'simulationsmcp-build') {
  $L = [IO.File]::ReadAllText("$root\site\$n.html").Split("`n")
  if ($L[1402] -ne '<style>') { throw "$n`: rad 1403 är inte <style>" }
  $close = [Array]::IndexOf($L, '</style>', 1403)
  if ($L[$close + 1] -ne '') { throw "$n`: ingen tomrad efter </style>" }
  $f = [Array]::IndexOf($L, '<footer>')
  $title = $L[9] -replace '^<title>(.*)</title>$', '$1'
  $desc  = $L[5] -replace '^<meta name="description" content="(.*)">$', '$1'
  $css   = $L[1403..($close - 1)] -join "`n"
  $body  = $L[($close + 2)..($f - 1)] -join "`n"
  $meta  = "<!--`ntitle: $title`ndescription: $desc`npage-css:`n$css`n-->`n"
  [IO.File]::WriteAllText("$root\mall\innehall\$n.html", $meta + $body + "`n", $utf8)
}
```

Kontrollera också att prefixen verkligen är gemensamma. Följande ska ge **ingen utdata** (bara rad 6 och 10 får skilja, och de maskas):

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
for n in simulationsmcp simulationsmcp-build; do diff <(sed -n '1,1403p' site/extendmqtt.html | sed '6d;10d') <(sed -n '1,1403p' site/$n.html | sed '6d;10d'); diff <(sed -n '/^<footer>/,$p' site/extendmqtt.html) <(sed -n '/^<footer>/,$p' site/$n.html); done
```

- [ ] **Step 4: Skriv `mall/bygg-sida.ps1`**

```powershell
<#
  Bygger en undersida: mall/prefix.html + innehållsfil + mall/suffix.html → <Ut>/<filnamn>.
  Innehållsfilen börjar med en metadata-kommentar (title, description, page-css), se mall/komponenter.md.
  Kör: pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/extendmqtt.html
#>
param(
  [Parameter(Mandatory)][string]$Innehall,
  [string]$Ut = (Join-Path $PSScriptRoot '..\site')
)
$ErrorActionPreference = 'Stop'
$utf8 = [Text.UTF8Encoding]::new($false)

function Las-Lf([string]$sokvag) {
  $strikt = [Text.UTF8Encoding]::new($false, $true)   # kastar på ogiltig UTF-8
  try { $text = $strikt.GetString([IO.File]::ReadAllBytes($sokvag)) }
  catch { throw "Filen är inte giltig UTF-8 (spara om den som UTF-8): $sokvag" }
  if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }
  $text -replace "`r`n", "`n"
}

$namn = [IO.Path]::GetFileName($Innehall)
if ($namn -eq 'index.html') { throw 'index.html är handredigerad och byggs aldrig av bygg-sida.ps1' }
if ($namn -cnotmatch '^[a-z0-9-]+\.html$') { throw "Otillåtet filnamn '$namn': bara a-z, 0-9 och bindestreck (å/ä/ö → a/a/o)" }

$raw = Las-Lf $Innehall
if (-not $raw.StartsWith("<!--`n")) { throw "Innehållsfilen saknar metadata-kommentar överst: $Innehall" }
$slut = $raw.IndexOf("`n-->`n")
if ($slut -lt 0) { throw "Metadata-kommentaren stängs inte med en egen rad '-->': $Innehall" }
$huvud = $raw.Substring(5, $slut - 5).Split("`n")
$kropp = $raw.Substring($slut + 5)

if ($huvud.Count -lt 3 -or -not $huvud[0].StartsWith('title:') -or -not $huvud[1].StartsWith('description:') -or $huvud[2] -ne 'page-css:') {
  throw "Metadata måste vara exakt raderna 'title:', 'description:', 'page-css:' i den ordningen: $Innehall"
}
$titel = $huvud[0].Substring(6).Trim()
$beskr = $huvud[1].Substring(12).Trim()
if (-not $titel) { throw "title saknar värde: $Innehall" }
if (-not $beskr) { throw "description saknar värde: $Innehall" }
if ($beskr.Contains('"')) { throw "description får inte innehålla citattecken (\"): $Innehall" }
$cssRader = if ($huvud.Count -gt 3) { $huvud[3..($huvud.Count - 1)] } else { @() }
$css = if (($cssRader -join '').Trim()) { ($cssRader -join "`n") + "`n" } else { '' }

# String.Replace är ordagrann (ingen regex), så $, & och {{ i titeln är ofarliga.
# PAGE_CSS ersätts först så att en titel som råkar innehålla "{{PAGE_CSS}}" inte tolkas.
$prefix = (Las-Lf (Join-Path $PSScriptRoot 'prefix.html')).Replace('{{PAGE_CSS}}', $css).Replace('{{DESCRIPTION}}', $beskr).Replace('{{TITLE}}', $titel)
$suffix = Las-Lf (Join-Path $PSScriptRoot 'suffix.html')

New-Item -ItemType Directory -Force $Ut | Out-Null
$utfil = Join-Path (Resolve-Path $Ut).Path $namn
[IO.File]::WriteAllText($utfil, $prefix + $kropp + $suffix, $utf8)
$utfil
```

Obs om ordningen på `.Replace()`: `{{PAGE_CSS}}`, `{{DESCRIPTION}}` och `{{TITLE}}` förekommer bara en gång var i prefixen. En titel som innehåller `{{x}}` skrivs in sist och ersätts därför aldrig vidare. Testet i steg 1 (punkt 5) bevisar det.

- [ ] **Step 5: Kör testet och se det passera**

Run: `pwsh -File mall/test/test-bygg-sida.ps1`
Expected: alla rader `OK`, sista raden `Alla test OK`, exit 0.

Om punkt 1 fallerar: jämför med `diff site/extendmqtt.html <tmp>/ut/extendmqtt.html` (lägg tillfälligt en `Read-Host` före `Remove-Item` för att behålla tmp-katalogen, eller kör bygget manuellt till en egen katalog). Vanligaste orsaken är en saknad eller extra `\n` runt `</style>` eller före `<footer>`.

- [ ] **Step 6: Bygg om `site/` med skriptet och bekräfta att git inte ser någon ändring**

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
for n in extendmqtt simulationsmcp simulationsmcp-build; do pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/$n.html; done
git status --short site/   # förväntat: ingen utdata
```

- [ ] **Step 7: Commit**

```bash
git add mall/prefix.html mall/suffix.html mall/innehall mall/bygg-sida.ps1 mall/test/test-bygg-sida.ps1
git commit -m "Mall och bygg-sida.ps1: undersidor byggs från innehållsfiler"
```

---

### Task 3: `verifiera.py` (webbläsarkontroll)

**Files:**
- Create: `mall/verifiera.py`
- Create: `mall/test/fixtures/trasig.html`
- Test: `mall/test/test_verifiera.py`

**Interfaces:**
- Consumes: `mall/bygg-sida.ps1` (Task 2), `site/` (Task 1).
- Produces:
  - `python mall/verifiera.py <sida.html> [--rot site] [--fran index.html] [--skarmdumpar <katalog>]` skriver `FEL: …`-rader och en sammanfattning, med exit 0 (OK) eller 1 (fel).
  - Python-API: `verifiera(rot: Path, sida: str, fran: str | None, skarmdumpar: Path | None) -> list[str]` returnerar felmeddelanden på svenska. En tom lista betyder OK.
  - Skärmdumpar: `<katalog>/<namn>-sv-desktop.png`, `<katalog>/<namn>-en-mobil.png`.

- [ ] **Step 1: Skriv fixture-filen** `mall/test/fixtures/trasig.html` (en innehållsfil med kända fel)

```html
<!--
title: Trasig testsida | Duke Systems AB
description: Fixture för test_verifiera.py
page-css:
-->
<section style="background:var(--white);">
  <div class="container">
    <h2 id="tomEn" data-sv="Rubrik" data-en="">Rubrik</h2>
    <p data-sv="Text med" data-en="Text with">Text med <strong>fetstil</strong></p>
    <a href="finns-inte.html">Trasig sidlänk</a>
    <a href="#saknas">Trasigt ankare</a>
    <a href="index.html#finns-inte-heller">Trasigt ankare på annan sida</a>
  </div>
</section>
<script>odefinieradFunktion();</script>

```

- [ ] **Step 2: Skriv det fallerande testet** `mall/test/test_verifiera.py`

```python
"""Tester för mall/verifiera.py. Kör: python mall/test/test_verifiera.py"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "mall"))
from verifiera import verifiera  # noqa: E402

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

print("Alla test OK" if fel_antal == 0 else f"{fel_antal} test fallerade")
sys.exit(1 if fel_antal else 0)
```

- [ ] **Step 3: Kör testet och se det fallera**

Run: `python mall/test/test_verifiera.py`
Expected: FAIL med `ModuleNotFoundError: No module named 'verifiera'`.

- [ ] **Step 4: Skriv `mall/verifiera.py`**

```python
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
from urllib.parse import urlsplit

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


def kontrollera_lankar(page, rot: Path, sida: str) -> list:
    fel = []
    ids = set(page.eval_on_selector_all("[id]", "els => els.map(e => e.id)"))
    for href in page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
        if EXTERNT.match(href):
            continue
        delar = urlsplit(href)
        if delar.path and not (rot / delar.path).is_file():
            fel.append(f"Länken {href} pekar på en fil som inte finns")
            continue
        if delar.fragment:
            if not delar.path or delar.path == sida:
                finns = delar.fragment in ids
            else:
                text = (rot / delar.path).read_text(encoding="utf-8")
                finns = re.search(r'id="%s"' % re.escape(delar.fragment), text) is not None
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


def verifiera(rot: Path, sida: str, fran=None, skarmdumpar=None) -> list:
    rot = Path(rot).resolve()
    if not (rot / sida).is_file():
        return [f"Sidan {sida} finns inte i {rot}"]
    fel = []
    namn = Path(sida).stem
    httpd, bas = starta_server(rot)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            # Desktop: JS-fel, språk, länkar, skärmdump SV
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            lyssna_efter_fel(page, fel)
            page.goto(f"{bas}/{sida}", wait_until="load")
            if skarmdumpar:
                Path(skarmdumpar).mkdir(parents=True, exist_ok=True)
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
                mobil.evaluate("toggleLang()")
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
    a = ap.parse_args(argv)
    fel = verifiera(a.rot, a.sida, a.fran, a.skarmdumpar)
    for f in fel:
        print("FEL:", f)
    print("OK" if not fel else f"{len(fel)} fel")
    return 1 if fel else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Kör testet och se det passera**

Run: `python mall/test/test_verifiera.py`
Expected: alla rader `OK`, `Alla test OK`, exit 0.

Om testfall 1 fallerar på en **befintlig** sida (till exempel "data-sv med inre markup" eller "Saknar data-en" i `extendmqtt.html`): **försvaga inte kontrollen.** Det är ett verkligt fel i den publicerade sidan. Stoppa och rapportera till användaren med den exakta felraden, och fråga om sidan ska rättas nu (i `mall/innehall/<namn>.html` + ombyggnad) eller om kontrollen ska undanta just det elementet.

- [ ] **Step 6: Kör verifieraren mot alla tre undersidor via CLI**

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
for n in extendmqtt simulationsmcp simulationsmcp-build; do python mall/verifiera.py $n.html --fran index.html || echo "^^ $n"; done
```
Expected: `OK` tre gånger.

- [ ] **Step 7: Commit**

```bash
git add mall/verifiera.py mall/test/test_verifiera.py mall/test/fixtures/trasig.html
git commit -m "verifiera.py: webbläsarkontroll av byggda sidor"
```

---

### Task 4: Komponentkatalogen `mall/komponenter.md` + demosida

**Files:**
- Create: `mall/komponenter.md`
- Test: `mall/test/komponent-demo.html` (innehållsfil som använder varje komponent en gång)

**Interfaces:**
- Consumes: `bygg-sida.ps1` (Task 2), `verifiera.py` (Task 3).
- Produces: `mall/komponenter.md` med rubrikerna `## Ryggrad`, `## Komponenter` (en `### K<n>: <namn>` per komponent), `## Mappning` och `## Regler`. Skillen i Task 5 hänvisar till komponenterna som `K1`–`K12`.

- [ ] **Step 1: Skriv `mall/komponenter.md`**

Dokumentets inledning, ryggrad, mappning och regler skrivs **exakt** så här:

````markdown
# Komponentkatalog – påklädning av importerade sidor

Regelbok för ingest-flödet (`.claude/skills/ingest/SKILL.md`). En rå sida ska se ut som de
befintliga produktsidorna (`site/extendmqtt.html` m.fl.). Använd bara komponenterna nedan. Hitta inte på nya.

Alla snuttar är innehåll för `mall/innehall/<namn>.html`. Byt texterna. Behåll klasser och struktur.

## Ryggrad (fast ordning)

1. **K1 Produkt-hero**: första rubriken + första stycket i råfilen.
2. **Innehållssektioner**: en per `<h2>` i råfilen, med bakgrund som växlar i ordningen
   vit (`var(--white)`) → ljusgrå (`var(--bg)`) → mörk (K2-mörk) → vit → …
   Två mörka sektioner i rad får aldrig förekomma, och sektionen direkt före K10 CTA är aldrig mörk.
3. **K10 CTA-band**: alltid sist.

## Tvåspråkighet – regler för varje textelement

- `data-sv="…"` + `data-en="…"` + svensk text som innehåll, på **löv-element** (inga barn-element).
- Behövs markup mitt i en mening (`<code>`, `<strong>`, länk)? Dela meningen i `<span data-sv data-en>`-bitar
  runt markupen, som `site/extendmqtt.html` gör med `<code>ssl://</code>`.
- Egennamn och tekniska termer som är lika på båda språken (t.ex. `MQTT_Publish`) behöver inga data-attribut.
- `&`, `<`, `"` i attributvärden skrivs som `&amp;`, `&lt;`, `&quot;`.

## Mappning: rått innehåll → komponent

| Rått innehåll | Komponent |
|---|---|
| Första `<h1>` + första `<p>` | K1 Produkt-hero |
| `<h2>` + inledande `<p>` | K2 Sektionshuvud (i ljus eller mörk sektion) |
| Lista, 3–6 punkter som var och en har egen rubrik (`<li><strong>Rubrik</strong> text`) | K3 Kortrutnät |
| `<ol>` eller "steg 1, 2, 3" / "så funkar det" | K4 Stegflöde |
| Nyckel–värde-par, tekniska fakta (`<dl>`, "Latens: 100 µs") | K5 Specifikationslista (i mörk sektion) |
| Två parallella listor ("Ingår / Ingår inte", "Idag / Senare") | K6 Två spår |
| 3–4 korta påståenden med rubrik | K7 Pelare (i mörk sektion) |
| `<pre>`, `<code>`-block, kommandon, exempeldialog | K8 Terminal |
| Löpande text utan struktur | K9 Brödtext |
| `<table>` | K11 Tabell |
| `<img>` | K12 Bild |
| — | K10 CTA-band (alltid sist) |

## Regler

- Varje block som ska animeras får `reveal`, och syskon i rutnät får `reveal-delay-1` … `reveal-delay-4` i tur och ordning.
- Bara CSS-variabler från `:root`. Inga nya hårdkodade färger. Undantaget är gradienterna i K1, K2-mörk och K10, som kopieras som de är.
- Passar innehållet ingen komponent: använd K9 Brödtext och flagga det i planen till användaren.
  Nya komponenter läggs till i den här katalogen först efter användarens godkännande.
- **Texten ändras inte i sak.** Ingressen i K1 får kortas och långa stycken delas upp. Allt som kortats redovisas i planen.
- Komponenter som kräver sid-CSS (K4, K5, K11, `<code>`) listar den under "Sid-CSS". Lägg den i innehållsfilens
  `page-css:`, en gång per sida.
````

Därefter kommer avsnittet `## Komponenter` med en `### K<n>`-rubrik per komponent. Varje komponent har tre delar: **När**, **Källa** och **Snutt**. Snuttarna kopieras från källan enligt tabellen nedan. Radnumren gäller filerna i `site/` efter Task 1. Leta upp dem med kommentarsrubrikerna om de flyttats. Kopiera **ett representativt exempel** av upprepade element (ett kort, en spec-rad, en terminalrad per talartyp) och byt all text mot korta svenska/engelska exempel (`Rubrik`/`Heading`, `Kort beskrivning.`/`Short description.`) så att snutten är generisk.

| K | Namn | Källa (fil, sektion) | Sid-CSS |
|---|---|---|---|
| K1 | Produkt-hero | `extendmqtt.html`, `<!-- ─── PRODUKT-HERO` till och med dess `</section>` | – |
| K2 | Sektionshuvud, ljus + mörk variant | ljus: `extendmqtt.html` "FEM BLOCK" (`<section>` + `.section-header`). Mörk: "ANVÄNDNINGSFALL" (`<section>` med gradient + `.mcp-bg-pattern` + `.section-header`) | – |
| K3 | Kortrutnät | `extendmqtt.html` "FEM BLOCK": `.services-grid` med ett `.service-card` | – |
| K4 | Stegflöde | `simulationsmcp-build.html` "ITERATIVT": raden med `.mcp-cat`-chips och `→` | `.mcp-cat{…}` (första raden i sid-CSS för `simulationsmcp.html`) |
| K5 | Specifikationslista | `extendmqtt.html` "PRESTANDA": ramen + en `.spec-row` | de fyra `.spec-row`-raderna i sid-CSS för `extendmqtt.html` |
| K6 | Två spår | `extendmqtt.html` "OMFATTNING & STATUS": `.konsult-grid` med två `.konsult-track`, ett `.track-item` vardera | – |
| K7 | Pelare | `extendmqtt.html` "ANVÄNDNINGSFALL": `.pillars` med en `.pillar` | – |
| K8 | Terminal | `simulationsmcp-build.html` "DEMO": `.mcp-terminal` med en `Du`-rad och en `AI`-rad | – |
| K9 | Brödtext | skrivs nedan | – |
| K10 | CTA-band | `extendmqtt.html` `<!-- ─── CTA` till och med `</section>` | – |
| K11 | Tabell | skrivs nedan | skrivs nedan |
| K12 | Bild | skrivs nedan | – |

K9, K11 och K12 finns inte på sajten i dag och skrivs exakt så här:

````markdown
### K9: Brödtext

**När:** löpande text utan struktur. Placeras efter K2 i en ljus sektion.

```html
<div class="reveal" style="max-width:680px;margin:0 auto;">
  <p style="margin-bottom:1.1rem;" data-sv="Stycke på svenska." data-en="Paragraph in English.">Stycke på svenska.</p>
</div>
```

### K11: Tabell

**När:** råfilen har en `<table>`. Placeras efter K2 i en ljus sektion.

**Sid-CSS:**
```css
  .duke-table{width:100%;max-width:820px;margin:0 auto;border-collapse:collapse;font-size:0.92rem;}
  .duke-table th{font-family:var(--mono);font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--teal);text-align:left;padding:0.75rem 1rem;border-bottom:2px solid var(--teal);}
  .duke-table td{padding:0.75rem 1rem;border-bottom:1px solid var(--border);color:var(--navy);vertical-align:top;}
  .duke-table tr:last-child td{border-bottom:none;}
  .duke-table-wrap{overflow-x:auto;}
```

```html
<div class="duke-table-wrap reveal">
  <table class="duke-table">
    <thead><tr><th data-sv="Kolumn" data-en="Column">Kolumn</th><th data-sv="Värde" data-en="Value">Värde</th></tr></thead>
    <tbody><tr><td data-sv="Rad" data-en="Row">Rad</td><td>42</td></tr></tbody>
  </table>
</div>
```

### K12: Bild

**När:** råfilen har `<img>`. Bildfilen kopieras till `site/img/` och `src` skrivs om till `img/<fil>`.
`alt` översätts: sätt `alt` till svenska och lägg `data-alt-en` för engelska. Språkbytet påverkar inte `alt` i dag, så engelska alt-texter sparas bara för framtida bruk.

```html
<figure class="reveal" style="max-width:820px;margin:0 auto;text-align:center;">
  <img src="img/exempel.png" alt="Beskrivning" data-alt-en="Description" style="max-width:100%;height:auto;border-radius:12px;border:1px solid var(--border);">
  <figcaption style="font-size:0.85rem;color:var(--text-muted);margin-top:0.75rem;" data-sv="Bildtext." data-en="Caption.">Bildtext.</figcaption>
</figure>
```
````

Innan K11 och K12 skrivs: kontrollera att `--border`, `--navy`, `--teal`, `--text-muted`, `--white` och `--bg` finns i `:root` i `mall/prefix.html` (`grep -o -- '--[a-z-]*:' mall/prefix.html | sort -u`). Saknas någon, byt till den närmaste befintliga variabeln och notera det i commit-meddelandet.

- [ ] **Step 2: Skriv demosidan** `mall/test/komponent-demo.html`

Demosidan är en innehållsfil med metadata `title: Komponentdemo | Duke Systems AB`, `description: Visuell kontroll av komponentkatalogen` och `page-css:` med sid-CSS för K4, K5 och K11. Innehållet följer ryggraden:
- K1
- K2 ljus + K3
- K2 ljus (`var(--bg)`) + K4
- K2 mörk + K5
- K2 ljus + K6
- K2 mörk + K7
- K2 ljus + K8 i en `<div style="max-width:720px;margin:0 auto;">`
- K2 ljus (`var(--bg)`) + K9 + K11 + K12 med `src="img/finns-ej.png"`
- K10

Snuttarna klistras in ordagrant från `komponenter.md`. Här testas katalogen, inte ny text.

- [ ] **Step 3: Bygg och verifiera demosidan**

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
D=$(mktemp -d); cp site/index.html "$D/"
pwsh -File mall/bygg-sida.ps1 -Innehall mall/test/komponent-demo.html -Ut "$D"
python mall/verifiera.py komponent-demo.html --rot "$D" --skarmdumpar "$D/dumpar"; echo "exit $?"
```
Expected: inga `FEL:`-rader utöver en bildrelaterad konsolrad för `img/finns-ej.png` (404). Accepteras den, bekräftar det bara att bilden inte finns. Exit 1 enbart p.g.a. den raden är godkänt.

- [ ] **Step 4: Titta på skärmdumparna**

Öppna `$D/dumpar/komponent-demo-sv-desktop.png` och `…-en-mobil.png` med Read-verktyget. Kontrollera:
- att varje komponent ser ut som på produktsidorna
- att bakgrunden växlar ljus/mörk
- att tabellen inte spräcker mobilbredden (den ska skrollas horisontellt inuti `.duke-table-wrap`)
- att EN-texten syns i mobilbilden

Rätta snuttarna i `komponenter.md` (och i demosidan) tills det ser rätt ut.

- [ ] **Step 5: Commit**

```bash
git add mall/komponenter.md mall/test/komponent-demo.html
git commit -m "Komponentkatalog för påklädning av importerade sidor"
```

---

### Task 5: Skillen `.claude/skills/ingest/SKILL.md`

**Files:**
- Create: `.claude/skills/ingest/SKILL.md`

**Interfaces:**
- Consumes: `mall/bygg-sida.ps1 -Innehall … [-Ut …]`, `python mall/verifiera.py <sida> --fran <källa> --skarmdumpar <katalog>`, `mall/komponenter.md` (K1–K12).
- Produces: kommandot `/ingest` (och att skillen triggas av "kör ingest", "importera sidorna i ingest").

- [ ] **Step 1: Skriv skillen**

````markdown
---
name: ingest
description: Importera rena HTML-sidor från ingest/ till webbplatsen site/ – klä på dem med Duke-designen, översätt till engelska, placera, länka in och verifiera. Använd när användaren säger "kör ingest", "importera sidorna", "/ingest" eller lägger filer i ingest/.
---

# Ingest – importera sidor till duke.se

Råa HTML-filer i `ingest/` blir färdiga, tvåspråkiga undersidor i `site/`. Följ stegen i ordning.
**Bygg ingenting före steg 3 (godkännande).** **Committa aldrig.**

Läs först: `mall/komponenter.md` (komponenter K1–K12 och regler) och HANDOFF §1 (`docs/HANDOFF_CONTEXT.md`).

## Steg 1: Inventera

Lista alla `*.html` rekursivt i `ingest/`, utom under `ingest/_importerat/`. Är listan tom: säg "Inkorgen är tom" och avsluta.
Andra filtyper (bilder) följer med den HTML-fil som refererar dem. Övriga filer nämns i planen som "ignoreras".

## Steg 2: Analysera varje fil (skriv ingenting)

För varje fil, bestäm:

1. **Kan den tolkas?** Tom fil, inte HTML, eller inte UTF-8 (å/ä/ö ser trasiga ut) → "hoppas över" med orsak. Filen ligger kvar.
2. **Typ:** produkt, tjänst, bransch, nyhet, juridiskt eller annat.
3. **Ny eller uppdatering:** jämför titel, `<h1>` och ämne mot `mall/innehall/*.html`. Samma produkt eller ämne → UPPDATERING av den filen.
4. **Filnamn** (ny sida): kort, url-vänligt, `^[a-z0-9-]+\.html$`, å/ä → a, ö → o. Aldrig `index.html`. Krockar det med en befintlig sida som *inte* är samma ämne, välj ett annat namn.
5. **Inlänkning** (ny sida): var i `site/index.html` sidan ska nås ifrån.
   - Produkt kopplad till en nod i `#mcp`: "Läs mer →"-länk som de befintliga (`site/index.html`, sök `Läs mer →`).
   - Bransch: kort eller länk i `#branscher`.
   - Övrigt: länk i footerns kolumn.
   Uppdatering: befintlig inlänkning behålls.
6. **Innehållskontroll:**
   - Förbjudna ord: NetApp, Bridgeworks, Spectra Logic, ForecastPRO, Komprise, Office 365-konsult, Visma, RPA, generell IT-support, TeamViewer.
   - Fel produktnamn: "ExtendSim MCP" → SimulationsMCP.
   - Ändrad tagline (ska vara "Vi löser problemet. Sedan 1988.").
   - Generiska CTA:er ("Kontakta oss") → "Berätta om ditt problem".
   Varje träff blir en varning i planen. Ta aldrig bort eller skriv om tyst.
7. **Komponentval:** mappa varje del av råfilen till K1–K12 enligt tabellen i `mall/komponenter.md`. Notera delar som inte passar (blir K9 + flagga).
8. **Engelska:** översätt rubrik och ingress till engelska (ton: saklig, självsäker, som befintliga EN-texter på sajten).

## Steg 3: Plan och godkännande (STOPP)

Visa en plan med ett block per fil:

```
### ingest/<sökväg>
Typ: produkt · NY → site/<namn>.html          (eller: UPPDATERING av site/<namn>.html – ändrar: …)
Inlänkning: "Läs mer →" under ExtendMQTT-noden i #mcp (site/index.html)
Komponenter: K1 hero · K2+K3 "Fem block" (6 kort) · K2m+K5 "Prestanda" · K10
EN rubrik: …
EN ingress: …
Kortat: ingressen 3 → 2 meningar (… borttaget)
Varningar: rad 12 nämner "ExtendSim MCP" → föreslår "SimulationsMCP"
```

Filer som hoppas över listas med orsak. Fråga sedan: **"Ja för alla, eller vill du ändra/hoppa över någon?"** Vänta på svar. Bygg bara godkända filer, med användarens ändringar.

## Steg 4: Bygg (per godkänd fil)

1. Skriv `mall/innehall/<namn>.html`:
   - Metadata: `title: <Sidtitel> | Duke Systems AB`, `description:` (en mening, utan citattecken), `page-css:` (sid-CSS för de komponenter som används, se "Sid-CSS" i katalogen).
   - Innehåll enligt ryggraden: K1, sektioner med växlande bakgrund, K10.
   - Alla texter med `data-sv`/`data-en` på löv-element (reglerna i katalogen). Hela sidan översätts till engelska, inte bara rubrik och ingress.
   - Texten ändras inte i sak. Bara den kortning som stod i planen.
   - Uppdatering: skriv över befintlig innehållsfil.
2. Bilder: kopiera refererade bilder till `site/img/` och skriv om `src` till `img/<fil>` (K12).
3. Bygg: `pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/<namn>.html`
4. Inlänkning (bara nya sidor): lägg in länken i `site/index.html` på den godkända platsen, i samma stil som befintliga länkar där. Ny synlig text följer CLAUDE.md:s tvåspråksregler (`data-sv`/`data-en` på löv-element räcker på undersidor. I `index.html` följ mönstret som gäller för just det stället).

## Steg 5: Verifiera

```
python mall/verifiera.py <namn>.html --fran index.html --skarmdumpar <scratchpad>/ingest-dumpar
```

- Exit 0: titta på båda skärmdumparna med Read-verktyget. Ser något fel ut (komponent trasig, text överlappar, mörk sektion efter mörk)? Rätta och kör om.
- `FEL:`-rader: rätta i innehållsfilen, bygg om, verifiera igen. Går det inte att lösa: gå till steg 6 med filen markerad som misslyckad.

Uppdatering: `--fran` utelämnas om sidan inte länkas från `index.html`.

## Steg 6: Städa och rapportera

- Lyckade filer: flytta originalet (och dess bilder) till `ingest/_importerat/<ÅÅÅÅ-MM-DD>/` och behåll den relativa undermappen.
  Använd `git mv` om filen är spårad, annars vanlig flytt.
- Misslyckade eller överhoppade filer ligger kvar i `ingest/`.
- Rapportera:
  - per fil: resultat (klar / misslyckad / överhoppad), målfil, inlänkning, varningar
  - ändrade filer (`git status --short`)
  - skärmdumparna (SV desktop, EN mobil)
- Avsluta med: "Inget är committat. Titta i `site/` och säg till när jag ska committa."
````

- [ ] **Step 2: Kontrollera att skillen syns**

Starta om Claude Code-sessionen eller kör `/skills`. Förväntat: `ingest` listas med beskrivningen ovan.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/ingest/SKILL.md
git commit -m "Skill /ingest: arbetsflöde för att importera sidor"
```

---

### Task 6: Genomkörning från början till slut + dokumentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/HANDOFF_CONTEXT.md` (nytt avsnitt sist)
- Modify: `C:\Users\Jonas\.claude\projects\C--Dev-CluadeCode-Hemsidan-duke-se\memory\site-redesign-direction.md`
- Temporärt: `ingest/test/provsida.html` (tas bort igen)

**Interfaces:**
- Consumes: allt ovan.

- [ ] **Step 1: Lägg en provfil i inkorgen**

`ingest/test/provsida.html`:

```html
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Simulering för sjukvården</title></head>
<body>
<h1>Simulering för sjukvården</h1>
<p>Vi hjälper regioner och sjukhus att hitta flaskhalsar i patientflöden innan de uppstår. Med ExtendSim modellerar vi akutmottagningar, operationsplanering och vårdplatser.</p>
<h2>Vad vi gör</h2>
<ul>
<li><strong>Akutflöden</strong> Väntetider och bemanning över dygnet.</li>
<li><strong>Operation</strong> Salsplanering och strykningar.</li>
<li><strong>Vårdplatser</strong> Beläggning och utskrivningsmönster.</li>
</ul>
<h2>Så går det till</h2>
<ol><li>Vi kartlägger flödet</li><li>Vi bygger modellen</li><li>Vi testar scenarier</li><li>Ni fattar beslut</li></ol>
<h2>Fakta</h2>
<table><tr><th>Område</th><th>Typisk effekt</th></tr><tr><td>Akut</td><td>Kortare väntetid</td></tr></table>
</body></html>
```

- [ ] **Step 2: Kör `/ingest` och följ skillen till steg 3**

Förväntat i planen:
- typ bransch, NY → `site/simulering-for-sjukvarden.html` (eller liknande)
- inlänkning i `#branscher`
- komponenter K1 · K2+K3 · K2+K4 · K2+K11 · K10
- EN-rubrik och EN-ingress
- inga varningar

**Visa planen för användaren.** Det här är skarpt test av godkännandesteget. Fortsätt efter svar.

- [ ] **Step 3: Slutför steg 4–6**

Förväntat:
- `verifiera.py` ger exit 0
- skärmdumparna ser ut som en produktsida
- `ingest/test/provsida.html` ligger nu i `ingest/_importerat/<dagens datum>/test/provsida.html`
- `git status` visar `site/simulering-for-sjukvarden.html`, `site/index.html` (inlänkning) och `mall/innehall/simulering-for-sjukvarden.html`

- [ ] **Step 4: Testa uppdatering**

Kopiera tillbaka provfilen till `ingest/test/provsida.html` och ändra en mening i den. Kör `/ingest` igen. Förväntat:
- planen säger **UPPDATERING** av `site/simulering-for-sjukvarden.html` och anger ändringen
- inlänkningen i `index.html` rörs inte (`git diff site/index.html` oförändrad jämfört med före körningen)

- [ ] **Step 5: Städa bort provsidan (fråga användaren först)**

Fråga användaren om provsidan ska behållas som riktig sida. Om nej:

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
git checkout -- site/index.html
rm -f site/simulering-for-sjukvarden.html mall/innehall/simulering-for-sjukvarden.html
rm -rf ingest/_importerat/*/test ingest/test
git status --short   # förväntat: bara docs/TODO.md (användarens) kvar
```

- [ ] **Step 6: Uppdatera `CLAUDE.md`**

1. I avsnittet "What this is": ersätt meningen "The entire site (HTML + CSS + JS) lives inline in one file: `src/index.html` (~2400 lines)." med:

```markdown
The live site is in **`site/`** (the deploy directory): `index.html` (one-pager) plus product subpages. Each page is a single self-contained file with inline CSS + JS. `src/index.html` and `src/variants/` are historical and not deployed.
```

2. Under "Running / previewing": byt `src/index.html` mot `site/index.html` i kommandot och texten.

3. Lägg till ett nytt avsnitt före "## Content guardrails":

```markdown
## Subpages, template and ingest

Subpages in `site/` (all except `index.html`) are **generated** — never edit them directly:
- Source: `mall/innehall/<name>.html` (metadata comment + page content).
- Build: `pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/<name>.html` → `mall/prefix.html` + content + `mall/suffix.html`.
- Verify: `python mall/verifiera.py <name>.html --fran index.html` (Playwright: JS errors, SV/EN, links, mobile menu).
- Tests: `pwsh -File mall/test/test-bygg-sida.ps1` and `python mall/test/test_verifiera.py`.
- Components for dressing up content: `mall/komponenter.md`.

On subpages, bilingual text uses `data-sv`/`data-en` on **leaf elements** (`applyLang()` sets `textContent`, which wipes inner markup).

**Ingest:** raw HTML pages dropped in `ingest/` are imported with the `/ingest` skill (`.claude/skills/ingest/SKILL.md`): analyse → plan for approval → build → verify → archive to `ingest/_importerat/`. Never commits automatically.

Changing shared head/header/footer: edit `mall/prefix.html` / `mall/suffix.html`, rebuild every file in `mall/innehall/`, and mirror the change in `site/index.html` by hand.
```

- [ ] **Step 7: Uppdatera `docs/HANDOFF_CONTEXT.md`**

Lägg till sist:

```markdown
## Ingest-arbetsflöde (2026-09-23)

Nya sidor läggs som ren HTML i `ingest/` och importeras med `/ingest` i Claude Code. Flödet klär på sidan med
sajtens design (komponenter i `mall/komponenter.md`), översätter till engelska, placerar den i `site/`, länkar in den
och verifierar i webbläsare. Användaren godkänner en plan innan något byggs och inget committas automatiskt.
Deploy-katalogen är `site/`. Spec: `docs/superpowers/specs/2026-09-23-ingest-arbetsflode-design.md`.
```

- [ ] **Step 8: Uppdatera minnet**

I `site-redesign-direction.md`, under `**How to apply:**`: ersätt "Skarp version finns i `src/release-2026-06-13/`." med "Skarp version finns i `site/` (flyttad från `src/release-2026-06-13/` 2026-09-23). Undersidorna genereras från `mall/innehall/` med `mall/bygg-sida.ps1`, och nya sidor importeras med `/ingest`." Ta också bort "privat GitHub-repo `hemsidan-duke`" ur listan över öppna TODO (klart enligt `docs/TODO.md`).

- [ ] **Step 9: Kör alla tester en sista gång**

```bash
cd /c/Dev/CluadeCode/Hemsidan_duke_se
pwsh -File mall/test/test-bygg-sida.ps1 && python mall/test/test_verifiera.py
```
Expected: `Alla test OK` två gånger.

- [ ] **Step 10: Commit**

```bash
git add CLAUDE.md docs/HANDOFF_CONTEXT.md
git commit -m "Dokumentera site/, mallen och ingest-flödet"
```
(Minnesfilen ligger utanför repot och committas inte.)
