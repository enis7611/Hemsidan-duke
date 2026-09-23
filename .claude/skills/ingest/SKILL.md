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
7. **Komponentval:** mappa varje del av råfilen till K1–K12 enligt tabellen i `mall/komponenter.md`. Notera delar som inte passar (blir K9 + flagga). Planera bakgrunderna samtidigt: K5, K7 och K8 kräver mörk sektion (K2m), ljus och mörk ska växla och sektionen före K10 ska vara ljus.
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
  Finns filen redan i arkivet (samma fil importerad två gånger samma dag): lägg till `-2`, `-3` … före `.html`. Skriv aldrig över ett arkiverat original.
- Misslyckade eller överhoppade filer ligger kvar i `ingest/`.
- Rapportera:
  - per fil: resultat (klar / misslyckad / överhoppad), målfil, inlänkning, varningar
  - ändrade filer (`git status --short`)
  - skärmdumparna (SV desktop, EN mobil)
- Avsluta med: "Inget är committat. Titta i `site/` och säg till när jag ska committa."
