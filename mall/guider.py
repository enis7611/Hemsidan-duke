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
