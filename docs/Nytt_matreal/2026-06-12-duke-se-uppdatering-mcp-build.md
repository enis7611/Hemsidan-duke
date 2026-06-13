# Informationspunkt: uppdatering av www.duke.se — ExtendSim MCP utökas med blockbyggande

Datum: 2026-06-12
Status: underlag (inte publicerad text)
Berör: sektionen `#mcp` ("ExtendSim möter AI") på www.duke.se

---

## 1. Nuläge på sajten

www.duke.se är en enkelsidig sajt (ankarsektioner) med menyn:
**ExtendSim · ExtendSim MCP NY · Konsult · Om oss · Kontakt**

Sektionen "ExtendSim möter AI — styr din simulering med naturligt språk"
beskriver i dag **en** förmåga:

> AI-assistenter (Claude, ChatGPT, Copilot) kommunicerar direkt med dina
> simuleringsmodeller — kör scenarier, hittar flaskhalsar, jämför kapacitet,
> räknar ROI.

Det motsvarar den första MCP-servern (SimulationsMCP, ~90 verktyg som
opererar på **befintliga** modeller och block).

## 2. Förändringen

Duke Systems har nu en **andra MCP-server** (SimulationsMCP_build, 22 verktyg,
leveransklar 2026-06-11) som gör något ingen annan erbjuder:

**AI:n bygger egna ExtendSim-block från grunden** — ModL-kod, dialogrutor,
kontakter (connectors), ikon och animering — och kompilerar dem till ett
färdigt bibliotek. Inget manuellt arbete i Library Manager.

Tillsammans bildar de två servrarna en komplett kedja:

```
            ExtendSim MCP — två servrar, en kedja
  ─────────────────────────────────────────────────────────────

  "Jag behöver ett block som      "Kör modellen och visa
   styr ett beställningslager"     var flaskhalsen sitter"
            │                               │
            ▼                               ▼
  ┌───────────────────┐          ┌───────────────────────┐
  │   BYGGAR-MCP:n    │          │     MODELL-MCP:n      │
  │  (SimulationsMCP  │          │   (SimulationsMCP)    │
  │      _build)      │          │                       │
  │                   │  .lbr-   │  placerar block,      │
  │  skapar block:    │  biblio- │  kopplar ihop,        │
  │  · ModL-kod       │──tek────▶│  kör simuleringen,    │
  │  · dialog         │          │  läser resultat,      │
  │  · kontakter      │          │  itererar scenarier   │
  │  · ikon/animering │          │                       │
  │  · kompilering    │          │                       │
  └───────────────────┘          └───────────────────────┘
            │                               │
            └───────────┬───────────────────┘
                        ▼
        Användaren beskriver sitt problem på svenska
        eller engelska — AI:n gör resten, i ExtendSim.
```

## 3. Föreslagen sajtändring (struktur)

Minsta ingrepp: utöka befintliga `#mcp`-sektionen med ett andra "ben".
Sektionen får två kort sida vid sida i stället för ett flöde:

```
  ┌─────────────────────────────────────────────────────────────┐
  │        ExtendSim möter AI — från idé till körd modell       │
  │                                                             │
  │  ┌──────────────────────────┐  ┌──────────────────────────┐ │
  │  │  STYR DINA MODELLER      │  │  BYGG EGNA BLOCK   [NYTT]│ │
  │  │                          │  │                          │ │
  │  │  Kör scenarier, hitta    │  │  Beskriv blocket du      │ │
  │  │  flaskhalsar, jämför     │  │  behöver — AI:n skriver  │ │
  │  │  kapacitet, räkna ROI —  │  │  ModL-koden, ritar       │ │
  │  │  med naturligt språk.    │  │  dialog, kontakter och   │ │
  │  │                          │  │  ikon, och kompilerar    │ │
  │  │  (befintlig text/demo)   │  │  ett färdigt bibliotek.  │ │
  │  └──────────────────────────┘  └──────────────────────────┘ │
  │                                                             │
  │   Claude · ChatGPT · Copilot          [Boka demo]           │
  └─────────────────────────────────────────────────────────────┘
```

Alternativ (större ingrepp): egen ankarsektion `#mcp-build` med eget
menyalternativ. Rekommendation: **börja med kortvarianten** — sajten är
medvetet kompakt och en sektion per erbjudande räcker.

## 4. Föreslagen brödtext (utkast, svenska)

> **Bygg egna block — utan att öppna Library Manager**
>
> ExtendSim MCP kan nu mer än att styra modeller. Beskriv blocket du
> behöver — "ett lagerblock med beställningspunkt, två parametrar och en
> nivåindikator" — så skapar AI-assistenten det åt dig: ModL-källkod,
> dialogruta, in- och utkontakter, ikon och animering. Blocket kompileras
> och landar i ett eget bibliotek, redo att placeras i din modell.
>
> Tillsammans med modellstyrningen blir kedjan komplett: AI:n bygger
> blocken, sätter ihop modellen och kör simuleringen — du beskriver
> problemet och granskar resultatet.

Engelsk variant tas fram när den svenska är godkänd (sajten har
engelskt språkval).

## 5. Vad vi kan lova (ärlighetsgränser)

Texten ovan håller sig inom vad som är levererat och verifierat:

| Påstående på sajten | Täckning i produkten |
|---|---|
| AI skriver ModL-kod och kompilerar | `block_set_source` + kompilering via placering, verifierat live |
| Dialog, kontakter, ikon, animering från spec | `block_create_from_spec` + 19 mutationsverktyg, 490+ enhetstester |
| Färdigt bibliotek utan manuellt arbete | Donatorfri syntes (Phase 5), inga skelett-/mallberoenden |
| Valfria namn på block och kontakter | Arbiträra UTF-16-namn levererat 2026-05-15 |

**Lova inte** (ännu): andra basformer än Brick byggda från grunden
(Activity/Queue-utseende löses i dag med Brick + egen ikon), spec-roundtrip
(läsa tillbaka ett block till redigerbar spec). Båda är medvetet
framskjutna — se `NEXT_SESSION.md`.

## 6. Öppna beslut innan publicering

1. Produktnamn utåt: "ExtendSim MCP" som paraply för båda servrarna, eller
   två namn (t.ex. "MCP Modeller" / "MCP Byggare")? Utkastet ovan antar
   **ett paraplynamn** — enklare budskap.
2. Demo-material: ett kort skärmklipp (AI-prompt → färdigt block i Library
   Manager) skulle bära sektionen. Artefakter finns i `artifacts/`.
3. Menyetiketten "ExtendSim MCP NY" — när "NY"-flaggan tas bort kan
   undertiteln i stället bli "Styr & bygg med AI".
