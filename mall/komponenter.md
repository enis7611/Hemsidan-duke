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
| `<pre>`, `<code>`-block, kommandon, exempeldialog | K8 Terminal (i mörk sektion) |
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

## Komponenter

### K1: Produkt-hero

**När:** alltid först. Innehåller råfilens första rubrik (`<h1>`) och första stycke (ingress, max ~2 meningar).
**Källa:** `site/extendmqtt.html`, `<!-- ─── PRODUKT-HERO`.
Tillbaka-länken pekar på den sektion i `index.html` där sidan länkas in. Det andra stycket, knappraden och siffraden är valfria.
Siffraden används bara när råfilen har 2–4 korta nyckeltal. Den andra knappen pekar på sidans första sektion (ge den `id`).

```html
<!-- ─── PRODUKT-HERO ─────────────────────────────────────── -->
<section id="top" style="background:linear-gradient(135deg,#1B4F4F 0%,#236060 45%,#2d7a7a 100%);padding:140px 0 80px;position:relative;overflow:hidden;">
  <div class="hero-grid-bg"></div>
  <div class="hero-glow"></div>
  <div class="container" style="position:relative;z-index:2;">
    <a href="index.html#branscher" data-sv="← Tillbaka till översikten" data-en="← Back to overview" style="display:inline-flex;align-items:center;gap:0.4rem;font-family:var(--mono);font-size:0.72rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--steel-lt);text-decoration:none;margin-bottom:1.5rem;">← Tillbaka till översikten</a>
    <div style="display:inline-flex;align-items:center;gap:0.6rem;margin-bottom:1rem;flex-wrap:wrap;">
      <span style="font-size:2rem;">🏭</span>
      <span class="section-label" style="color:var(--steel-lt);margin:0;" data-sv="Kategori · underkategori" data-en="Category · subcategory">Kategori · underkategori</span>
    </div>
    <h1 style="color:#fff;margin-bottom:1.25rem;" data-sv="Sidans rubrik" data-en="Page heading">Sidans rubrik</h1>
    <p style="font-size:1.15rem;color:rgba(255,255,255,0.8);max-width:640px;margin-bottom:1rem;" data-sv="Ingress på svenska." data-en="Lead paragraph in English.">Ingress på svenska.</p>
    <p style="color:rgba(255,255,255,0.6);max-width:640px;margin-bottom:2.25rem;" data-sv="Valfritt andra stycke." data-en="Optional second paragraph.">Valfritt andra stycke.</p>
    <div style="display:flex;gap:1rem;flex-wrap:wrap;">
      <a href="index.html#kontakt" class="btn btn-primary" data-sv="Berätta om ditt problem" data-en="Tell us about your problem">Berätta om ditt problem</a>
      <a href="#forsta-sektionen" class="btn btn-ghost" data-sv="Läs mer" data-en="Read more">Läs mer</a>
    </div>
    <div style="display:flex;gap:2.5rem;flex-wrap:wrap;margin-top:3rem;">
      <div><div style="font-family:var(--serif);font-size:2rem;font-weight:700;color:#fff;line-height:1;">42</div><div style="font-family:var(--mono);font-size:0.7rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--steel-lt);margin-top:0.3rem;" data-sv="nyckeltal" data-en="key figure">nyckeltal</div></div>
    </div>
  </div>
</section>
```

### K2: Sektionshuvud (ljus och mörk sektion)

**När:** en per `<h2>` i råfilen. Omsluter efterföljande komponenter i samma sektion.
**Källa:** ljus: `site/extendmqtt.html` "FEM BLOCK". Mörk: "ANVÄNDNINGSFALL".
Ljus sektion har bakgrund `var(--white)` eller `var(--bg)`. Stycket i `.section-header` är valfritt.

Ljus:
```html
<!-- ─── RUBRIK I VERSALER ─────────────────────────────────── -->
<section id="forsta-sektionen" style="background:var(--white);">
  <div class="container">
    <div class="section-header reveal">
      <span class="section-label" data-sv="Etikett" data-en="Label">Etikett</span>
      <h2 style="color:var(--navy);" data-sv="Sektionsrubrik" data-en="Section heading">Sektionsrubrik</h2>
      <p data-sv="Inledande mening." data-en="Introductory sentence.">Inledande mening.</p>
    </div>
    <!-- komponent(er) här -->
  </div>
</section>
```

