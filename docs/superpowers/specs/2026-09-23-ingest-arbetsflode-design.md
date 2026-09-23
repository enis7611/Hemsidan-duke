# Ingest-arbetsflöde – design

**Datum:** 2026-09-23
**Status:** Godkänd design, väntar på implementationsplan

## 1. Syfte

Jonas lägger **rena HTML-filer utan styling** i `ingest/` (valfri undermappsstruktur). Ett arbetsflöde som Claude kör ("kör ingest" / `/ingest`) ska:

1. klä på sidorna med Duke-designen (Mint & Stål) så att de ser ut som befintliga produktsidor,
2. göra dem fullt tvåspråkiga (SV → EN),
3. placera dem i webbträdet och länka in dem,
4. verifiera resultatet,

så att `site/` därefter är redo att deployas.

**Framgångskriterier**
- En importerad sida går inte att skilja från de handbyggda undersidorna vad gäller head, header, footer, CSS och sektionsstil.
- SV/EN-växling fungerar utan tomma element.
- Jonas godkänner en plan innan något skrivs.
- Samma sida kan importeras igen som uppdatering.

## 2. Beslut

| Fråga | Beslut |
|---|---|
| Form | Arbetsflöde som Claude kör (projektskill), inte ett fristående skript |
| Beslutsnivå | Claude föreslår en plan per fil, Jonas godkänner innan bygget |
| Deploy-katalog | Fast katalog `site/` (flyttad från `src/release-2026-06-13/` med `git mv`) |
| Språk | Råfiler på svenska. Claude översätter till engelska. EN-rubrik och ingress visas i planen |
| Nya sidor / uppdateringar | Båda. En befintlig sida känns igen och innehållet ersätts |
| Paketering | Alternativ A: skill + mall + hopsättningsskript |
| Mallens placering | `mall/` i rotkatalogen, bredvid `site/`, så att `site/` är exakt det som laddas upp |
| Commit | Aldrig automatiskt. Jonas granskar först |

## 3. Katalogstruktur

```
ingest/                         inkorg, valfri struktur, undermappar OK
  _importerat/ÅÅÅÅ-MM-DD/       original flyttas hit efter lyckad import

site/                           deploy-katalog (tidigare src/release-2026-06-13/)
  index.html                    handredigerad, byggs inte av skriptet
  simulationsmcp.html
  simulationsmcp-build.html
  extendmqtt.html
  img/                          bilder som följer med importerade sidor
  <nya sidor>.html

mall/                           deployas inte
  prefix.html                   <!DOCTYPE> t.o.m. header, med platshållare
  suffix.html                   <footer> t.o.m. </html>, inkl. JS
  komponenter.md                sektionsmönster med HTML-snuttar + när de passar
  bygg-sida.ps1                 prefix + innehåll + suffix → site/<namn>.html
  verifiera.py                  Playwright-kontroll av en byggd sida
  innehall/<namn>.html          innehållsdelen per undersida (källan vid ombyggnad)

.claude/skills/ingest/SKILL.md  arbetsflödet
```

`src/index.html` och `src/variants/` lämnas orörda.

### 3.1 Mall och platshållare

`prefix.html` klipps ut ur `extendmqtt.html` (rad 1 t.o.m. slutet av header). Enligt jämförelsen mellan de tre undersidorna skiljer sig prefixen bara i `<title>` och sidspecifik CSS sist i `<style>`, och suffixen (`<footer>` → slut) är identiska.

Platshållare i `prefix.html`:
- `{{TITLE}}`: sidans `<title>`
- `{{DESCRIPTION}}`: `<meta name="description">`
- `{{PAGE_CSS}}`: sidspecifik CSS, infogas sist i `<style>`, oftast tom

### 3.2 Innehållsfil

`mall/innehall/<namn>.html` innehåller allt mellan header och `<footer>` (hero, sektioner, CTA). Metadata ligger i en inledande kommentar:

```html
<!--
title: ExtendMQTT – MQTT för ExtendSim | Duke Systems AB
description: ...
page-css:
  .spec-row{...}
-->
```

### 3.3 `bygg-sida.ps1`

- Indata: sökväg till innehållsfil.
- Läser metadata-kommentaren, ersätter platshållarna i `prefix.html`, konkatenerar prefix + innehåll (utan metadata-kommentaren) + suffix och skriver `site/<namn>.html` i UTF-8 utan BOM.
- Avbryter med tydligt fel om en platshållare saknar värde (utom `page-css`, som får vara tom).
- `index.html` byggs aldrig av skriptet.

## 4. Arbetsflödet (SKILL.md)

### Steg 1: Inventera
Lista alla `.html` rekursivt i `ingest/`, utom `_importerat/`. Om inkorgen är tom meddelas det och flödet avslutas.

### Steg 2: Analysera varje fil (skriver ingenting)
- **Typ:** produkt, tjänst, bransch, nyhet, juridiskt, annat.
- **Ny eller uppdatering:** jämför titel, rubriker och ämne mot sidorna i `site/`.
- **Filnamn:** url-vänligt, gemener, bindestreck, å/ä/ö → a/a/o. Webbträdet är platt, allt ligger direkt i `site/`.
- **Inlänkning:** var sidan länkas från (t.ex. "Läs mer →" i `#mcp`, kort i `#branscher`, footer).
- **Innehållskontroll** mot HANDOFF §1 och projektminnet:
  - inga utgångna produkter (NetApp, Bridgeworks, Spectra Logic, ForecastPRO, Komprise, Office 365-konsult, Visma, RPA, generell IT-support, TeamViewer)
  - produktnamn SimulationsMCP / SimulationsMCP Build / ExtendMQTT, aldrig "ExtendSim MCP"
  - tagline "Vi löser problemet. Sedan 1988." oförändrad
  - CTA "Berätta om ditt problem"
