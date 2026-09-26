# Ingest av leveranser (manifest, guider, exakta kopior) – design

**Datum:** 2026-09-26
**Status:** Godkänd design, väntar på implementationsplan
**Bygger på:** `docs/superpowers/specs/2026-09-23-ingest-arbetsflode-design.md` (enstaka sidor). Den processen gäller fortfarande för HTML som inte har något känt format.

## 1. Bakgrund

Den första verkliga leveransen i `ingest/` (guides v1.13.0, 2026-09-26) var ett **paket**, inte en lös sida:

- `UPLOAD.txt`: instruktioner (kontrollsumma, "MUST"-krav, version). Publiceras inte.
- `urls.json`: facit, alltså alla adresser som ska finnas på duke.se efter uppladdningen. Publiceras inte.
- `simulationsmcp/v1/modeling_guides.json` och `guide-schema.json`: data som installerade SimulationsMCP-servrar hämtar **byte för byte**, med https, status 200 och ingen omdirigering. De måste vara uppe innan nästa serverrelease.
- 19 guidesidor under `guides/`: rå engelsk HTML från en generator med fast struktur (`<main class="guide-content">`). Länkarna börjar med `/`, adresserna är mappar (`/guides/queuing/simple-queue/`) och de ska vara permanenta.

**Varje leverans innehåller alltid `UPLOAD.txt` + `urls.json`.** Resten är nytt eller uppdaterat material och varierar från gång till gång.

## 2. Beslut

| Fråga | Beslut |
|---|---|
| Styrning | Manifeststyrd: `urls.json` är facit och `UPLOAD.txt` ger kontrollsummor och krav |
| Godkännande | En plan per leverans, inte per fil |
| Guidesidor | Deterministisk konverterare (skript), inte omdöme per sida |
| `[object Object]` i "Variations" | Ingest bygger avsnittet själv ur `modeling_guides.json` |
| Språk på guider | Innehållet bara på engelska. Ramen (header, footer, CTA) följer SV/EN-knappen. Sidan startar i EN-läge |
| Synlighet | Inga länkar från sajten, `noindex, nofollow` på varje guidesida och `robots.txt` stänger av |
| Adresser | Allt som hör till MCP ligger under `https://duke.se/simulationsmcp/v1/`, med JSON i roten av v1 och guiderna i `v1/guides/…` |
| Avvikelse från leveransens `/guides/` | Ingest skriver om adresserna via en regelfil (beslut 2026-09-26; källan rättas inte) |
| Borttagning | Aldrig automatiskt. Sidor i `site/` som saknas i facit flaggas i planen |

## 3. Adressregler

`mall/adressregler.json`:

```json
{
  "prefix": [
    { "fran": "/guides/", "till": "/simulationsmcp/v1/guides/" }
  ]
}
```

- Regeln används på **tre ställen**: var filen hamnar i `site/`, varje `href` i konverterade sidor och varje adress i `urls.json` innan kontrollen görs.
- En adress som redan börjar med `till` lämnas orörd. Om källan en dag rättas gör regeln alltså ingenting, och planen visar då "regeln användes inte".
- Omskrivning görs bara på adresser som börjar med `fran`. Externa länkar och andra adresser rörs inte.

Exempel: leveransens `guides/queuing/simple-queue/index.html` får adressen `/simulationsmcp/v1/guides/queuing/simple-queue/` och hamnar på `site/simulationsmcp/v1/guides/queuing/simple-queue/index.html`.

## 4. Flödet (`/ingest` med en leverans)

1. **Känn igen leveransen.** Om `ingest/urls.json` finns är det en leverans. Annars används det gamla flödet för enstaka sidor.
2. **Läs styrfilerna.**
   - Ur `urls.json` hämtas listan med adresser, omskriven enligt §3.
   - Ur `UPLOAD.txt` hämtas:
     - version och build-datum, från rubrikraden `built <datum>, guides v<version>`
     - kontrollsummor: varje rad med en ensam sha256-sträng (64 hex-tecken) kopplas till den **senaste föregående raden** i en `curl`/`Invoke-WebRequest`-kontroll som nämner en fil från leveransen
     - MUST-filer: filsökvägar som nämns i det numrerade avsnitt vars rubrik innehåller `MUST`, fram till nästa numrerade avsnitt

     Om formatet inte går att tolka visas en varning i planen och bygget fortsätter bara efter ditt uttryckliga ja.
