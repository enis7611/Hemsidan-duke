# Duke Systems AB — Webbplats: Kontext & Handoff för Claude Code

> **Syfte med denna fil:** Allt du behöver veta för att fortsätta bygga / underhålla Duke Systems webbplats i Claude Code eller annan miljö. Läs igenom hela innan du börjar koda.

---

## 1. Projektöversikt

**Företag:** Duke Systems AB (duke.se)
**Bransch:** Nordisk distributör av ExtendSim-simuleringsprogramvara sedan 1988, plus konsulttjänster.
**Mål:** Bygga om en föråldrad WordPress-sida till en ren, modern one-page-sajt som speglar dagens tre erbjudanden.

**Tre erbjudanden (det enda företaget säljer idag):**
1. **ExtendSim** — simuleringsmjukvara (CP / DE / Pro) från ANDRITZ Inc. Duke är Nordic Reseller.
2. **ExtendSim MCP** — en MCP-server (Model Context Protocol) som låter AI-assistenter (Claude, ChatGPT, Copilot) styra ExtendSim-modeller med naturligt språk.
3. **Konsulttjänster** — två spår: (a) simuleringskonsult, (b) IT-infrastruktur (Commvault, Windows Server, Microsoft Azure).

**VIKTIGT — vad som INTE längre säljs** (får aldrig dyka upp på sidan):
NetApp, Bridgeworks, Spectra Logic, ForecastPRO, Komprise, Office 365-konsult, Visma, RPA, generell IT-support, TeamViewer-fjärrsupport.

---

## 2. Nuvarande status

**Levererat:** En komplett, fungerande **single-file `index.html`** (~2400 rader, ~94 KB) med all HTML, CSS och JavaScript inline. Inga externa beroenden utom Google Fonts. Helt responsiv. Redo att ladda upp.

**Filen finns som:** `index.html`

---

## 3. Designsystem (LÅST — ändra inte utan anledning)

### Färgtema: "Mint & Stål" (ljus variant)
Alla färger ligger som CSS-variabler i `:root`. Ändra HÄR så slår det igenom överallt.

```css
--navy:      #1B4F4F;   /* Mörka sektioner, header, footer (mellangrön, EJ svart) */
--navy-mid:  #236060;   /* Gradient-partner till navy */
--steel:     #00897B;   /* Accent: länkar, ikoner, section-labels */
--steel-lt:  #4DB6AC;   /* Ljus accent, hover */
--teal:      #00BFA5;   /* MCP-sektionens specialaccent */
--amber:     #D9937A;   /* CTA-knappar — "Koppar-rosa", EJ orange längre */
--amber-dk:  #C07B62;   /* CTA hover */
--bg:        #FAFFFE;   /* Sidans bakgrund — nästan vit med mintunderton */
--white:     #FFFFFF;
--text:      #1B4F4F;
--text-muted:#4A6960;
--border:    #D0EDE9;   /* Kort & avgränsningar */
```