- **Komponentval:** vilket mönster i `komponenter.md` varje del får.

### Steg 3: Plan och godkännande
Per fil visas en tabell: typ, ny/uppdatering, målfil, inlänkning, komponentval, varningar och vad som kortats, samt **EN-rubrik och EN-ingress**. Jonas svarar per fil: ja / ändra / hoppa över. Inget byggs utan ja.

### Steg 4: Bygg
1. Skriv `mall/innehall/<namn>.html` med SV + EN (`data-sv`/`data-en`, eller `id` + `setText` + nycklar i båda språken i `translations` där sidan kräver det).
2. Kör `mall/bygg-sida.ps1`.
3. Kopiera bilder som ligger bredvid källfilen till `site/img/` och skriv om `src`.
4. Lägg in länken på den godkända platsen. Ny synlig text följer tvåspråksreglerna i CLAUDE.md.

Vid **uppdatering** ersätts innehållsfilen. Befintlig inlänkning behålls om inte planen säger annat.

### Steg 5: Verifiera
Kör `mall/verifiera.py` (Playwright, via `python -m http.server` i `site/`):
- sidan laddar utan konsolfel
- SV → EN → SV: inget synligt textelement är tomt i EN
- alla `href` pekar på något som finns (ankare och sidor i `site/`)
- hamburgermenyn öppnas vid 375 px bredd
- inlänkningen från källsidan leder till den nya sidan
- skärmdumpar: SV desktop och EN mobil

### Steg 6: Städa och rapportera
- Originalet flyttas till `ingest/_importerat/ÅÅÅÅ-MM-DD/` (relativ undermappsstruktur behålls).
- Rapport: ändrade filer, varningar, skärmdumpar.
- Ingen commit.

### Felhantering
- Fil som inte går att tolka (tom, trasig HTML, oklart ämne): hoppas över, ligger kvar i `ingest/` och orsaken anges i planen.
- Verifieringen misslyckas: originalet ligger kvar i `ingest/` tills sidan är fixad, och felet rapporteras.

## 5. Påklädningsregler (`komponenter.md`)

Målet är att en rå sida ser ut som de tre produktsidorna. Befintliga mönster används och nya visuella element hittas inte på.

**Ryggrad (fast ordning)**
1. **Produkt-hero:** mörk teal-gradient, `section-label`, H1, ingress, 1–2 knappar. Innehåll: filens första rubrik och första stycke.
2. **Innehållssektioner:** en per `<h2>`, växlande bakgrund vit → `var(--bg)` → mörk gradient.
3. **CTA-band** sist: "Berätta om ditt problem" → `index.html#kontakt`.

**Mappning**

| Rått innehåll | Komponent |
|---|---|
| Lista, 3–6 punkter med egna rubriker | `services-grid` + `service-card` + `card-icon` |
| Numrerade steg / "så funkar det" | stegflöde (ur SimulationsMCP "Så funkar det") |
| Nyckel–värde, tekniska fakta | `spec-row` på mörk bakgrund (ur ExtendMQTT "Prestanda") |
| 2 parallella spår/alternativ | `konsult-grid` + `konsult-track` + `track-item` |
| 3–4 korta påståenden | `pillars` / `pillar` |
| Kommandon, kod, exempeldialog | terminalblock (ur SimulationsMCP "I praktiken") |
| Löpande text | `section-header` + brödtext i `container`, max ~70 tecken breda rader |
| `<table>` | stylad tabell (ny komponent, definieras i katalogen vid implementation) |
| `<img>` | behålls, filen kopieras till `site/img/` |

**Regler**
- Alla sektioner får `reveal` + `reveal-delay-N`.
- Bara CSS-variabler från `:root`. Inga nya hårdkodade färger (heroernas befintliga gradienter undantagna).
- Innehåll som inte passar något mönster blir brödtext och flaggas i planen. Nya komponenter läggs till i katalogen först efter godkännande.
- **Texten ändras inte i sak.** Ingress får kortas för heron och långa stycken delas upp. Allt som kortats redovisas i planen.

## 6. Engångsmigrering

1. `git mv src/release-2026-06-13 site`
2. Klipp ut `mall/prefix.html` (med platshållare) och `mall/suffix.html` ur `site/extendmqtt.html`.
3. Skapa `mall/innehall/` för `extendmqtt`, `simulationsmcp` och `simulationsmcp-build` (innehåll + metadata inkl. sid-CSS).
4. Bygg om de tre sidorna med `bygg-sida.ps1` och `diff` mot originalen. Förväntat: identiskt, bortsett från blanktecken och sid-CSS:ens exakta position i `<style>`.
5. Kontrollera att nav och "Läs mer →" från `site/index.html` fungerar.
6. Skapa `ingest/` med `_importerat/` (`.gitkeep`).

## 7. Dokumentation

- **CLAUDE.md:** `site/` är deploy-katalogen, `mall/` + ingest-flödet, samt att `src/index.html` är historisk.
- **HANDOFF_CONTEXT.md:** kort avsnitt om ingest-arbetsflödet.
- **Projektminne** (site-redesign-direction): ny sökväg `site/`.

## 8. Utanför omfattningen

Deploy-steget, undermappar i `site/`, automatisk commit, testramverk och WordPress-export.