3. **Para ihop varje fil med en adress.**
   - En fil `X/index.html` motsvarar adressen `/X/`. Andra filer motsvarar `/<sökväg>`.
   - En fil utan matchande adress stoppas och flaggas.
   - En adress utan fil i leveransen är okej om adressen redan finns i `site/`, eftersom den då inte har ändrats. Annars flaggas den som **saknas**.
4. **Klassa varje fil:**

   | Spår | Känns igen på | Hantering |
   |---|---|---|
   | Exakt kopia | allt som inte är `.html` | kopieras byte för byte. Kontrollsumman kontrolleras om `UPLOAD.txt` anger en |
   | Guide | HTML med `<main class="guide-content">` | `mall/guider.py` (§5) |
   | Vanlig sida | annan HTML | befintligt flöde med omdöme (spec 2026-09-23) |

5. **Plan (STOPP).** En plan för hela leveransen, med:
   - version och build-datum
   - antal nya och ändrade filer per spår
   - MUST-filer överst med kontrollsummans status
   - vilka adressregler som användes
   - saknade eller överblivna adresser
   - varningar

   Bygget startar först när du godkänt.
6. **Bygg.**
   - Exakta kopior skrivs till `site/`.
   - Guider går genom `guider.py` till innehållsfiler och sedan genom `bygg-sida.ps1`.
   - Vanliga sidor hanteras som tidigare.
   - `site/robots.txt` skapas eller uppdateras (§7).
7. **Verifiera (§8).**
8. **Arkivera och rapportera.**
   - Hela leveransen (inklusive `UPLOAD.txt` och `urls.json`) flyttas till `ingest/_importerat/<ÅÅÅÅ-MM-DD>/`. Om mappen finns läggs `-2` och så vidare till.
   - Rapporten innehåller deploy-noterna (§9).
   - Ingen commit.

## 5. Guidekonverteraren `mall/guider.py`

**In:** leveransens rotmapp. **Ut:** innehållsfiler under `mall/innehall/simulationsmcp/v1/guides/…/index.html`, en per guide-HTML.

**Metadata** i varje innehållsfil:
- `title:` `<title>` + " | Duke Systems AB"
- `description:` `<meta name="description">` (citattecken ersätts med `&quot;`)
- `page-css:` bara den CSS som komponenterna kräver
- **nytt:** `lang: en`, `robots: noindex, nofollow`

**Mappning** (sektioner i ordning, med växlande ljus och mörk bakgrund enligt `mall/komponenter.md`):

| Generatorns element | Komponent |
|---|---|
| `nav.breadcrumb` | tillbaka-länk i K1 (till sista länken i brödsmulan) |
| `h1` + `p.summary` | K1 hero. Tomt `section-label` ersätts med kategorins namn |
| `section.use-when` | K9 punktlista, ljus |
| `section.blocks` (tabell) | K11 tabell, ljus |
| `section.connections` | K8 terminal, mörk, en `terminal-line` per `<li>` |
| `section.key-parameters` (tabell) | K11 tabell, ljus |
| `section.common-mistakes` | K9 punktlista med ⚠️, ljus |
| `section.key-metrics` | K7 pelare, mörk |
| `section.variations` | byggs ur `modeling_guides.json` → `scenarios.<id>.variations[]`: namn (rubrik), `change` (text) och länk till guiden om `scenario` inte är `null` |
| `section.category` (startsidan) | K3 kort per kategori, med länk och guidernas namn |
| `section.guide-list` (kategorisida) | K3 kort per guide, med namn, beskrivning och länk |
| – | K10 CTA sist (tvåspråkig ram) |

- Sektionsrubrikerna (`h2`) behålls ordagrant. Texten ändras inte.
- **Scenario-id ↔ adress:** kopplingen tas från JSON:ens `categories.<kat>.scenarios` och scenarionamnet (`simple_queue`), jämfört med adressens sista del (`simple-queue`, där `_` blir `-`). Om det inte går att koppla ihop stannar konverteraren med ett felmeddelande.
- **Okänt element** (en ny `section`-klass eller en annan struktur): konverteraren **stannar** och rapporterar det. Den gissar aldrig.
- Alla `href` skrivs om enligt §3.
- Texten HTML-escapas korrekt (`&`, `<`, `>`, `"`).

## 6. Mall och byggskript: ändringar