**Designhistorik (så du förstår besluten):**
- Färgtemat valdes från 10 förslag → blev "Mint & Stål" (#3).
- Bakgrunden ljusades upp till `#FAFFFE` (alternativ "D — Nästan vit") för mindre kontrast.
- De mörka fälten sänktes från nästan-svart `#0D2B2B` till `#1B4F4F–#2d7a7a` med gradienter — användaren tyckte kontrasten var för hård.
- CTA-färgen byttes från orange/amber till **Koppar-rosa `#D9937A`** (vald från 15 förslag i familjerna Koppar/Sandguld/Rosenkvarts).

### Typografi
Google Fonts, en enda `<link>`:
```
IBM Plex Serif  (400/600/700) — rubriker H1/H2, produktnamn
IBM Plex Sans   (300/400/500/600) — brödtext, UI, knappar
IBM Plex Mono   (400/500) — section-labels, terminal, tekniska detaljer
Permanent Marker — ENBART logotypen "** Duke Systems **"
```

### Logotyp
Textbaserad, INTE en bildfil. `** Duke Systems **` i Permanent Marker. Asteriskerna (`**`) är i koppar-rosa (`--amber`), texten i vitt. Detta matchar en handskriven logga på en penna som kunden fotograferade — behåll stilen. Permanent Marker ser "bold" ut men är weight 400 (det finns ingen tunnare variant — användaren testade och valde att behålla).

### Tagline (LÅST)
**"Vi löser problemet. Sedan 1988."**
Kärnbudskap: Duke löser kundens problem (säljer inte bara produkter) och arbetar långsiktigt. CTA-texter använder "Berätta om ditt problem" istället för generiskt "Kontakta oss".

---

## 4. Sidstruktur (sektioner i ordning)

| # | Section-id | Innehåll | Bakgrund |
|---|-----------|----------|----------|
| 1 | `#hero` | Tagline + animerat SVG-simuleringsdiagram | Mörk gradient |
| 2 | `#tjanster` | 3 erbjudande-kort (ExtendSim/MCP/Konsult) | Vit |
| 3 | `#varfor` | "Varför Duke" — 4 pelare (37+, 3, ∞, N) | Mörk gradient |
| 4 | `#extendsim` | CP/DE/Pro-produktkort + licensmodeller | Ljus bg |
| 5 | `#mcp` | Flödesdiagram + animerad "terminal" + kompatibilitet | Mörk gradient + teal |
| 6 | `#konsult` | 2 spår: simulering + infrastruktur | Vit |
| 7 | `#branscher` | 6 branschkort | Ljus bg |
| 8 | `#cta-banner` | "Vi har löst liknande problem förut" | Mörk gradient |
| 9 | `#om-oss` | Historik + 4 statistikrutor | Vit |
| 10 | `#kontakt` | Kontaktformulär (mailto) | Ljus bg |
| 11 | `#sekretesspolicy` | GDPR-text | Ljus bg |
| – | `<footer>` | Länkar, kontakt, copyright | Mörk gradient |

---

## 5. Funktioner & hur de fungerar

### Språkväxlare (SV/EN)
- Knapp i headern (`#langToggle`) växlar hela sidan SV ↔ EN utan omladdning.
- All text styrs av ett stort `translations`-objekt i JavaScript med två nycklar: `sv` och `en`.
- Varje textelement i HTML har ett unikt `id` (t.ex. `id="heroTitle"`). Funktionen `applyLang(lang)` sätter `.innerHTML` på varje id från rätt språkobjekt.
- **När du lägger till ny text:** (1) ge elementet ett `id`, (2) lägg till nyckeln i BÅDA språkobjekten, (3) lägg till en `setText('ditt-id', L.dittId)`-rad i `applyLang()`.
- Standardspråk: svenska (`currentLang = 'sv'`).

### Kontaktformulär (mailto)
- `handleSubmit()` validerar namn + e-post + GDPR-checkbox.
- Bygger en `mailto:info@duke.se`-länk med ämnesrad (från ärende-dropdown) och förformaterad brödtext (namn, e-post, ärende, meddelande).
- Öppnar besökarens e-postklient. **Ingen server, ingen backend.**
- Visar ett grönt "Tack!"-meddelande efter klick.
- Fungerar på båda språken.
- **OBS:** Om kunden senare vill ha riktig formulärhantering — överväg Formspree (gratis, ingen server) eller, eftersom de kör WordPress, ett plugin som Contact Form 7 / WPForms.

### Animationer
- Scroll-reveal via `IntersectionObserver` — element med klassen `.reveal` tonar in när de scrollas in i vy. `.reveal-delay-1/2/3/4` ger förskjutning.
- Hero: animerat SVG med pulserande noder och flödeslinjer (CSS `@keyframes`).
- MCP-terminal: statisk "konversation" som visar exempelkommandon.
- Sticky header med skugga som tonar in på scroll.
- Hamburger-meny på mobil (`< 768px`).

---

## 6. Externa länkar (verifierade fungerande)

- `https://extendsim.com` — tillverkarens sida
- `https://extendsim.com/products/line/extendsimcp` (+ `/de`, `/pro`)
- `mailto:info@duke.se`
- Interna ankarlänkar: alla 8 verifierade mot matchande section-id.

---

## 7. Att göra / nästa steg (förslag)

**Inte gjort än:**
- [ ] Riktig formulärbackend (om mailto inte räcker) — Formspree eller WP-plugin.
- [ ] Riktiga produktbilder/skärmdumpar från ExtendSim (med tillstånd) — just nu används CSS/SVG-grafik och emoji-ikoner.
- [ ] Generera och lägga in Gemini Imagen-bilder (prompts finns i PRD v1.1, se nedan).
- [ ] WordPress-integration (se sektion 8).
- [ ] 301-redirects från gamla URL:er (lista i PRD).
- [ ] Riktig OG-bild för social delning (1200×630).
- [ ] Cookie-banner om analytics läggs till (just nu inga cookies → ingen banner krävs).
- [ ] Byt emoji-ikoner mot SVG-ikoner för mer professionell känsla (valfritt).

**Relaterade dokument från projektet:**
- `duke_systems_prd_v1_1.md` — full PRD med sitemap, Gemini-bildprompts, SEO-nyckelord, genomförandechecklista.

---

## 8. WordPress-integration

Sidan är byggd som fristående HTML men ska in i WordPress. Två vägar:

**A) Enklast — Custom HTML:**
Skapa en tom sidmall eller använd ett plugin som "Insert HTML Snippet" / en Custom HTML-block. Klistra in hela `index.html`. Fungerar men svårt att underhålla i WP-admin.