Mörk (K2m):
```html
<!-- ─── RUBRIK I VERSALER ─────────────────────────────────── -->
<section style="background:linear-gradient(160deg,#1B4F4F 0%,#1E5A5A 50%,#236060 100%);position:relative;overflow:hidden;">
  <div class="mcp-bg-pattern"></div>
  <div class="container" style="position:relative;z-index:2;">
    <div class="section-header reveal">
      <span class="section-label" style="color:var(--teal);" data-sv="Etikett" data-en="Label">Etikett</span>
      <h2 style="color:#fff;" data-sv="Sektionsrubrik" data-en="Section heading">Sektionsrubrik</h2>
      <p style="color:rgba(255,255,255,0.72);" data-sv="Inledande mening." data-en="Introductory sentence.">Inledande mening.</p>
    </div>
    <!-- komponent(er) här -->
  </div>
</section>
```

### K3: Kortrutnät

**När:** 3–6 punkter som var och en har en egen rubrik. Ljus sektion.
**Källa:** `site/extendmqtt.html` "FEM BLOCK". Ett `.service-card` per punkt. `reveal-delay-1/2/3` upprepas i tur och ordning.
Ikonfärg: `blue`, `teal` eller `amber`. Välj en passande emoji per kort.

```html
<div class="services-grid">
  <div class="service-card reveal reveal-delay-1"><div class="card-icon teal">📈</div><h3 data-sv="Rubrik" data-en="Heading">Rubrik</h3><p data-sv="Kort beskrivning." data-en="Short description.">Kort beskrivning.</p></div>
</div>
```

### K4: Stegflöde

**När:** numrerade steg, ett förlopp eller "så funkar det" (3–6 korta steg). Passar i både ljus och mörk sektion.
**Källa:** `site/simulationsmcp-build.html` "ITERATIVT" (chipraden).
`⟲` sist används bara om flödet är en loop. Det finns en mörk och en ljus variant. Välj den som matchar sektionens bakgrund.

**Sid-CSS:**
```css
  .mcp-cat{font-family:var(--mono);font-size:0.72rem;letter-spacing:0.05em;border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:7px 14px;color:rgba(255,255,255,0.78);white-space:nowrap;}
```

Mörk sektion:
```html
<div class="reveal reveal-delay-1" style="display:flex;justify-content:center;align-items:center;gap:0.6rem;flex-wrap:wrap;margin-bottom:2.5rem;">
  <span class="mcp-cat" data-sv="1 · Första steget" data-en="1 · First step">1 · Första steget</span>
  <span style="color:rgba(255,255,255,0.4);">→</span>
  <span class="mcp-cat" data-sv="2 · Andra steget" data-en="2 · Second step">2 · Andra steget</span>
  <span style="color:rgba(255,255,255,0.4);">→</span>
  <span class="mcp-cat" data-sv="3 · Tredje steget" data-en="3 · Third step">3 · Tredje steget</span>
</div>
```

Ljus sektion:
```html
<div class="reveal reveal-delay-1" style="display:flex;justify-content:center;align-items:center;gap:0.6rem;flex-wrap:wrap;margin-bottom:2.5rem;">
  <span class="mcp-cat" style="color:var(--navy);border-color:var(--border);background:var(--white);" data-sv="1 · Första steget" data-en="1 · First step">1 · Första steget</span>
  <span style="color:var(--text-muted);">→</span>
  <span class="mcp-cat" style="color:var(--navy);border-color:var(--border);background:var(--white);" data-sv="2 · Andra steget" data-en="2 · Second step">2 · Andra steget</span>
  <span style="color:var(--text-muted);">→</span>
  <span class="mcp-cat" style="color:var(--navy);border-color:var(--border);background:var(--white);" data-sv="3 · Tredje steget" data-en="3 · Third step">3 · Tredje steget</span>
</div>
```

### K5: Specifikationslista

**När:** nyckel–värde-par och tekniska fakta. Endast i mörk sektion (K2m).
**Källa:** `site/extendmqtt.html` "PRESTANDA". Ett `.spec-row` per par. Värden utan språk (siffror, namn) behöver inga data-attribut.

**Sid-CSS:**
```css
  .spec-row{display:flex;justify-content:space-between;gap:1rem;padding:0.85rem 0;border-bottom:1px solid rgba(255,255,255,0.12);}
  .spec-row:last-child{border-bottom:none;}
  .spec-row .k{color:rgba(255,255,255,0.7);font-size:0.9rem;}
  .spec-row .v{color:#fff;font-weight:500;font-size:0.9rem;text-align:right;font-family:var(--mono);}
```

```html
<div style="max-width:620px;margin:0 auto;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.13);border-radius:12px;padding:1.5rem 2rem;">
  <div class="spec-row"><span class="k" data-sv="Egenskap" data-en="Property">Egenskap</span><span class="v">~100 µs</span></div>
</div>
```

### K6: Två spår