- **Undersidor i mappar.** Filnamn och mappar i sökvägen följer `^[a-z0-9-]+$`, filen heter `<namn>.html`, och `index.html` är tillåten i undermappar. `site/index.html` i roten byggs aldrig.
- **`{{ROOT}}`** i `mall/prefix.html` och `mall/suffix.html` ersätter varje relativ länk till roten (`index.html#…`). Den blir `""` i roten och `../` per mappnivå. Befintliga sidor i roten ska byggas **byte-identiskt** som i dag.
- **`lang: en`:** sätter `<html lang="en">` och gör att sidan startar i EN-läge (kör `toggleLang()` en gång när sidan laddats).
- **`robots: …`:** lägger till `<meta name="robots" content="…">` i `<head>`.
- Sidor utan de nya metadataraderna byggs byte-identiskt som i dag.
- **`.gitattributes`:** `*.json -text`, så att git aldrig ändrar JSON-filer.

## 7. `robots.txt`

`site/robots.txt` (skapas om den inte finns; regeln läggs till om den saknas):

```
User-agent: *
Disallow: /simulationsmcp/v1/

User-agent: GPTBot
User-agent: ClaudeBot
User-agent: CCBot
User-agent: Google-Extended
User-agent: PerplexityBot
User-agent: Bytespider
Disallow: /simulationsmcp/v1/
```

Det här hindrar bara robotar som följer reglerna. MCP-servrarna påverkas inte. Mer än så kräver åtgärder på servernivå, vilket ligger utanför omfattningen.

## 8. Verifiering

1. Varje omskriven adress i `urls.json` finns i `site/`: `/a/b/` ↔ `site/a/b/index.html`, annars ↔ `site/<sökväg>`.
2. Varje exakt kopia är byte-identisk med leveransen, och kontrollsumman stämmer mot `UPLOAD.txt`.
3. `verifiera.py` körs på varje guidesida utan fel. Den ska nu:
   - godta `/`-länkar (lösta från `--rot`)
   - godta länkar som slutar med `/` (lösta till `index.html`)
   - avkoda procentkodning
4. **Inga inlänkar:** ingen sida utanför `site/simulationsmcp/v1/` innehåller `href` till `/simulationsmcp/v1/` eller till en relativ väg dit.
5. `site/robots.txt` innehåller `Disallow: /simulationsmcp/v1/`.
6. Inget `[object Object]` finns någonstans i `site/`.
7. Varje guidesida har `noindex` och startar i EN-läge (verifieraren kontrollerar `document.documentElement.lang === 'en'` efter att sidan laddats).

## 9. Deploy-noter (skrivs i rapporten, utförs av användaren)

- Ladda upp **hela `site/`** med behållen mappstruktur. JSON-filerna laddas upp i **binärt läge**.
- MUST-filer ska vara uppe före nästa serverrelease.
- Kontroll efteråt:
  ```
  curl -sI https://duke.se/simulationsmcp/v1/modeling_guides.json   # 200, ingen Location:
  curl -s  https://duke.se/simulationsmcp/v1/modeling_guides.json | sha256sum   # = UPLOAD.txt
  curl -sI https://duke.se/simulationsmcp/v1/guides/                # 200
  curl -sI https://duke.se/simulationsmcp.html                      # produktsidan är orörd
  ```
- **Krockrisk:** `site/simulationsmcp.html` och mappen `site/simulationsmcp/` kan av vissa webbservrar och WordPress (permalänkar, "MultiViews") tolkas som samma adress eller ge en omdirigering. Testa detta särskilt första gången.

## 10. Test

- `mall/test/test-bygg-sida.ps1`, utökat med:
  - befintliga sidor är fortfarande byte-identiska
  - en undersida på nivå 3 får `../../../` i header- och footerlänkar
  - `lang: en` och `robots:` hamnar rätt
  - otillåtna mappnamn avvisas
  - `index.html` i roten vägras, men `index.html` i en undermapp är tillåten
- `mall/test/test_guider.py` med den här leveransen (kopieras till `mall/test/fixtures/leverans-2026-09-26/`) som testdata:
  - alla 19 sidor konverteras
  - inget `[object Object]` blir kvar
  - varianter med `scenario` blir länkar
  - alla `href` är omskrivna
  - en okänd `section`-klass stoppar konverteringen
- `mall/test/test_verifiera.py`, utökat med `/`-länkar, länkar som slutar med `/` och kontroll av EN-start.
- Ett leveranstest (`mall/test/test_leverans.py`) med fixturen:
  - ihopparning av filer och adresser
  - omskrivning
  - kontrollsumma (rätt och avsiktligt fel)
  - saknad adress
  - fil utan adress

## 11. Utanför omfattningen

- Spärrar på servernivå.
- Själva uppladdningen.
- Att rätta generatorn "på andra sidan".
- Översättning av guider till svenska.
- Automatisk borttagning av sidor.