**B) Rekommenderat — Konvertera till tema/blockmall:**
- IBM Plex finns gratis via Google Fonts (bekräftat under SIL OFL 1.1) — enkelt att enqueua i `functions.php`.
- Bryt ut CSS till en `style.css`, JS till `main.js`.
- Gör om sektionerna till WordPress-block eller en page template.
- Behåll CSS-variablerna i `:root` så temat går att färgjustera centralt.

**SEO (för WP):** primära nyckelord: `ExtendSim Sverige`, `simuleringsmjukvara Norden`, `produktionssimulering`, `ExtendSim MCP`, `Commvault konsult Sverige`. Använd Yoast eller Rank Math.

---

## 9. Tekniska konventioner (om du fortsätter koda)

- **En fil, allt inline.** Behåll det så länge sajten är en one-pager — det gör den lätt att ladda upp.
- **CSS-variabler för allt färgrelaterat.** Ändra aldrig hårdkodade hex om en variabel finns.
- **Varje synlig textsträng ska ha ett `id` + nyckel i båda språkobjekten.** Annars bryts språkväxlaren.
- **Mobil-brytpunkt:** `768px` (och `1024px` för grid-justeringar, `480px` för småskärm).
- **Inga ramverk.** Vanlig HTML/CSS/JS. Inga byggsteg.
- Testa alltid språkväxlaren efter textändringar (en saknad `setText` syns direkt).

---

## 10. Snabb sanity-check innan deploy

1. Öppna sidan, klicka SV/EN — all text ska byta, inget ska bli tomt.
2. Scrolla igenom — alla sektioner tonar in, footern syns.
3. Fyll i formuläret, tryck skicka — e-postklienten öppnas med rätt mottagare/innehåll.
4. Testa på mobil — hamburgermeny fungerar, allt staplas snyggt.
5. Klicka alla nav-länkar — scrollar till rätt sektion.
6. Kontrollera att inga avvecklade produkter (NetApp, Bridgeworks etc.) finns kvar.

---

*Skapad som handoff-kontext för fortsatt arbete. Sidan är i körbart skick — detta dokument beskriver nuläget, designbesluten och vad som återstår.*