**När:** två parallella listor ("Ingår / Ingår inte", "Idag / Senare", "Simulering / IT"). Ljus sektion.
**Källa:** `site/extendmqtt.html` "OMFATTNING & STATUS". Ett `.track-item` per punkt. Det andra spåret får `background:var(--bg)`.

```html
<div class="konsult-grid">
  <div class="konsult-track reveal reveal-delay-1">
    <h3 data-sv="Första spåret" data-en="First track">Första spåret</h3>
    <div class="track-items">
      <div class="track-item"><div class="track-item-icon">✅</div><div><h4 data-sv="Punkt" data-en="Item">Punkt</h4><p data-sv="Kort beskrivning." data-en="Short description.">Kort beskrivning.</p></div></div>
    </div>
  </div>
  <div class="konsult-track reveal reveal-delay-2" style="background:var(--bg);">
    <h3 data-sv="Andra spåret" data-en="Second track">Andra spåret</h3>
    <div class="track-items">
      <div class="track-item"><div class="track-item-icon">🔜</div><div><h4 data-sv="Punkt" data-en="Item">Punkt</h4><p data-sv="Kort beskrivning." data-en="Short description.">Kort beskrivning.</p></div></div>
    </div>
  </div>
</div>
```

### K7: Pelare

**När:** 3–4 korta påståenden eller användningsfall med rubrik. Mörk sektion (K2m).
**Källa:** `site/extendmqtt.html` "ANVÄNDNINGSFALL". En `.pillar` per påstående, `reveal-delay-1` … `4`.

```html
<div class="pillars">
  <div class="pillar reveal reveal-delay-1"><div style="font-size:1.8rem;margin-bottom:0.75rem;">🔄</div><h3 data-sv="Rubrik" data-en="Heading">Rubrik</h3><p data-sv="Kort beskrivning." data-en="Short description.">Kort beskrivning.</p></div>
</div>
```

### K8: Terminal

**När:** kommandon, kod, loggar eller en exempeldialog (användare ↔ AI). **Endast i mörk sektion (K2m).** På ljus bakgrund blir den grå och urtvättad.
**Källa:** `site/simulationsmcp-build.html` "DEMO".
Talare: `Du`/`You` (`.terminal-cmd`) eller `AI` (`.terminal-result`, teal prompt). Ren kod: utelämna prompten och använd `.terminal-result`. Kod och kommandon översätts inte.

```html
<div class="mcp-terminal reveal" style="background:rgba(0,0,0,0.4);">
  <div class="terminal-bar">
    <div class="terminal-dot"></div><div class="terminal-dot"></div><div class="terminal-dot"></div>
    <span class="terminal-title">Titel</span>
  </div>
  <div class="terminal-body">
    <div class="terminal-line"><span class="terminal-prompt" data-sv="Du" data-en="You">Du</span><span class="terminal-cmd" data-sv="Fråga på svenska" data-en="Question in English">Fråga på svenska</span></div>
    <div class="terminal-line"><span class="terminal-prompt" style="color:var(--teal);">AI</span><span class="terminal-result" data-sv="→ svar ✓" data-en="→ answer ✓">→ svar ✓</span></div>
  </div>
</div>
```

### K9: Brödtext

**När:** löpande text utan struktur. Placeras efter K2 i en ljus sektion.

```html
<div class="reveal" style="max-width:680px;margin:0 auto;">
  <p style="margin-bottom:1.1rem;" data-sv="Stycke på svenska." data-en="Paragraph in English.">Stycke på svenska.</p>
</div>
```


### K10: CTA-band

**När:** alltid sist. Rubriken och stycket anpassas till sidan. Knapptexten är låst.
**Källa:** `site/extendmqtt.html` `<!-- ─── CTA`.

```html
<!-- ─── CTA ──────────────────────────────────────────────── -->
<section style="background:linear-gradient(135deg,#1B4F4F 0%,#236060 50%,#287070 100%);padding:80px 0;text-align:center;">
  <div class="container" style="position:relative;z-index:2;">
    <h2 style="color:#fff;margin-bottom:1rem;" data-sv="Fråga som knyter an till sidan?" data-en="Question tied to the page?">Fråga som knyter an till sidan?</h2>
    <p style="color:rgba(255,255,255,0.75);max-width:480px;margin:0 auto 2.5rem;" data-sv="En mening om vad vi kan hjälpa till med." data-en="One sentence on how we can help.">En mening om vad vi kan hjälpa till med.</p>
    <a href="index.html#kontakt" class="btn btn-primary" data-sv="Berätta om ditt problem" data-en="Tell us about your problem">Berätta om ditt problem</a>
  </div>
</section>
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
