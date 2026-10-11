#!/usr/bin/env python3
"""
Lotus Sun Energy website, build step.

Run from anywhere:   python3 tools/build.py
Re-running is safe (idempotent). It rewrites the .html files in place, generates the guides, FAQ,
glossary and quote pages, then writes sitemap.xml, robots.txt, llms.txt, feed.xml and _redirects, and
finally checks every internal link, image and #anchor. It exits non-zero if anything is broken.

What it does to every page:
  * bakes the shared header + footer into the HTML (crawlers see every nav link)
  * sets one consistent <head> block: title, description, canonical, robots,
    Open Graph + Twitter tags, all on SITE_URL
  * normalises internal links to one clean URL per page ("/about/")
  * adds width/height/decoding/loading to every <img>
  * adds a BreadcrumbList where a page has none

Edit PAGES for titles/descriptions, NAV and FOOTER for the shared chrome, tools/content.py for the FAQ,
glossary and schemes, and tools/articles.py for the guides.
"""
import hashlib
import html
import html.parser
import json
import os
import re
import struct
import subprocess
import sys
from datetime import date

# The site's public address. Used ONLY where search engines and social networks need a full
# URL: canonical tags, og:/twitter: tags, structured data, sitemap.xml, robots.txt and llms.txt.
# Links between pages are always root-relative ("/about/"), so the site works on any host.
SITE_URL = "https://lotussunenergy.com"
# Any of these in existing markup are rewritten to SITE_URL.
KNOWN_HOSTS = re.compile(r"https?://(?:www\.)?lotussunenergy\.com")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_SOURCES = ("components", "main", "calculator", "quote")


def _asset_version():
    """Short hash of the CSS, fonts and JS sources: changes whenever they change, so browsers never reuse stale files."""
    import hashlib
    h = hashlib.sha1()
    for rel in ["assets/css/fonts.css", "assets/css/style.css"] + [f"assets/js/{n}.js" for n in JS_SOURCES]:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:8]


def write_min_assets():
    """style.min.css (fonts + styles) and *.min.js, minified. Pages load only the minified files."""
    try:
        import rcssmin, rjsmin
        cssmin, jsmin = rcssmin.cssmin, rjsmin.jsmin
    except ImportError:  # pip install rcssmin rjsmin for real minification; this fallback only trims comments/space
        cssmin = lambda c: re.sub(r"\s*([{};:,])\s*", r"\1", re.sub(r"/\*.*?\*/", "", c, flags=re.S))
        jsmin = lambda j: j
    css = "".join(open(os.path.join(ROOT, f"assets/css/{n}.css"), encoding="utf8").read() for n in ("fonts", "style"))
    open(os.path.join(ROOT, "assets/css/style.min.css"), "w", encoding="utf8").write(cssmin(css))
    for n in JS_SOURCES:
        src = open(os.path.join(ROOT, f"assets/js/{n}.js"), encoding="utf8").read()
        open(os.path.join(ROOT, f"assets/js/{n}.min.js"), "w", encoding="utf8").write(jsmin(src))


ASSET_VERSION = _asset_version()
BRAND = "Lotus Sun Energy"
LEGAL = "Lotus Sun Energy"
EMAIL = "info@lotussunenergy.com"
ADDRESS = "Pakhanaha Sriram, Muzaffarpur, Bihar 843109, India"
TODAY = date.today().isoformat()

# ---------------------------------------------------------------- pages ----
# path: URL path; title 50-60 chars; desc 135-155 chars; crumb: breadcrumb name.
PAGES = {
    "index.html": dict(path="/", crumb="Home",
        title="Lotus Sun Energy | Veteran-Led Rooftop Solar for Homes",
        desc="Veteran-led rooftop solar for homes across India: cut your bill by up to 90%, get up to Rs 78,000 PM Surya Ghar subsidy, easy EMIs and a free site visit."),
    "about.html": dict(path="/about.html", crumb="About",
        title="About Lotus Sun Energy | Veteran-Led Solar Company",
        desc="Lotus Sun Energy is a new, veteran-led solar company from Muzaffarpur, Bihar: honest advice, quality components and clean power for every home in India."),
    "ex-servicemen-led-msme.html": dict(path="/ex-servicemen-led-msme.html", crumb="Veteran-Led",
        title="Veteran-Led Solar Company: Olive Green to Go Green",
        desc="Lotus Sun Energy is led by ex-servicemen: the discipline, integrity and service of the armed forces, now powering India's homes and businesses with solar."),
    "quality-safety.html": dict(path="/quality-safety.html", crumb="Quality & Safety",
        title="Quality & Safety Standards | Lotus Sun Energy Solar",
        desc="How Lotus Sun Energy builds solar safely and to standard: BIS and IEC certified equipment, CEA safety rules, proper earthing, testing and clean handover."),
    "how-it-works.html": dict(path="/how-it-works.html", crumb="How It Works",
        title="How Going Solar Works, Step by Step | Lotus Sun Energy",
        desc="How solar makes power for your home or business, and every step of going solar with Lotus Sun Energy, from the free site visit to subsidy and switch-on."),
    "industries.html": dict(path="/industries.html", crumb="Who We Serve",
        title="Solar for Homes, Societies & Business | Lotus Sun Energy",
        desc="Solar for every kind of site in India: homes, housing societies, shops, offices, schools, hospitals, factories and farms, from Lotus Sun Energy."),
    "solar-in-bihar.html": dict(path="/solar-in-bihar.html", crumb="Solar in Bihar", parent="services",
        title="Rooftop Solar in Muzaffarpur & Bihar | Lotus Sun Energy",
        desc="Rooftop solar in Muzaffarpur and across Bihar: PM Surya Ghar subsidy, NBPDCL and SBPDCL net metering, sizes, costs and a free site visit from a local team."),
    "solar-for-homes.html": dict(path="/solar-for-homes.html", crumb="Solar for Homes", parent="services",
        title="Rooftop Solar for Homes in India | Lotus Sun Energy",
        desc="Home rooftop solar made simple: the right system size for your bill, up to Rs 78,000 PM Surya Ghar subsidy, easy EMIs and every approval handled for you."),
    "capex-solar-epc.html": dict(path="/capex-solar-epc.html", crumb="Own Your Solar Plant", parent="services",
        title="Own Your Solar Plant: CAPEX Solar EPC | Lotus Sun Energy",
        desc="Own your solar plant outright. Lotus Sun Energy designs, supplies, installs and commissions rooftop and ground-mount solar that you own from day one."),
    "solar-installation-commissioning.html": dict(path="/solar-installation-commissioning.html", crumb="Installation & Commissioning",
        parent="services", title="Solar Installation & Commissioning | Lotus Sun Energy",
        desc="Solar installation and commissioning by veteran-led crews: structures, modules, cabling, earthing, testing and grid synchronisation, done right first time."),
    "service-rooftop.html": dict(path="/service-rooftop.html", crumb="Rooftop Solar",
        title="Rooftop Solar for Homes & Business | Lotus Sun Energy",
        desc="On-grid rooftop solar on RCC and metal-sheet roofs for homes, housing societies, shops, offices and factories across India, installed by Lotus Sun Energy."),
    "service-ground-mount.html": dict(path="/service-ground-mount.html", crumb="Ground-Mount Solar",
        title="Ground-Mount Solar Power Plants in India | Lotus Sun Energy",
        desc="Ground-mount solar plants for farms, factories and open land: design, piling, structures, installation and grid connection by Lotus Sun Energy."),
    "service-epc.html": dict(path="/service-epc.html", crumb="EPC Turnkey",
        title="Turnkey Solar EPC Company in India | Lotus Sun Energy",
        desc="Turnkey solar EPC from Lotus Sun Energy: engineering, procurement and construction under one roof, with one accountable team from survey to switch-on."),
    "service-piling.html": dict(path="/service-piling.html", crumb="Pile Foundation",
        title="Solar Pile Foundations & Piling Works | Lotus Sun Energy",
        desc="Solar pile foundations by Lotus Sun Energy: soil checks, pile design, augering, casting and pull-out tests, so ground-mount structures stand for 25 years."),
    "service-civil.html": dict(path="/service-civil.html", crumb="Civil & Fencing",
        title="Solar Civil Works, Fencing & Drainage | Lotus Sun Energy",
        desc="Solar civil works by Lotus Sun Energy: foundations, cable trenches, inverter rooms, internal roads, drainage, boundary walls and chain-link fencing."),
    "service-om.html": dict(path="/service-om.html", crumb="O&M & Support",
        title="Solar O&M, Cleaning & Maintenance | Lotus Sun Energy",
        desc="Solar operation and maintenance from Lotus Sun Energy: module cleaning, inspections, inverter checks, fault response and generation reports."),
    "solar-schemes-india.html": dict(path="/solar-schemes-india.html", crumb="Solar Schemes in India",
        title="Government Solar Schemes in India 2026 | Lotus Sun Energy",
        desc="Solar schemes in India 2026: PM Surya Ghar subsidy, PM-KUSUM, net metering, GST at 5%, ALMM and accelerated depreciation, explained in plain English."),
    "contact.html": dict(path="/contact.html", crumb="Contact",
        title="Contact Lotus Sun Energy | Solar Company, Muzaffarpur",
        desc="Contact Lotus Sun Energy for rooftop or ground-mount solar, subsidy help or a free site visit. Office in Muzaffarpur, Bihar, serving all of India."),
    "privacy-policy.html": dict(path="/privacy-policy.html", crumb="Privacy Policy",
        title="Privacy Policy (DPDP Act 2023) | Lotus Sun Energy Solar",
        desc="How Lotus Sun Energy handles the details you send through our forms: what we collect, why, how long we keep it, who we share it with and your rights."),
    "terms.html": dict(path="/terms.html", crumb="Terms & Conditions",
        title="Terms & Conditions and Legal Notices | Lotus Sun Energy",
        desc="Terms for the Lotus Sun Energy website and enquiries: estimates, quotations, subsidy and approvals, warranties, permitted use, liability and governing law."),
    "404.html": dict(path=None, crumb=None,
        title="Page Not Found (404) | Lotus Sun Energy Solar Company",
        desc="Sorry, this page could not be found. Explore Lotus Sun Energy's solar services, savings calculator, subsidy guides and FAQ, or get in touch with our team."),
}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import FAQ, GLOSSARY, NATIONAL_FACTS, SCHEMES, PANCHAMRIT, PANCHAMRIT_URL  # noqa: E402
from articles import ARTICLES  # noqa: E402  long-form guides, one page each

PAGES.update({
    "insights.html": dict(path="/insights.html", crumb="Solar Guides",
        title="Solar Guides for India 2026 | Lotus Sun Energy Insights",
        desc="Plain-English solar guides for India in 2026: PM Surya Ghar subsidy, net metering, GST at 5%, ALMM, batteries, rooftop vs ground-mount and maintenance."),
    "faq.html": dict(path="/faq.html", crumb="FAQ",
        title="Solar FAQs: Cost, Subsidy, EMI & Roofs | Lotus Sun Energy",
        desc="Straight answers on solar cost, the PM Surya Ghar subsidy, EMIs, roof suitability, net metering, monsoon output and maintenance, from Lotus Sun Energy."),
    "solar-glossary.html": dict(path="/solar-glossary.html", crumb="Solar Glossary",
        title="Solar Glossary: Terms in Plain English | Lotus Sun Energy",
        desc="Plain-English definitions of solar terms: kW and kWp, net metering, DISCOM, inverter, ALMM, EPC, CAPEX vs OPEX, payback, subsidy, earthing and many more."),
    "free-solar-quote.html": dict(path="/free-solar-quote.html", crumb="Free Solar Quote",
        title="Get a Free Solar Quote & Site Visit | Lotus Sun Energy",
        desc="Free, no-obligation solar quote for your home, business or land: a few quick questions, an instant savings estimate and a free site visit."),
})
for _a in ARTICLES:
    PAGES[_a["file"]] = dict(path="/" + _a["file"], crumb=_a["short"], parent="insights", title=_a["seo_title"], desc=_a["desc"],
                             kind="article", published=_a["date"], modified=_a["updated"], section=_a["tag"])


def write_page(fname, html_text):
    os.makedirs(os.path.dirname(page_path(fname)), exist_ok=True)
    open(page_path(fname), "w", encoding="utf8").write(html_text)


def page_url(fname):
    """Clean, folder-style URL of a page: /about/ (no .html, always a trailing slash)."""
    return "/" if fname == "index.html" else "/" + fname[:-5] + "/"


def page_path(fname):
    """Where a page lives on disk: about.html -> about/index.html, so the server needs no rewrites."""
    if fname in ("index.html", "404.html"):
        return os.path.join(ROOT, fname)
    return os.path.join(ROOT, fname[:-5], "index.html")


for _f, _m in PAGES.items():
    if _m["path"]:
        _m["path"] = page_url(_f)
PARENTS = {"services": ("Services", "/#services"), "insights": ("Solar Guides", "/insights/")}
SERVICE_PAGES = [p for p in PAGES if p.startswith("service-")]
for _p in SERVICE_PAGES:
    PAGES[_p].setdefault("parent", "services")

MONTHS = "January February March April May June July August September October November December".split()


def fmt_date(iso):
    if not iso:
        return ""
    parts = [int(p) for p in iso.split("-")]
    return f"{MONTHS[parts[1] - 1]} {parts[0]}" if len(parts) == 2 else f"{parts[2]} {MONTHS[parts[1] - 1][:3]} {parts[0]}"


EXT_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>')
ARROW_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>')
MAIL_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>')
SUN_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
           'aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>')


def esc(s):
    return html.escape(str(s), quote=True)


# ----------------------------------------------------- header / footer ----
# The logo: the lotus-and-sun mark (assets/img/logo.png) and the three-colour wordmark, as on lotussunenergy.com.
BRAND_HTML = ('<img src="assets/img/logo.png" alt="Lotus Sun Energy logo: a lotus with a solar-panel bud under the rising sun" '
              'class="brand-mark" width="270" height="270" />'
              '<span class="brand-word"><span class="w1">Lotus</span> <span class="w2">Sun</span> <span class="w3">Energy</span>'
              '<span class="brand-tag">From Olive Green to Go Green</span></span>')

# Top-level menu: (label, href, page keys that light it up, dropdown items or None)
NAV = [
    ("For Homes", "solar-for-homes.html", {"homes"}, None),
    ("Subsidy", "pm-surya-ghar-subsidy.html", {"subsidy"}, None),
    ("How It Works", "how-it-works.html", {"how"}, None),
    ("Services", "/#services", {"services", "industries"}, [
        ("Solar for Homes", "solar-for-homes.html"), ("Rooftop Solar", "service-rooftop.html"), ("Care & Maintenance", "service-om.html"),
        ("Solar in Bihar", "solar-in-bihar.html"), ("Ground-Mount Solar", "service-ground-mount.html"),
        ("Own Your Plant (CAPEX)", "capex-solar-epc.html"), ("EPC Turnkey", "service-epc.html"),
        ("Installation & Commissioning", "solar-installation-commissioning.html"), ("Pile Foundations", "service-piling.html"),
        ("Civil Works & Fencing", "service-civil.html"), ("Who We Serve", "industries.html")]),
    ("Resources", "insights.html", {"insights", "faq"}, [
        ("Solar Guides", "insights.html"), ("Savings Calculator", "/#calculator"), ("Government Solar Schemes", "solar-schemes-india.html"),
        ("Solar Glossary", "solar-glossary.html"), ("FAQ", "faq.html")]),
    ("About", "about.html", {"about"}, [
        ("About Us", "about.html"), ("Veteran-Led Company", "ex-servicemen-led-msme.html"), ("Quality & Safety", "quality-safety.html")]),
    ("Contact", "contact.html", {"contact"}, None),
]
CARET = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'


def render_header(page_key, fname=""):
    items = ['<a class="nav-home" href="/">Home</a>']
    for i, (label, href, keys, sub) in enumerate(NAV):
        on = page_key in keys or href == fname
        cls = ' class="active"' if on else ""
        cur = ' aria-current="page"' if href == fname else ""
        if not sub:
            items.append(f'<a href="{href}"{cls}{cur}>{esc(label)}</a>')
            continue
        wide = " sub--wide" if len(sub) > 6 else ""
        subs = "".join(f'<a href="{h}"{" aria-current=" + chr(34) + "page" + chr(34) if h == fname else ""}>{esc(t)}</a>' for t, h in sub)
        items.append(f'<div class="nav-item has-sub{" active" if on else ""}">'
                     f'<a href="{href}" class="nav-top{" active" if on else ""}"{cur}>{esc(label)}</a>'
                     f'<button class="sub-toggle" type="button" aria-expanded="false" aria-controls="sub-{i}" aria-label="Show {esc(label)} menu">{CARET}</button>'
                     f'<div class="sub{wide}" id="sub-{i}">{subs}</div></div>')
    links = "".join(items)
    return f"""<header class="header scrolled solid" id="header">
    <div class="container nav">
      <a href="/" class="brand" aria-label="Lotus Sun Energy, home">{BRAND_HTML}</a>
      <nav class="nav-links" id="navLinks" aria-label="Primary">{links}<a class="nav-quote" href="free-solar-quote.html">Get a Free Quote</a></nav>
      <div class="nav-cta">
        <a href="/#calculator" class="btn btn--outline">Estimate Savings</a>
        <a href="free-solar-quote.html" class="btn btn--primary">Get a Free Quote</a>
        <button class="menu-toggle" id="menuToggle" aria-label="Toggle menu" aria-expanded="false" aria-controls="navLinks">
          <span></span><span></span><span></span>
        </button>
      </div>
    </div>
  </header>"""


FOOTER = f"""<section class="cta-strip" aria-label="Contact Lotus Sun Energy">
    <div class="container cta-strip__in">
      <div class="cta-strip__txt"><span class="eyebrow">Free site visit</span><h2>Ready to cut your power bill? <span class="text-sun">Let's go solar together.</span></h2>
        <p>Rooftop and ground-mount solar for homes, businesses and industry, from a veteran-led team that handles the survey, subsidy, approvals and installation for you.</p></div>
      <div class="cta-strip__btns">
        <a class="btn btn--sun" href="free-solar-quote.html">Get a Free Quote {ARROW_SVG}</a>
        <a class="btn btn--ghost" href="mailto:{EMAIL}?subject=Solar%20enquiry">Email {EMAIL}</a>
      </div>
    </div>
  </section>
  <footer class="footer">
    <div class="container">
      <div class="footer__top">
        <div class="footer__brand">
          <div class="logo">{BRAND_HTML}</div>
          <p class="footer__motto">Serving the Nation, From Olive Green to Go Green.</p>
          <p>Clean, affordable solar power for every home and business in India. A veteran-led (ex-servicemen) company that makes going solar simple, from your first question to long-term support.</p>
          <a href="mailto:{EMAIL}" class="footer-email">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:8px;" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>{EMAIL}
          </a>
        </div>
        <div>
          <h2 class="footer__h">Explore</h2>
          <ul>
            <li><a href="about.html">About Us</a></li>
            <li><a href="ex-servicemen-led-msme.html">Veteran-Led Company</a></li>
            <li><a href="how-it-works.html">How It Works</a></li>
            <li><a href="quality-safety.html">Quality &amp; Safety</a></li>
            <li><a href="industries.html">Who We Serve</a></li>
            <li><a href="/#calculator">Savings Calculator</a></li>
            <li><a href="pm-surya-ghar-subsidy.html">PM Surya Ghar Subsidy</a></li>
            <li><a href="insights.html">Solar Guides</a></li>
            <li><a href="solar-schemes-india.html">Government Solar Schemes</a></li>
            <li><a href="solar-glossary.html">Solar Glossary</a></li>
            <li><a href="faq.html">FAQ</a></li>
            <li><a href="contact.html">Contact</a></li>
          </ul>
        </div>
        <div>
          <h2 class="footer__h">Services</h2>
          <ul>
            <li><a href="solar-for-homes.html">Solar for Homes</a></li>
            <li><a href="service-rooftop.html">Rooftop Solar</a></li>
            <li><a href="service-ground-mount.html">Ground-Mount Solar</a></li>
            <li><a href="capex-solar-epc.html">Own Your Plant (CAPEX)</a></li>
            <li><a href="service-epc.html">EPC Turnkey</a></li>
            <li><a href="solar-installation-commissioning.html">Installation &amp; Commissioning</a></li>
            <li><a href="service-piling.html">Pile Foundation</a></li>
            <li><a href="service-civil.html">Civil &amp; Fencing</a></li>
            <li><a href="service-om.html">O&amp;M &amp; Support</a></li>
          </ul>
        </div>
        <div class="footer__reg">
          <h2 class="footer__h">Reach Us</h2>
          <p>
            <b>Office:</b> Pakhanaha Sriram,<br/>Muzaffarpur, Bihar 843109, India<br/>
            <b>Email:</b> <a href="mailto:{EMAIL}">{EMAIL}</a><br/>
            <b>Hours:</b> Mon to Sat, 9 AM to 7 PM<br/>
            <b>Service area:</b> Free site visits across India
          </p>
        </div>
      </div>
      <div class="footer__bottom">
        <span>© <span id="year">{date.today().year}</span> Lotus Sun Energy. All rights reserved.</span>
        <span class="footer-legal"><a href="privacy-policy.html">Privacy Policy</a><a href="terms.html">Terms &amp; Conditions</a><a href="/sitemap.xml">Sitemap</a></span>
        <span class="made">Clean energy for every home ☀️</span>
      </div>
    </div>
  </footer>

  <nav class="contact-dock" aria-label="Quick contact">
    <a class="cd-mail" href="mailto:{EMAIL}?subject=Solar%20enquiry" aria-label="Email Lotus Sun Energy">{MAIL_SVG}<span>Email us</span></a>
    <a class="cd-quote" href="free-solar-quote.html">{SUN_SVG}<span>Free solar quote</span></a>
  </nav>
  <button class="to-top" id="toTop" aria-label="Back to top">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
  </button>"""


# ------------------------------------------------------- shared blocks ----
def render_national_facts():
    cards = []
    for i, f in enumerate(NATIONAL_FACTS):
        cards.append(f'<a class="nf-card reveal" data-d="{i}" href="{f["url"]}" target="_blank" rel="noopener">'
                     f'<span class="nf-num"><span data-count="{f["num"]}">{f["num"]}</span><small>{f["suffix"]}</small></span>'
                     f'<span class="nf-lbl">{esc(f["label"])}</span><span class="nf-src">Source: {"MNRE data" if "solarquarter" in f["url"] else "PIB"} {EXT_SVG}</span></a>')
    return '<div class="nf-grid">' + "".join(cards) + "</div>"


def render_schemes():
    nav = "".join(f'<a href="#scheme-{art_slug(t)}">{esc(t)}</a>' for t, *_ in SCHEMES)
    cards = []
    for i, (title, who, points, fit, src, url, guide, status) in enumerate(SCHEMES):
        pts = "".join(f"<li>{esc(p)}</li>" for p in points)
        source = (f'<a class="sc-src" href="{url}" target="_blank" rel="noopener">Source: {esc(src)} {EXT_SVG}</a>' if url
                  else f'<span class="sc-src">Source: {esc(src)}</span>')
        cards.append(f'<article class="scheme-card reveal" id="scheme-{art_slug(title)}" data-d="{i % 3}"><span class="sc-who">{esc(who)}</span><h3>{esc(title)}</h3>'
                     f'<span class="sc-status">{esc(status)}</span><ul>{pts}</ul><p class="sc-fit"><b>Where we fit:</b> {esc(fit)}</p>'
                     f'<a class="sc-guide" href="{guide}">Read the full guide {ARROW_SVG}</a>{source}</article>')
    rows = "".join(f'<tr><th scope="row"><a href="#scheme-{art_slug(t)}">{esc(t)}</a></th><td>{esc(who)}</td><td>{esc(status)}</td><td><a href="{guide}">Guide</a></td></tr>'
                   for t, who, _p, _f, _s, _u, guide, status in SCHEMES)
    table = (f'<div class="cmp-wrap reveal" tabindex="0" role="region" aria-label="Schemes at a glance"><table class="cmp-table">'
             f'<caption class="sr-only">Solar schemes and policies at a glance, October 2026</caption>'
             f'<thead><tr><th scope="col">Scheme or policy</th><th scope="col">For</th><th scope="col">Status (Oct 2026)</th><th scope="col">In depth</th></tr></thead><tbody>{rows}</tbody></table></div>')
    return (f'<nav class="sc-nav reveal" aria-label="Jump to a scheme">{nav}</nav>{table}'
            f'<div class="scheme-grid">' + "".join(cards) + "</div>")


def render_scheme_guides():
    return '<div class="art-grid-cards">' + "".join(art_card(a, i) for i, a in enumerate(ARTICLES)) + "</div>"


def render_panchamrit():
    items = "".join(f'<li class="pa-item reveal" data-d="{i % 5}"><span class="pa-n">{i + 1}</span><p>{esc(t)}</p></li>'
                    for i, t in enumerate(PANCHAMRIT))
    return (f'<ol class="panchamrit">{items}</ol><p class="lq-note">The five commitments in the Prime Minister\'s words, from his '
            f'national statement at COP26, Glasgow, 1 November 2021 (<a href="{PANCHAMRIT_URL}" target="_blank" rel="noopener">PIB</a>).</p>')


BLOCKS = {
    "national-facts": render_national_facts,
    "schemes": render_schemes,
    "scheme-guides": render_scheme_guides,
    "guides-home": lambda: '<div class="art-grid-cards">' + "".join(art_card(a, i) for i, a in enumerate(ARTICLES[:6])) + "</div>",
    "panchamrit": render_panchamrit,
}


# ------------------------------------------------------ generated pages ----
def page_shell(page_key, body, ld=None, extra_head=""):
    """A complete page; the build fills in title, meta, canonical and header/footer."""
    ld_html = "".join('<script type="application/ld+json">\n' + json.dumps(x, ensure_ascii=False, indent=2) + "\n</script>\n"
                      for x in (ld or []))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="theme-color" content="#16245e" />
<title>x</title>
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/favicon-32.png" />
<link rel="stylesheet" href="assets/css/style.css?v={ASSET_VERSION}" />
{extra_head}{ld_html}</head>
<body data-page="{page_key}">
<!-- build:header --><!-- /build:header -->

{body}

<!-- build:footer --><!-- /build:footer -->
<script src="assets/js/components.js?v={ASSET_VERSION}"></script>
<script src="assets/js/main.js?v={ASSET_VERSION}"></script>
</body>
</html>
"""


def page_hero(eyebrow, h1, lead, crumbs, actions=""):
    """The inner-page banner. No photo: a navy sky with the sun rising behind solar-panel rows (pure CSS/SVG)."""
    trail = '<a href="/">Home</a>' + "".join(
        f'<span>/</span><a href="{href}">{esc(name)}</a>' if href else f"<span>/</span>{esc(name)}" for name, href in crumbs)
    return f"""<section class="page-hero">
  <div class="page-hero__bg" aria-hidden="true"><span class="sky-sun"></span><span class="sky-rows"></span></div>
  <div class="container">
    <span class="eyebrow">{eyebrow}</span>
    <h1>{h1}</h1>
    <p>{lead}</p>{actions}
    <nav class="breadcrumb" aria-label="Breadcrumb">{trail}</nav>
  </div>
</section>"""


def page_label(fname):
    return PAGES[fname]["crumb"]


def render_faq_page():
    groups = []
    for title, items in FAQ:
        qs = "".join(f'\n      <details class="faq"><summary>{esc(q)}</summary><div class="faq-a">{a}</div></details>' for q, a in items)
        groups.append(f'\n    <h2 class="faq-group reveal" id="{art_slug(title)}">{esc(title)}</h2>\n    <div class="faq-list reveal">{qs}\n    </div>')
    nav = "".join(f'<a href="#{art_slug(t)}">{esc(t)}</a>' for t, _ in FAQ)
    plain = lambda t: html.unescape(re.sub(r"<[^>]+>", "", t))
    ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for _, items in FAQ for q, a in items]}]
    body = page_hero("Frequently Asked Questions", 'Your Solar Questions, <span class="text-sun">Answered</span>',
                     "Cost, subsidy, EMIs, roofs, net metering, the monsoon and maintenance: everything people ask us before they go solar.",
                     [("FAQ", None)]) + f"""

<section class="section">
  <div class="container faq-page">
    <nav class="sc-nav reveal" aria-label="FAQ topics">{nav}</nav>{"".join(groups)}
    <div class="section-cta reveal"><a class="btn btn--primary" href="contact.html">Ask Us Anything {ARROW_SVG}</a><a class="btn btn--outline" href="solar-glossary.html">Solar Glossary</a></div>
  </div>
</section>"""
    return page_shell("faq", body, ld)


# ------------------------------------------------------------ articles ----
TAG_ICONS = {
    "Schemes": '<path d="M3 10l9-6 9 6"/><path d="M5 10v9h14v-9"/><path d="M9 19v-5h6v5"/>',
    "Tax": '<path d="M19 5L5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/>',
    "Policy": '<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4M10 12h6M10 16h6"/>',
    "Grid & Regulation": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "Business Models": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "Buyer's Guide": '<path d="M9 11l3 3 8-8"/><path d="M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"/>',
    "System Design": '<rect x="3" y="4" width="18" height="12" rx="1"/><path d="M3 10h18M9 4v12M15 4v12M8 20h8M12 16v4"/>',
    "O&M": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.5-.5-.5-2.5z"/>',
    "Standards & Safety": '<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/><path d="M9 12l2 2 4-4"/>',
    "Storage": '<rect x="2" y="7" width="18" height="10" rx="2"/><path d="M22 11v2M6 11v2M10 11v2"/>',
    "Installation & Commissioning": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
    "Market Update": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
}
TAG_ART = ["sun", "leaf", "lotus", "navy"]


def art_visual(a, cls="ac-img"):
    """Guide cards carry no photo: a colour tile with the topic icon (the site has no stock or project photos)."""
    tags = list(dict.fromkeys(x["tag"] for x in ARTICLES))
    tone = TAG_ART[tags.index(a["tag"]) % len(TAG_ART)]
    icon = TAG_ICONS.get(a["tag"], TAG_ICONS["Policy"])
    return (f'<span class="{cls} art-tile art-tile--{tone}" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{icon}</svg></span>')


def art_slug(text):
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text).lower()).strip("-")[:60]


def art_words(a):
    def flat(b):
        if isinstance(b, str):
            return b
        return " ".join(flat(x) if isinstance(x, (str, tuple, list)) else "" for x in b[1:])
    txt = " ".join(flat(b) for sec in a["sections"] for b in sec["blocks"]) + " " + " ".join(q + " " + ans for q, ans in a["faq"])
    return len(re.sub(r"<[^>]+>", " ", txt).split())


def art_block(b):
    """One block of an article body. A plain string is a paragraph (it may contain inline HTML)."""
    if isinstance(b, str):
        return f"\n        <p>{b}</p>"
    kind = b[0]
    if kind == "h3":
        return f'\n        <h3 id="{art_slug(b[1])}">{b[1]}</h3>'
    if kind in ("ul", "ol"):
        return f"\n        <{kind} class=\"art-list\">" + "".join(f"<li>{x}</li>" for x in b[1]) + f"</{kind}>"
    if kind == "table":
        _, caption, head, rows = b
        th = "".join(f'<th scope="col">{h}</th>' for h in head)
        trs = "".join("<tr>" + "".join((f'<th scope="row">{c}</th>' if i == 0 else f"<td>{c}</td>") for i, c in enumerate(r)) + "</tr>" for r in rows)
        return (f'\n        <div class="art-table" tabindex="0" role="region" aria-label="{esc(re.sub("<[^>]+>", "", caption))}"><table>'
                f"<caption>{caption}</caption><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>")
    if kind == "note":
        _, title, text = b
        return f'\n        <aside class="art-note"><b>{title}</b><p>{text}</p></aside>'
    if kind == "warn":
        _, title, text = b
        return f'\n        <aside class="art-note art-note--warn"><b>{title}</b><p>{text}</p></aside>'
    if kind in ("fig", "yt"):  # no photos or videos on this site yet: image and video blocks are skipped
        return ""
    if kind == "stats":
        return '\n        <div class="art-stats">' + "".join(f"<div><b>{n}</b><span>{l}</span></div>" for n, l in b[1]) + "</div>"
    if kind == "steps":
        return '\n        <ol class="art-steps">' + "".join(f"<li><b>{t}</b><span>{x}</span></li>" for t, x in b[1]) + "</ol>"
    if kind == "quote":
        _, text, cite = b
        return f"\n        <blockquote class=\"art-quote\"><p>{text}</p><cite>{cite}</cite></blockquote>"
    if kind == "cta":
        return (f'\n        <div class="art-cta"><p>{b[1]}</p><a class="btn btn--sun" href="free-solar-quote.html">Get a free solar quote {ARROW_SVG}</a></div>')
    raise ValueError(f"unknown article block {kind}")


def art_card(a, d=0, cls="art-card"):
    return (f'<a class="{cls} reveal" data-d="{d % 3}" href="{a["file"]}" data-tag="{art_slug(a["tag"])}">{art_visual(a)}'
            f'<span class="ac-body"><span class="ins-tag">{esc(a["tag"])}</span><b>{esc(a["title"])}</b><span class="ins-sum">{esc(a["summary"])}</span>'
            f'<span class="ins-meta">{max(3, round(art_words(a) / 220))} min read · Updated {fmt_date(a["updated"])} {ARROW_SVG}</span></span></a>')


def render_article_page(a):
    words = art_words(a)
    mins = max(3, round(words / 220))
    toc = "".join(f'<li><a href="#{art_slug(sec["h"])}">{sec["h"]}</a></li>' for sec in a["sections"])
    toc += '<li><a href="#faq">Frequently asked questions</a></li><li><a href="#sources">Sources</a></li>'
    keys = "".join(f"<li>{t}</li>" for t in a["takeaways"])
    secs = "".join(f'\n      <section class="art-sec" id="{art_slug(sec["h"])}">\n        <h2>{sec["h"]}</h2>'
                   + "".join(art_block(b) for b in sec["blocks"]) + "\n      </section>" for sec in a["sections"])
    faq = "".join(f'<details class="faq"><summary>{esc(q)}</summary><div class="faq-a">{ans}</div></details>' for q, ans in a["faq"])
    srcs = "".join(f'<li><a href="{u}" target="_blank" rel="noopener">{esc(n)}</a></li>' for n, u in a["sources"])
    related = [x for x in ARTICLES if x["file"] in a.get("related", [])] or [x for x in ARTICLES if x["tag"] == a["tag"] and x is not a]
    related = (related + [x for x in ARTICLES if x is not a and x not in related])[:3]
    services = "".join(f'<a href="{f}">{esc(page_label(f))}</a>' for f in a.get("services", []))
    plain = lambda t: html.unescape(re.sub(r"<[^>]+>", "", t))
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["desc"],
           "image": [f"{SITE_URL}/{OG_BRAND}"], "datePublished": a["date"], "dateModified": a["updated"],
           "author": {"@type": "Organization", "name": "Lotus Sun Energy team", "url": SITE_URL + "/about/"},
           "publisher": {"@id": SITE_URL + "/#organization"}, "mainEntityOfPage": SITE_URL + page_url(a["file"]),
           "articleSection": a["tag"], "keywords": ", ".join(a.get("keywords", [])), "wordCount": words, "inLanguage": "en-IN",
           "about": [{"@type": "Thing", "name": k} for k in a.get("keywords", [])[:5]],
           "citation": [u for _, u in a["sources"]]},
          {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(ans)}} for q, ans in a["faq"]]}]
    body = page_hero(f"Guide · {esc(a['tag'])}", a["title"], esc(a["summary"]),
                     [("Solar Guides", "insights.html"), (a["short"], None)]) + f"""
<div class="read-progress" aria-hidden="true"><span></span></div>
<section class="section art-wrap">
  <div class="container art-grid">
    <aside class="art-toc" aria-label="On this page">
      <details open><summary>On this page</summary><ol>{toc}</ol></details>
    </aside>
    <article class="art-body prose">
      <p class="art-byline">By the <a href="about.html">Lotus Sun Energy team</a> · <time datetime="{a['updated']}">Updated {fmt_date(a['updated'])}</time> · {mins} min read</p>
      <div class="ins-keys"><b>Key takeaways</b><ul>{keys}</ul></div>{secs}
      <section class="art-sec" id="faq">
        <h2>Frequently asked questions</h2>
        <div class="faq-list">{faq}</div>
      </section>
      <section class="art-sec" id="sources">
        <h2>Sources</h2>
        <ol class="art-sources">{srcs}</ol>
        <p class="art-disclaimer">This guide explains public policy in plain language for planning purposes. Rules, rates and deadlines change: confirm the current position with the notifying authority, your DISCOM and your tax adviser before you commit. Last checked {fmt_date(a['updated'])}.</p>
      </section>
      <div class="art-author"><img src="assets/img/logo.png" alt="Lotus Sun Energy logo" width="270" height="270" /><p><b>About the authors.</b> Lotus Sun Energy is a veteran-led solar company from Muzaffarpur, Bihar, helping homes, businesses and industry across India go solar with honest advice and careful installation. <a href="about.html">About us</a> · <a href="how-it-works.html">How it works</a></p></div>
      {f'<div class="svc-other art-services">{services}</div>' if services else ''}
    </article>
  </div>
</section>

<section class="section section--soft">
  <div class="container">
    <div class="section-head center reveal"><span class="eyebrow">Keep Reading</span><h2>Related <span class="text-grad">Guides</span></h2></div>
    <div class="art-grid-cards">{"".join(art_card(x, i) for i, x in enumerate(related))}</div>
    <div class="section-cta reveal"><a class="btn btn--outline" href="insights.html">All solar guides</a><a class="btn btn--primary" href="solar-schemes-india.html">Government solar schemes {ARROW_SVG}</a></div>
  </div>
</section>"""
    return page_shell("subsidy" if a["file"] == "pm-surya-ghar-subsidy.html" else "insights", body, ld)


def render_insights_page():
    tags = []
    for a in ARTICLES:
        if a["tag"] not in tags:
            tags.append(a["tag"])
    filters = '<button class="filter active" data-art-filter="all">All guides</button>' + "".join(
        f'<button class="filter" data-art-filter="{art_slug(t)}">{esc(t)}</button>' for t in tags)
    lead, rest = ARTICLES[0], ARTICLES[1:]
    ld = [{"@context": "https://schema.org", "@type": "Blog", "name": "Lotus Sun Energy Solar Guides", "url": SITE_URL + "/insights/",
           "publisher": {"@id": SITE_URL + "/#organization"},
           "blogPost": [{"@type": "BlogPosting", "headline": a["title"], "description": a["desc"], "url": SITE_URL + page_url(a["file"]),
                         "datePublished": a["date"], "dateModified": a["updated"], "image": f"{SITE_URL}/{OG_BRAND}",
                         "author": {"@id": SITE_URL + "/#organization"}, "publisher": {"@id": SITE_URL + "/#organization"}} for a in ARTICLES]}]
    body = page_hero("Solar Guides 2026", 'Solar Power in India, <span class="text-sun">Explained</span>',
                     f"{len(ARTICLES)} plain-English guides on subsidies, taxes, net metering, standards and how to get a solar system that "
                     "pays back. Updated for October 2026, with every figure linked to its source.", [("Solar Guides", None)]) + f"""

<section class="section" id="guides">
  <div class="container">
    <a class="art-feature reveal" href="{lead['file']}" data-art-feature>{art_visual(lead, "af-img")}
      <span class="af-body"><span class="ins-tag">Featured · {esc(lead['tag'])}</span><b>{esc(lead['title'])}</b><span>{esc(lead['summary'])}</span><span class="btn btn--primary">Read the guide {ARROW_SVG}</span></span></a>
    <div class="filters reveal" role="group" aria-label="Filter guides by topic">{filters}</div>
    <p class="sr-only" aria-live="polite" data-art-count></p>
    <div class="art-grid-cards" data-art-grid>{art_card(lead, 0).replace('class="art-card reveal"', 'class="art-card reveal is-hidden" data-lead="1"', 1)}{"".join(art_card(a, i) for i, a in enumerate(rest))}</div>
    <p class="art-empty" data-art-empty hidden>No guides in this topic yet. <a href="insights.html">See all guides</a>.</p>
  </div>
</section>

<section class="section section--soft">
  <div class="container">
    <div class="section-head center reveal"><span class="eyebrow">Keep Learning</span><h2>Schemes, Glossary &amp; <span class="text-grad">Straight Answers</span></h2><p>Plain-English definitions, the government schemes and the questions people ask most.</p></div>
    <div class="svc-other reveal"><a href="solar-schemes-india.html">Government Solar Schemes</a><a href="pm-surya-ghar-subsidy.html">PM Surya Ghar Subsidy</a><a href="solar-glossary.html">Solar Glossary</a><a href="faq.html">FAQ</a><a href="/#calculator">Savings Calculator</a><a href="how-it-works.html">How It Works &rarr;</a></div>
  </div>
</section>"""
    return page_shell("insights", body, ld)


def render_glossary_page():
    terms = sorted(GLOSSARY, key=lambda t: t[0].lower())
    def slug(t):
        return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    letters = sorted({t[0][0].upper() for t in terms})
    index = "".join(f'<a href="#letter-{l}">{l}</a>' for l in letters)
    blocks, cur = [], None
    for term, definition in terms:
        l = term[0].upper()
        if l != cur:
            if cur:
                blocks.append("</dl>")
            blocks.append(f'<h2 class="gl-letter" id="letter-{l}">{l}</h2><dl class="gl-list">')
            cur = l
        blocks.append(f'<div class="gl-item" id="{slug(term)}"><dt>{esc(term)}</dt><dd>{esc(definition)}</dd></div>')
    blocks.append("</dl>")
    ld = [{"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "Solar glossary",
           "url": SITE_URL + "/solar-glossary.html", "publisher": {"@id": SITE_URL + "/#organization"},
           "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t, "description": d,
                               "url": f"{SITE_URL}/solar-glossary.html#{slug(t)}"} for t, d in terms]}]
    body = page_hero("Solar Glossary", 'Solar Terms, <span class="text-sun">in Plain English</span>',
                     "The words you will meet when going solar, from kW and net metering to DISCOM, ALMM and payback.",
                     [("Solar Guides", "insights.html"), ("Solar Glossary", None)]) + f"""

<section class="section">
  <div class="container gl-wrap">
    <nav class="gl-index reveal" aria-label="Glossary index">{index}</nav>
    {"".join(blocks)}
    <div class="section-cta reveal"><a class="btn btn--primary" href="faq.html">Read the FAQ {ARROW_SVG}</a><a class="btn btn--outline" href="insights.html">Solar Guides</a></div>
  </div>
</section>"""
    return page_shell("insights", body, ld)




QUOTE_SEGMENTS = [
    ("home", "Home", "An independent house or villa",
     '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M9 20v-5h6v5"/>'),
    ("society", "Housing society", "Common areas, lifts, pumps and lighting",
     '<path d="M4 21V5h8v16M12 9h8v12"/><path d="M7 9h2M7 13h2M7 17h2M15 13h2M15 17h2"/>'),
    ("commercial", "Shop, office or clinic", "Shops, offices, hotels, clinics, petrol pumps",
     '<path d="M3 9l1.5-5h15L21 9M4 9h16v11H4zM9 20v-6h6v6"/>'),
    ("industry", "Factory or industry", "Plants, warehouses, cold stores, mills",
     '<path d="M3 21V10l6 4V10l6 4V6l6 4v11z"/><path d="M7 17h2M13 17h2"/>'),
    ("institution", "School, hospital or institution", "Schools, colleges, hospitals, offices of government",
     '<path d="M3 21h18M5 21V9l7-5 7 5v12M9 21v-6h6v6"/>'),
    ("land", "Farm or open land", "Ground-mount plants, pumps, farmhouses",
     '<path d="M12 21c-5-3-8-7-8-11 4 0 7 2 8 5 1-3 4-5 8-5 0 4-3 8-8 11z"/><path d="M12 21v-6"/>'),
]
QUOTE_SERVICES = ["Complete solar system (design, supply, install, commission)", "Installation & commissioning only",
                  "Pile foundations & civil works", "Fencing, roads & drainage", "Maintenance of an existing system", "Advice: not sure yet"]
QUOTE_STATES = ["Bihar", "Jharkhand", "Uttar Pradesh", "West Bengal", "Odisha", "Assam", "Delhi", "Haryana", "Punjab", "Uttarakhand",
                "Himachal Pradesh", "Jammu & Kashmir", "Ladakh", "Rajasthan", "Gujarat", "Maharashtra", "Goa", "Madhya Pradesh",
                "Chhattisgarh", "Karnataka", "Kerala", "Tamil Nadu", "Andhra Pradesh", "Telangana", "Arunachal Pradesh", "Meghalaya",
                "Tripura", "Mizoram", "Manipur", "Nagaland", "Sikkim", "Puducherry", "Chandigarh", "Andaman & Nicobar Islands",
                "Dadra & Nagar Haveli and Daman & Diu", "Lakshadweep"]


def render_quote_page():
    def cards(name, items, cls="q-opt", typ="radio", req=True):
        return "".join(
            f'<label class="{cls}"><input type="{typ}" name="{name}" value="{esc(v)}"{" required" if req and typ == "radio" else ""} />'
            f'<span class="q-opt__box">{b}</span></label>' for v, b in items)

    def sel(name, label, opts, req=False, hint=""):
        o = "".join(f"<option>{esc(x)}</option>" for x in opts)
        return (f'<div class="field"><label for="q-{name}">{label}{" *" if req else ""}</label><select id="q-{name}" name="{name}"'
                f'{" required" if req else ""}><option value="">Select…</option>{o}</select>{hint}</div>')

    seg_cards = cards("segment", [(t, f'<span class="q-ic" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                                     f'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{ic}</svg></span>'
                                     f'<b>{esc(t)}</b><small>{esc(d)}</small>') for k, t, d, ic in QUOTE_SEGMENTS], "q-opt q-seg")
    seg_keys = "".join(f'<input type="hidden" disabled data-seg-key="{esc(t)}" value="{k}" />' for k, t, _, _ in QUOTE_SEGMENTS)
    svc_cards = cards("services", [(x, f"<b>{esc(x)}</b>") for x in QUOTE_SERVICES], "q-opt q-chk", "checkbox")
    own = cards("ownership", [
        ("Pay upfront and own it", "<b>Pay upfront</b><small>Usually the lowest lifetime cost. For homes, the PM Surya Ghar subsidy comes back to your bank account.</small>"),
        ("Pay in EMIs", "<b>Pay in EMIs</b><small>Spread the cost with a bank or solar loan; the EMI is often close to the bill it replaces.</small>"),
        ("Not sure, advise me", "<b>Not sure yet</b><small>We will compare the options for you.</small>")])
    timeline = cards("timeline", [(x, f"<b>{esc(x)}</b>") for x in
                                  ["Within 1 month", "In 1 to 3 months", "In 3 to 6 months", "In 6 to 12 months", "Just exploring"]], "q-opt q-pill")
    chips = "".join(f'<button type="button" class="q-chip" data-bill="{v}">{l}</button>'
                    for v, l in [(2000, "Rs 2,000"), (5000, "Rs 5,000"), (25000, "Rs 25,000"), (100000, "Rs 1 lakh+")])
    tick = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>'

    body = page_hero("Free Solar Quote · Takes about 1 minute",
                     'See What Solar Can <span class="text-sun">Save You</span>',
                     "Answer a few quick questions, see an instant savings estimate, and get a free, no-obligation "
                     "proposal and site visit from our veteran-led team.", [("Free Solar Quote", None)]) + f"""

<section class="section quote-section">
  <div class="container quote-grid">
    <form class="form-card quote-form reveal" id="quoteForm" action="https://formsubmit.co/{EMAIL}" method="POST"
          data-endpoint="https://formsubmit.co/ajax/{EMAIL}">
      <input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true" />
      <input type="hidden" name="_subject" value="Free solar quote request, Lotus Sun Energy website" />
      <input type="hidden" name="_captcha" value="false" />
      <input type="hidden" name="_template" value="table" />
      <input type="hidden" name="lead_score" value="" />
      <input type="hidden" name="estimate_kwp" value="" />
      <input type="hidden" name="estimate_monthly_savings" value="" />
      <input type="hidden" name="source" value="" />
      {seg_keys}

      <div class="q-top">
        <div class="q-bar" aria-hidden="true"><span class="q-bar__fill"></span></div>
        <p class="q-count"><span class="q-steptxt">Step 1 of 6</span></p>
      </div>

      <fieldset class="q-step" data-step="1">
        <legend>Who is the solar system for?</legend>
        <p class="q-sub">Pick one. It helps us plan the right system for you.</p>
        <div class="q-opts q-opts--3">{seg_cards}</div>
        <div class="q-nav"><span></span><button type="button" class="btn btn--primary" data-next>Continue {ARROW_SVG}</button></div>
      </fieldset>

      <fieldset class="q-step" data-step="2">
        <legend>What do you need from us?</legend>
        <p class="q-proof" data-proof hidden></p>
        <p class="q-sub">Tick all that apply.</p>
        <div class="q-opts">{svc_cards}</div>
        <div data-plant-only>
          <p class="q-label">How would you like to pay for it?</p>
          <div class="q-opts q-opts--3">{own}</div>
        </div>
        <div class="q-nav"><button type="button" class="btn btn--outline" data-back>Back</button><button type="button" class="btn btn--primary" data-next>Continue {ARROW_SVG}</button></div>
      </fieldset>

      <fieldset class="q-step" data-step="3">
        <legend>Where is the site?</legend>
        <div class="field-row">
          {sel("state", "State", QUOTE_STATES, True)}
          <div class="field"><label for="q-city">City / district *</label><input type="text" id="q-city" name="city" placeholder="e.g. Muzaffarpur" maxlength="80" required /></div>
        </div>
        <div class="field-row">
          {sel("site_type", "Where will the panels go?", ["RCC (concrete) rooftop", "Metal-sheet rooftop", "Open land (ground-mount)", "Carport / parking", "Not sure yet"])}
          <div class="field"><label for="q-area">Free area available</label><div class="q-inline"><input type="number" id="q-area" name="area" min="0" step="any" inputmode="decimal" placeholder="e.g. 400" /><select name="area_unit" aria-label="Area unit"><option>sq ft</option><option>sq m</option><option>acres</option><option>bigha</option><option>katha</option></select></div></div>
        </div>
        <div class="field" data-service-only hidden><label for="q-scope">About the system and the work *</label><textarea id="q-scope" name="scope_details" maxlength="1500" placeholder="For maintenance: capacity, age, inverter make and any problem you see. For piling, civil or installation work: capacity, scope and whether drawings are ready."></textarea></div>
        <div class="field"><label for="q-capacity">Capacity in mind (optional)</label><div class="q-inline"><input type="number" id="q-capacity" name="capacity_kw" min="0" step="any" inputmode="decimal" placeholder="If you already know it" /><span class="q-unit">kW</span></div></div>
        <div class="q-nav"><button type="button" class="btn btn--outline" data-back>Back</button><button type="button" class="btn btn--primary" data-next>Continue {ARROW_SVG}</button></div>
      </fieldset>

      <fieldset class="q-step" data-step="4" data-plant-step>
        <legend>How much power do you use?</legend>
        <p class="q-sub">Your bill lets us size the system and estimate your savings right now.</p>
        <div class="field"><label for="q-bill">Average monthly electricity bill *</label><div class="q-inline q-money"><span class="q-unit">Rs</span><input type="number" id="q-bill" name="monthly_bill" min="500" step="any" inputmode="numeric" placeholder="e.g. 3000" required /></div>
          <div class="q-chips" aria-label="Quick picks">{chips}</div></div>
        <div class="field-row">
          <div class="field"><label for="q-tariff">Tariff per unit (if known)</label><div class="q-inline q-money"><span class="q-unit">Rs</span><input type="number" id="q-tariff" name="tariff" min="1" max="30" step="0.1" inputmode="decimal" placeholder="8" /></div></div>
          {sel("connection", "Electricity connection", ["Domestic (home)", "Commercial", "Industrial LT", "Industrial HT", "Not sure"])}
        </div>
        <div class="field-row">
          <div class="field"><label for="q-load">Sanctioned load (optional)</label><div class="q-inline"><input type="number" id="q-load" name="sanctioned_load" min="0" step="any" inputmode="decimal" placeholder="e.g. 5" /><select name="load_unit" aria-label="Load unit"><option>kW</option><option>kVA</option></select></div></div>
          {sel("backup", "Do you use an inverter battery or generator?", ["Inverter battery", "Diesel generator", "Both", "No"])}
        </div>
        <div class="q-estimate" id="qEstimate" hidden>
          <p class="q-est__kicker">Your instant estimate</p>
          <div class="q-est__grid">
            <div><b data-est="size">-</b><span>System size</span></div>
            <div><b data-est="save">-</b><span>Savings per month</span></div>
            <div><b data-est="payback">-</b><span>Payback</span></div>
            <div><b data-est="co2">-</b><span>CO2 avoided a year</span></div>
          </div>
          <p class="q-est__loss" data-est="loss"></p>
          <p class="q-est__note">Indicative only. Same model as our savings calculator: <span data-est="assume"></span> Your free proposal will be based on your actual site.</p>
        </div>
        <div class="q-nav"><button type="button" class="btn btn--outline" data-back>Back</button><button type="button" class="btn btn--primary" data-next>Continue {ARROW_SVG}</button></div>
      </fieldset>

      <fieldset class="q-step" data-step="5">
        <legend>When would you like to start?</legend>
        <div class="q-opts q-opts--pills">{timeline}</div>
        <div class="field-row">
          {sel("roof_owner", "Do you own the roof or land?", ["Yes, I own it", "It is rented / leased", "It belongs to the society", "Not sure"])}
          {sel("role", "You are", ["Home owner", "Business owner / director", "Society committee member", "Manager / engineer", "Other"])}
        </div>
        <div class="q-nav"><button type="button" class="btn btn--outline" data-back>Back</button><button type="button" class="btn btn--primary" data-next>Last step {ARROW_SVG}</button></div>
      </fieldset>

      <fieldset class="q-step" data-step="6">
        <legend>Where should we send your free quote?</legend>
        <div class="q-summary" id="qSummary" hidden></div>
        <div class="field-row">
          <div class="field"><label for="q-name">Full name *</label><input type="text" id="q-name" name="name" autocomplete="name" maxlength="100" required /></div>
          <div class="field"><label for="q-company">Company / society (optional)</label><input type="text" id="q-company" name="company" autocomplete="organization" maxlength="120" /></div>
        </div>
        <div class="field-row">
          <div class="field"><label for="q-phone">Mobile number *</label><input type="tel" id="q-phone" name="phone" placeholder="+91 " autocomplete="tel" inputmode="tel" pattern="[0-9+\\(\\)\\s\\-]{{7,20}}" title="Phone number: 7 to 20 digits, spaces, +, - or brackets" maxlength="20" required /></div>
          <div class="field"><label for="q-email">Email *</label><input type="email" id="q-email" name="email" autocomplete="email" maxlength="254" required /></div>
        </div>
        <div class="field-row">
          {sel("contact_by", "Best way to reach you", ["Phone call", "WhatsApp", "Email"])}
          {sel("best_time", "Best time to call", ["Morning (9 to 12)", "Afternoon (12 to 4)", "Evening (4 to 7)", "Any time"])}
        </div>
        <div class="field"><label for="q-message">Anything else? (optional)</label><textarea id="q-message" name="message" maxlength="2000" placeholder="Roof condition, shade from trees or buildings, deadlines, preferred brands…"></textarea></div>
        {sel("heard_from", "How did you hear about us?", ["Google search", "Facebook / Instagram / X", "YouTube", "A friend or neighbour", "Saw our work locally", "Other"])}
        <p class="form-consent">By submitting this form, you agree to our <a href="/privacy-policy/">Privacy Policy</a>. We use your details only to prepare your quote and never add you to a mailing list.</p>
        <div class="q-nav"><button type="button" class="btn btn--outline" data-back>Back</button><button type="submit" class="btn btn--sun q-submit">Send Me My Free Quote {ARROW_SVG}</button></div>
        <ul class="q-assure"><li>{tick}Free</li><li>{tick}No obligation</li><li>{tick}Your details are used only to reply</li></ul>
        <div class="form-status" id="quoteStatus" role="status"></div>
      </fieldset>

      <div class="q-done" id="quoteDone" hidden>
        <span class="q-done__ic" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg></span>
        <h2>Thank you<span data-done-name></span>! Your request is in.</h2>
        <p>Our team will study your details and call you to plan a free site visit. Meanwhile, read how the subsidy and the whole process work.</p>
        <ol class="q-done__next"><li><b>Review</b>We study your bill, roof or land and goals.</li><li><b>Call &amp; site visit</b>We talk, then visit your site for free.</li><li><b>Proposal</b>System size, savings and an all-inclusive price, with no obligation.</li></ol>
        <div class="q-nav q-nav--center"><a class="btn btn--outline" href="/how-it-works/">How it works</a><a class="btn btn--primary" href="/pm-surya-ghar-subsidy/">PM Surya Ghar subsidy guide</a></div>
      </div>
    </form>

    <aside class="quote-trust reveal" data-d="1">
      <div class="qt-brand"><img src="assets/img/logo.png" alt="Lotus Sun Energy logo" width="270" height="270" /><p><b>Lotus Sun Energy</b>Serving the Nation, From Olive Green to Go Green</p></div>
      <ul class="qt-points">
        <li><b>Veteran-led</b>An ex-servicemen enterprise: discipline, integrity and keeping our word.</li>
        <li><b>Free site visit</b>We check your roof or land, shade and bills before we quote.</li>
        <li><b>Subsidy and approvals handled</b>PM Surya Ghar registration, DISCOM feasibility, net metering and inspection.</li>
        <li><b>Quality, warrantied components</b>BIS-certified, ALMM-listed modules and trusted inverters, chosen for your site.</li>
        <li><b>Transparent pricing</b>One all-inclusive quote, with GST and the subsidy shown line by line.</li>
      </ul>
      <p class="qt-mail">Prefer email? Write to <a href="mailto:{EMAIL}">{EMAIL}</a>. We reply within one working day.</p>
    </aside>
  </div>
</section>

<section class="section section--soft">
  <div class="container">
    <div class="section-head center reveal"><span class="eyebrow">What Happens Next</span><h2>From Request to <span class="text-grad">Proposal</span></h2></div>
    <ol class="proc-steps q-next">
      <li class="reveal" data-d="0"><span class="st-n">1</span><div><b>We review your request</b><p>We study your bill, your roof or land and what you want to achieve.</p></div></li>
      <li class="reveal" data-d="1"><span class="st-n">2</span><div><b>We call and visit</b><p>A short call, then a free site visit to check space, shade and wiring.</p></div></li>
      <li class="reveal" data-d="2"><span class="st-n">3</span><div><b>You get a clear proposal</b><p>System size, expected savings and an all-inclusive price, with no obligation.</p></div></li>
    </ol>
    <div class="section-cta reveal"><a class="btn btn--outline" href="/how-it-works/">How going solar works</a><a class="btn btn--outline" href="/faq/">Questions? Read the FAQ</a></div>
  </div>
</section>
<script src="assets/js/quote.js?v={ASSET_VERSION}"></script>"""
    ld = [{"@context": "https://schema.org", "@type": "ContactPage", "name": "Get a free solar quote",
           "url": SITE_URL + page_url("free-solar-quote.html"), "about": {"@id": SITE_URL + "/#organization"},
           "potentialAction": {"@type": "QuoteAction", "agent": {"@type": "Person"}, "object": {"@id": SITE_URL + "/#organization"}}}]
    return page_shell("quote", body, ld)


def write_generated_pages():
    for a in ARTICLES:
        write_page(a["file"], render_article_page(a))
    for fname, render in (("free-solar-quote.html", render_quote_page), ("faq.html", render_faq_page),
                          ("solar-glossary.html", render_glossary_page), ("insights.html", render_insights_page)):
        write_page(fname, render())


# -------------------------------------------------------------- pages ----
def image_size(path):
    """(width, height) for JPEG/PNG/SVG without third-party libraries."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    if path.endswith(".svg"):
        t = data.decode("utf8", "ignore")
        vb = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"', t)
        if vb:
            return round(float(vb.group(1))), round(float(vb.group(2)))
    return None


def set_attr(tag, name, value):
    if re.search(rf'\s{name}="', tag):
        return re.sub(rf'\s{name}="[^"]*"', f' {name}="{value}"', tag)
    return re.sub(r"\s*/?>$", f' {name}="{value}" />', tag)


def del_attr(tag, name):
    return re.sub(rf'\s{name}="[^"]*"', "", tag)


def set_attr(tag, name, value):
    if re.search(rf'\s{name}="', tag):
        return re.sub(rf'\s{name}="[^"]*"', f' {name}="{value}"', tag)
    return re.sub(r"\s*/?>$", f' {name}="{value}" />', tag)


def del_attr(tag, name):
    return re.sub(rf'\s{name}="[^"]*"', "", tag)


def brand_alt(tag, src):
    """Photos of our own work (assets/photos/) always name the company, so image search leads back to us."""
    src = src.lstrip("/")
    alt = re.search(r'\salt="([^"]*)"', tag)
    if not alt or not src.startswith(BRAND_DIRS) or "Lotus Sun Energy" in alt.group(1) or not alt.group(1):
        return tag
    return tag.replace(alt.group(0), f' alt="{alt.group(1).rstrip(".")}, Lotus Sun Energy"', 1)


BRAND_DIRS = ("assets/photos/",)


def fix_heading_levels(body_html):
    """Headings never skip a level (h2 -> h4). A skipped heading is demoted to the next level and keeps
    its look through the .hs class, so the outline is correct without changing the design."""
    prev = [1]

    def fix(m):
        lvl, attrs = int(m.group(1)), m.group(2)
        if lvl > prev[0] + 1:
            new = prev[0] + 1
            attrs = re.sub(r'class="([^"]*)"', r'class="\1 hs"', attrs) if 'class="' in attrs else attrs + ' class="hs"'
            prev[0] = new
            return f"<h{new}{attrs}>", new, lvl
        prev[0] = lvl
        return m.group(0), lvl, lvl

    out, stack = [], []
    pos = 0
    for m in re.finditer(r"<h([1-6])(\s[^>]*)?>|</h([1-6])>", body_html):
        out.append(body_html[pos:m.start()])
        if m.group(1):
            tag, new, old = fix(re.match(r"<h([1-6])((?:\s[^>]*)?)>", m.group(0)))
            stack.append(new)
            out.append(tag)
        else:
            out.append(f"</h{stack.pop() if stack else m.group(3)}>")
        pos = m.end()
    out.append(body_html[pos:])
    return "".join(out)


def add_main(body_html):
    """Wrap the page content between the header and footer in <main>, with a skip link."""
    body_html = re.sub(r'<main id="main">\n?', "", body_html)
    body_html = re.sub(r"\n*</main>\n", "\n", body_html)
    body_html = body_html.replace('<a class="skip-link" href="#main">Skip to content</a>\n', "")
    body_html = body_html.replace("<!-- /build:header -->", '<!-- /build:header -->\n<main id="main">', 1)
    body_html = re.sub(r"(<main id=\"main\">)\n+", r"\1\n", body_html)
    body_html = re.sub(r"\n*<!-- build:footer -->", "\n</main>\n<!-- build:footer -->", body_html, count=1)
    return body_html.replace("<!-- build:header -->", '<a class="skip-link" href="#main">Skip to content</a>\n<!-- build:header -->', 1)


WEBP_DIRS = ("assets/photos/",)
WEBP_WIDTHS = (480, 960, 1600)
SIZES_FULL = "100vw"
SIZES_CARD = "(max-width: 700px) 100vw, (max-width: 1100px) 50vw, 33vw"


def webp_set(rel):
    """Responsive WebP copies of a photo under assets/opt/ (made once, refreshed when the source changes).
    Returns [(url, width)] or [] when the image is not a photo we optimise."""
    rel = rel.lstrip("/").split("?")[0]
    if not rel.startswith(WEBP_DIRS) or not rel.lower().endswith((".jpg", ".jpeg", ".png")):
        return []
    src = os.path.join(ROOT, rel)
    if not os.path.isfile(src):
        return []
    size = image_size(src)
    if not size:
        return []
    widths = [w for w in WEBP_WIDTHS if w < size[0]] + [min(size[0], WEBP_WIDTHS[-1])]
    out = []
    for w in sorted(set(widths)):
        dst_rel = "assets/opt/" + rel[len("assets/"):].rsplit(".", 1)[0] + f"-{w}.webp"
        dst = os.path.join(ROOT, dst_rel)
        if not os.path.isfile(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            from PIL import Image, ImageOps
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            if im.width > w:
                im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            im.save(dst, "WEBP", quality=78, method=6)
        out.append(("/" + dst_rel, w))
    return out


def process_images(body_html):
    """Every local <img>: width/height (no layout shift), async decoding, lazy loading below the fold,
    and a WebP srcset in a <picture>. The first content image is the LCP: eager, high priority."""
    first = [True]
    body_html = re.sub(r'<picture class="rp">(?:<source[^>]*>)*(<img\b[^>]*>)</picture>', r"\1", body_html)

    def fix(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if not src:
            return tag
        path = os.path.join(ROOT, src.group(1).lstrip("/").split("?")[0])
        in_chrome = "brand-mark" in tag or "brand-logo" in tag
        if os.path.isfile(path) and not re.search(r'\swidth="', tag):
            size = image_size(path)
            if size:
                tag = set_attr(tag, "width", size[0])
                tag = set_attr(tag, "height", size[1])
        if in_chrome:
            return tag
        tag = brand_alt(tag, src.group(1))
        tag = set_attr(tag, "decoding", "async")
        hero = first[0]
        if hero:
            first[0] = False
            tag = set_attr(tag, "loading", "eager")
            tag = set_attr(tag, "fetchpriority", "high")
        elif "data-eager" in tag:  # key photos further down (CM mosaic, video thumbnails): never left blank while lazy-loading
            tag = del_attr(tag, "data-eager")
            tag = set_attr(tag, "loading", "eager")
            tag = set_attr(tag, "fetchpriority", "low")  # fetched early, but after the hero and fonts
        else:
            tag = del_attr(tag, "fetchpriority")
            tag = set_attr(tag, "loading", "lazy")
        variants = webp_set(src.group(1))
        if not variants:
            return tag
        full = hero or 'class="slide' in body_html[max(0, m.start() - 120):m.start()]
        srcset = ", ".join(f"{u} {w}w" for u, w in variants)
        sizes = SIZES_FULL if full else SIZES_CARD
        return f'<picture class="rp"><source type="image/webp" srcset="{srcset}" sizes="{sizes}" />{tag}</picture>'

    return re.sub(r"<img\b[^>]*>", fix, body_html)


def hero_preload(body_html):
    """<link rel=preload> for the LCP image, matching the srcset the browser will pick."""
    m = re.search(r'<picture class="rp"><source type="image/webp" srcset="([^"]+)" sizes="([^"]+)" /><img[^>]*fetchpriority="high"', body_html)
    if m:
        return f'<link rel="preload" as="image" type="image/webp" imagesrcset="{m.group(1)}" imagesizes="{m.group(2)}" fetchpriority="high" />'
    m = re.search(r'<img[^>]*fetchpriority="high"[^>]*>', body_html)
    if m:
        src = re.search(r'src="([^"]+)"', m.group(0)).group(1)
        return f'<link rel="preload" as="image" href="{src}" fetchpriority="high" />'
    return ""


FONT_PRELOADS = ('<link rel="preload" href="/assets/fonts/plus-jakarta-sans-var-latin.woff2" as="font" type="font/woff2" crossorigin />\n'
                 '<link rel="preload" href="/assets/fonts/poppins-700-latin.woff2" as="font" type="font/woff2" crossorigin />\n')


def optimise_head_and_scripts(text):
    """Self-hosted fonts and minified assets; every script deferred; LCP image and fonts preloaded."""
    head, body = text.split("</head>", 1)
    head = re.sub(r'<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>\n', "", head)
    head = re.sub(r'<link href="https://fonts\.googleapis\.com/[^"]*" rel="stylesheet" />\n', "", head)
    head = re.sub(r'<link rel="preload"[^>]*>\n', "", head)
    head = re.sub(r'(<link rel="stylesheet" href="/?assets/css/style(?:\.min)?\.css[^"]*" />\n)',
                  lambda m: hero_preload(body) + "\n" + FONT_PRELOADS + m.group(1) if hero_preload(body) else FONT_PRELOADS + m.group(1), head, count=1)
    head = head.replace("\n\n<link rel=\"preload\"", "\n<link rel=\"preload\"")
    text = head + "</head>" + body
    text = re.sub(r"assets/css/style(?:\.min)?\.css", "assets/css/style.min.css", text)
    text = re.sub(r"assets/js/(" + "|".join(JS_SOURCES) + r")(?:\.min)?\.js", r"assets/js/\1.min.js", text)
    text = re.sub(r'<script src="(/assets/js/[^"]+)"(?![^>]*\bdefer)([^>]*)></script>', r'<script src="\1"\2 defer></script>', text)
    return text


def replace_block(text, name, content):
    pat = re.compile(rf"<!-- build:{name} -->.*?<!-- /build:{name} -->", re.S)
    block = f"<!-- build:{name} -->\n{content}\n<!-- /build:{name} -->"
    if pat.search(text):
        return pat.sub(lambda _: block, text)
    placeholder = f'<div id="site-{name}"></div>'
    return text.replace(placeholder, block)


def normalise_links(text):
    """Every internal link points at the clean URL (/about/#x); every asset path is root-absolute."""
    pages = {p[:-5] for p in PAGES if p not in ("404.html",)}
    def page_link(m):
        q, name, frag = m.group(1), m.group(2), m.group(3) or ""
        if name == "index":
            return f'href="/{frag}"'
        return f'href="/{name}/{frag}"' if name in pages else m.group(0)
    # about.html, /about.html, ./about.html, /about, /about/  (+ #fragment)
    text = re.sub(r'href=(["\'])(?:\./|/)?([a-z0-9-]+)(?:\.html|/)?(#[^"\']*)?\1',
                  lambda m: page_link(m) if (m.group(2) in pages or m.group(2) == "index") else m.group(0), text)
    # absolute site URLs in structured data and meta
    text = re.sub(re.escape(SITE_URL) + r'/([a-z0-9-]+)\.html', lambda m: f"{SITE_URL}/" if m.group(1) == "index" else (f"{SITE_URL}/{m.group(1)}/" if m.group(1) in pages else m.group(0)), text)
    # relative asset paths -> root-absolute, so they work from /about/
    text = re.sub(r'(\s(?:src|href|data-full|poster|srcset)=")(assets/|site\.webmanifest|llms\.txt|sitemap\.xml)', r'\1/\2', text)
    text = re.sub(r"url\((['\"]?)assets/", r"url(\1/assets/", text)
    text = re.sub(r"href='([^']*)'", r'href="\1"', text)
    return text


def breadcrumb_ld(fname):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"}]
    meta = PAGES[fname]
    if meta.get("parent"):
        name, path = PARENTS[meta["parent"]]
        items.append({"@type": "ListItem", "position": 2, "name": name, "item": SITE_URL + path})
    if fname != "index.html":
        items.append({"@type": "ListItem", "position": len(items) + 1, "name": meta["crumb"], "item": SITE_URL + meta["path"]})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


# Google Search Console: paste the content="..." value of the google-site-verification meta tag here
# (or verify by DNS instead and leave it empty), then submit /sitemap.xml in Search Console.
GSC_VERIFICATION = ""   # Google Search Console HTML-tag token, once the property is verified
BING_VERIFICATION = ""  # Bing Webmaster Tools token (msvalidate.01); Bing also feeds Copilot and ChatGPT search


def md_url(fname):
    """The Markdown twin of a page: /about/ -> /about/index.md (home -> /index.md)."""
    path = PAGES[fname]["path"] or "/"
    return SITE_URL + path + "index.md"


def head_block(fname, og_image, og_alt):
    meta = PAGES[fname]
    e = lambda s: html.escape(s, quote=True)
    lines = [f"<title>{e(meta['title'])}</title>",
             f'<meta name="description" content="{e(meta["desc"])}" />']
    if meta["path"] is None:
        lines.append('<meta name="robots" content="noindex, follow" />')
        return "\n".join(lines)
    url = SITE_URL + meta["path"]
    lines += [
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />',
        '<meta name="geo.region" content="IN-BR" />', '<meta name="geo.placename" content="Muzaffarpur, Bihar, India" />',
        *([f'<meta name="google-site-verification" content="{GSC_VERIFICATION}" />'] if GSC_VERIFICATION and fname == "index.html" else []),
        *([f'<meta name="msvalidate.01" content="{BING_VERIFICATION}" />'] if BING_VERIFICATION and fname == "index.html" else []),
        f'<link rel="canonical" href="{url}" />',
        f'<link rel="alternate" hreflang="en-IN" href="{url}" />',
        f'<link rel="alternate" hreflang="x-default" href="{url}" />',
        f'<link rel="alternate" type="text/markdown" href="{md_url(fname)}" title="This page as Markdown (for AI assistants)" />',
        f'<link rel="alternate" type="application/rss+xml" href="{SITE_URL}/feed.xml" title="{BRAND}: solar guides" />',
        '<meta property="og:type" content="article" />' if meta.get("kind") == "article" else '<meta property="og:type" content="website" />',
        *([f'<meta property="article:published_time" content="{meta["published"]}" />',
           f'<meta property="article:modified_time" content="{meta["modified"]}" />',
           f'<meta property="article:section" content="{e(meta["section"])}" />'] if meta.get("kind") == "article" else []),
        f'<meta property="og:site_name" content="{BRAND}" />',
        '<meta property="og:locale" content="en_IN" />',
        f'<meta property="og:url" content="{url}" />',
        f'<meta property="og:title" content="{e(meta["title"])}" />',
        f'<meta property="og:description" content="{e(meta["desc"])}" />',
        f'<meta property="og:image" content="{og_image}" />',
    ]
    size = image_size(os.path.join(ROOT, og_image.replace(SITE_URL + "/", "").lstrip("/")))
    if size:
        lines += [f'<meta property="og:image:width" content="{size[0]}" />',
                  f'<meta property="og:image:height" content="{size[1]}" />']
    lines += [
        f'<meta property="og:image:alt" content="{e(og_alt)}" />',
        '<meta name="twitter:card" content="summary_large_image" />',
        f'<meta name="twitter:title" content="{e(meta["title"])}" />',
        f'<meta name="twitter:description" content="{e(meta["desc"])}" />',
        f'<meta name="twitter:image" content="{og_image}" />',
        f'<meta name="twitter:image:alt" content="{e(og_alt)}" />',
    ]
    return "\n".join(lines)


HEAD_TAG_RE = re.compile(
    r'^[ \t]*(?:<title>.*?</title>|<meta (?:property|name)="(?:og:[^"]+|twitter:[^"]+|article:[^"]+|description|robots|geo\.[a-z]+)"[^>]*>'
    r'|<meta name="google-site-verification"[^>]*>|<link rel="canonical"[^>]*>|<link rel="alternate" (?:hreflang|type)="[^"]*"[^>]*>|<meta name="msvalidate\.01"[^>]*>)[ \t]*\n', re.M | re.S)


OG_BRAND = "assets/img/lotus-sun-energy-og.jpg"


def organization_ld():
    return {"@context": "https://schema.org", "@type": ["Organization", "LocalBusiness"], "@id": SITE_URL + "/#organization",
            "name": BRAND, "url": SITE_URL + "/", "logo": f"{SITE_URL}/assets/img/logo.png", "image": f"{SITE_URL}/{OG_BRAND}",
            "description": "Veteran-led (ex-servicemen) solar company: rooftop and ground-mount solar for homes, businesses and industry "
                           "across India, with PM Surya Ghar subsidy assistance, EMI options and free site visits.",
            "slogan": "Serving the Nation, From Olive Green to Go Green", "email": EMAIL,
            "address": {"@type": "PostalAddress", "streetAddress": "Pakhanaha Sriram", "addressLocality": "Muzaffarpur",
                        "addressRegion": "Bihar", "postalCode": "843109", "addressCountry": "IN"},
            "areaServed": [{"@type": "State", "name": "Bihar"}, {"@type": "Country", "name": "India"}],
            "priceRange": "₹₹", "currenciesAccepted": "INR", "knowsLanguage": ["en", "hi"],
            "contactPoint": {"@type": "ContactPoint", "contactType": "customer service", "email": EMAIL,
                             "areaServed": "IN", "availableLanguage": ["English", "Hindi"]},
            "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Solar services", "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "url": SITE_URL + "/" + u + "/"}} for n, u in [
                    ("Rooftop solar for homes", "solar-for-homes"), ("Rooftop solar for societies and businesses", "service-rooftop"),
                    ("Ground-mount solar plants", "service-ground-mount"), ("Turnkey solar EPC", "service-epc"),
                    ("Solar installation and commissioning", "solar-installation-commissioning"), ("Solar operation and maintenance", "service-om")]]},
            "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
                                          "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                                          "opens": "09:00", "closes": "19:00"},
            "knowsAbout": ["Rooftop solar", "Residential solar", "Ground-mount solar", "PM Surya Ghar subsidy", "Net metering",
                           "Solar EPC", "Solar installation and commissioning", "Solar operation and maintenance"]}


def website_ld():
    return {"@context": "https://schema.org", "@type": "WebSite", "@id": SITE_URL + "/#website", "name": BRAND, "url": SITE_URL + "/",
            "publisher": {"@id": SITE_URL + "/#organization"}, "inLanguage": "en-IN"}


def process_page(fname):
    path = page_path(fname)
    text = open(path, encoding="utf8").read()
    text = KNOWN_HOSTS.sub(SITE_URL, text)
    page_key = re.search(r'<body data-page="([^"]+)"', text).group(1)

    # header / footer / shared blocks baked in
    text = replace_block(text, "header", render_header(page_key, fname))
    text = replace_block(text, "footer", FOOTER)
    for name, render in BLOCKS.items():
        if f"<!-- build:{name} -->" in text:
            text = replace_block(text, name, render())

    # head: one brand share image (1200 x 630) everywhere
    head, body = text.split("</head>", 1)
    og_image = f"{SITE_URL}/{OG_BRAND}"
    alt = "Lotus Sun Energy, veteran-led solar company: Serving the Nation, From Olive Green to Go Green"
    head = HEAD_TAG_RE.sub("", head)
    head = re.sub(r'(<meta name="viewport"[^>]*>\n)', lambda m: m.group(1) + head_block(fname, og_image, alt) + "\n", head, count=1)
    head = re.sub(r'(?:<link rel="(?:icon|apple-touch-icon|manifest)"[^>]*>\n)+',
                  '<link rel="icon" href="/favicon.ico" sizes="48x48" />\n'
                  '<link rel="icon" href="/assets/img/favicon-32.png" type="image/png" sizes="32x32" />\n'
                  '<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png" />\n'
                  '<link rel="manifest" href="/site.webmanifest" />\n', head, count=1)

    def link_provider(m):
        data = json.loads(m.group(2))
        if isinstance(data, dict) and data.get("@type") == "Service" and "@id" not in data.get("provider", {}):
            data["provider"] = {"@id": SITE_URL + "/#organization"}
            return m.group(1) + "\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>"
        return m.group(0)
    head = re.sub(r'(<script type="application/ld\+json">)\s*(.*?)\s*</script>', link_provider, head, flags=re.S)
    head = re.sub(r'<script type="application/ld\+json" data-build="(?:org|site)">.*?</script>\n', "", head, flags=re.S)
    if fname == "index.html":
        head += ('<script type="application/ld+json" data-build="org">\n' + json.dumps(organization_ld(), ensure_ascii=False, indent=2)
                 + '\n</script>\n<script type="application/ld+json" data-build="site">\n' + json.dumps(website_ld(), ensure_ascii=False, indent=2)
                 + "\n</script>\n")
    if PAGES[fname]["path"] and '"BreadcrumbList"' not in head:
        head += '<script type="application/ld+json">\n' + json.dumps(breadcrumb_ld(fname), ensure_ascii=False, indent=2) + "\n</script>\n"
    text = head + "</head>" + body

    # links, asset versions, scripts
    text = normalise_links(text)
    text = re.sub(r"\?v=[0-9a-f]+", f"?v={ASSET_VERSION}", text)
    # the PDF library is loaded on demand by components.js (window.loadScript)
    text = re.sub(r'<script src="/?assets/js/jspdf\.umd\.min\.js[^"]*"[^>]*></script>\n', "", text)

    # images
    head, body = text.split("</head>", 1)
    # the header logo is chrome; the hero is the first image after </header>
    pre, sep, post = body.partition("</header>")
    body = pre + sep + fix_heading_levels(process_images(post)) if sep else process_images(body)
    body = add_main(body)
    text = optimise_head_and_scripts(head + "</head>" + body)

    # 404 is served at arbitrary depths: make its URLs root-absolute
    if fname == "404.html":
        text = re.sub(r'(src|href)="(?!https?:|mailto:|tel:|/|#|data:)([^"]+)"', r'\1="/\2"', text)

    open(path, "w", encoding="utf8").write(text)


# -------------------------------------------------------- site files ----
def write_sitemap():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for fname, meta in PAGES.items():
        if not meta["path"]:
            continue
        text = open(page_path(fname), encoding="utf8").read()
        body = text.split("</header>", 1)[-1]
        imgs = []
        for src in re.findall(r'(?:src|data-full)="/?(assets/photos/[^"]+\.(?:jpe?g|png|webp))"', body):
            if src not in imgs:
                imgs.append(src)
        out.append(f"  <url>\n    <loc>{SITE_URL}{meta['path']}</loc>\n    <lastmod>{LASTMOD.get(fname, TODAY)}</lastmod>")
        for src in imgs:
            out.append(f"    <image:image><image:loc>{SITE_URL}/{src}</image:loc></image:image>")
        out.append("  </url>")
    out.append("</urlset>\n")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf8").write("\n".join(out))


AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
           "Perplexity-User", "Google-Extended", "Applebot", "Applebot-Extended", "Bingbot", "DuckAssistBot", "meta-externalagent",
           "MistralAI-User", "CCBot", "Amazonbot", "YouBot"]


def write_robots():
    """Every crawler is welcome, search engines and AI assistants alike: being found and cited is the point.
    The AI crawlers are named explicitly so a blanket rule elsewhere (a CDN default, say) cannot be mistaken for our intent."""
    bots = "".join(f"User-agent: {b}\n" for b in AI_BOTS)
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf8").write(
        "# Lotus Sun Energy: search engines and AI assistants may crawl, index and cite this site.\n"
        "User-agent: *\nAllow: /\nDisallow: /tools/\n\n"
        "# AI search and assistant crawlers: welcome\n" + bots + "Allow: /\nDisallow: /tools/\n\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
        f"# Plain-language summary for AI assistants: {SITE_URL}/llms.txt\n"
        f"# Full text of every page in one file: {SITE_URL}/llms-full.txt\n"
        f"# Guides feed: {SITE_URL}/feed.xml\n")


def _plain(x):
    return html.unescape(re.sub(r"<[^>]+>", "", x)).strip()


def write_llms():
    """llms.txt: a plain-language map of the site for AI assistants (llmstxt.org)."""
    def line(f):
        m = PAGES[f]
        return f"- [{m['title'].split(' | ')[0]}]({SITE_URL}{m['path']}): {m['desc']}"
    groups = [
        ("For homes", ["solar-for-homes.html", "pm-surya-ghar-subsidy.html", "solar-in-bihar.html", "how-it-works.html"]),
        ("Company", ["about.html", "ex-servicemen-led-msme.html", "quality-safety.html", "industries.html",
                     "contact.html", "free-solar-quote.html"]),
        ("Services", ["service-rooftop.html", "service-ground-mount.html", "capex-solar-epc.html", "service-epc.html",
                      "solar-installation-commissioning.html", "service-piling.html", "service-civil.html", "service-om.html"]),
        ("Solar guides for India (updated " + max(a["updated"] for a in ARTICLES) + ")", ["insights.html"] + [a["file"] for a in ARTICLES]),
        ("Reference", ["solar-schemes-india.html", "solar-glossary.html", "faq.html"]),
    ]
    out = ["# Lotus Sun Energy", "",
           "> Veteran-led (ex-servicemen) solar company based in Muzaffarpur, Bihar, India. Mainly rooftop solar for homes "
           "and housing societies, with full help on the PM Surya Ghar subsidy, net metering and EMIs; also rooftop and "
           "ground-mount solar for shops, businesses, institutions, industry and farms. "
           "Motto: \"Serving the Nation, From Olive Green to Go Green\".", "",
           "Every page below also has a clean Markdown version: add `index.md` to its URL (for example "
           f"{SITE_URL}/about/index.md). The full text of the whole site is in one file at {SITE_URL}/llms-full.txt.", "",
           "## Key facts",
           "- Main focus: rooftop solar for individual homes (typically 1 to 10 kW) and housing societies, with a free site visit, "
           "one all-inclusive quote, and the PM Surya Ghar portal registration, DISCOM feasibility, net meter, inspection and "
           "subsidy claim handled for the customer (central subsidy up to Rs 78,000 for 3 kW or more).",
           "- Also: rooftop systems for shops, offices, schools and factories; ground-mount plants; turnkey EPC; installation & "
           "commissioning; pile foundations, civil works and fencing; operation & maintenance.",
           "- In Bihar: north Bihar (including Muzaffarpur) is served by NBPDCL and south Bihar by SBPDCL; free site visits across the state.",
           "- Equipment: Lotus Sun Energy does not manufacture modules or inverters; it specifies BIS-certified, ALMM-listed modules "
           "(Indian-made DCR modules for subsidy systems) and warrantied inverters.",
           "- Lotus Sun Energy is a new company: it does not claim past projects, clients or awards on this website.",
           f"- Office: {ADDRESS}. Hours: Monday to Saturday, 9 AM to 7 PM. Free site visits across India.",
           f"- Contact: {EMAIL}, the form at {SITE_URL}/contact/ or a free quote at {SITE_URL}/free-solar-quote/", ""]
    for title, files in groups:
        out.append(f"## {title}")
        out += [line(f) for f in files if f in PAGES]
        out.append("")
    out.append("## Quick answers")
    out += [f"- **{_plain(q)}** {_plain(a)}" for _, items in FAQ for q, a in items][:14]
    out.append("")
    out += ["## Optional",
            f"- [Full text of the site]({SITE_URL}/llms-full.txt): every page as Markdown in one file",
            f"- [Guides feed]({SITE_URL}/feed.xml): RSS feed of the solar guides",
            f"- [Sitemap]({SITE_URL}/sitemap.xml): every page", ""]
    open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf8").write("\n".join(out))


# ------------------------------------------------- markdown twins ----
class _MD(html.parser.HTMLParser):
    """Turns a page's <main> into readable Markdown: headings, paragraphs, lists, tables and links; no chrome."""
    SKIP = {"script", "style", "svg", "nav", "form", "button", "template", "noscript", "select", "textarea", "iframe", "video", "picture"}
    BLOCK = {"caption", "p", "div", "section", "article", "aside", "header", "footer", "figure", "figcaption", "blockquote", "details",
             "summary", "dl", "dt", "dd", "ul", "ol", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.href, self.link_text, self.row, self.cell = [], 0, None, [], None, None
        self.rows_seen = 0
        self.list_depth = 0

    def nl(self, n=2):
        self.out.append("\n" * n)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip or tag in self.SKIP or "hidden" in a or a.get("aria-hidden") == "true" \
                or "is-hidden" in (a.get("class") or "") or "sr-only" in (a.get("class") or "") and tag != "span":
            if tag not in ("br", "img", "input", "source", "meta", "link", "hr"):
                self.skip += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.nl(); self.out.append("#" * int(tag[1]) + " ")
        elif tag == "li":
            self.nl(1); self.out.append("  " * max(self.list_depth - 1, 0) + "- ")
        elif tag in ("ul", "ol"):
            self.list_depth += 1; self.nl(1)
        elif tag == "br":
            self.out.append("\n")
        elif a.get("data-count"):  # animated counters start at 0: print the real figure
            self.out.append(("**" if tag in ("b", "strong") else "") + a.get("data-prefix", "") + a["data-count"] + a.get("data-suffix", "")
                            + ("**" if tag in ("b", "strong") else "") + " ")
            self.skip += 1
        elif tag in ("b", "strong"):
            prev = "".join(self.out[-2:])
            self.out.append(": **" if prev[-1:].isalnum() else "**")
        elif tag == "a" and a.get("href") and not a["href"].startswith(("#", "javascript:")):
            h = a["href"]
            self.href = h if h.startswith(("http", "mailto:", "tel:")) else SITE_URL + h
            self.link_text = []
            self.out.append("\x00")
        elif tag == "img" and a.get("alt") and self.cell is None:
            pass
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
        elif tag == "table":
            self.nl(); self.rows_seen = 0
        elif tag in self.BLOCK:
            self.nl()

    def handle_endtag(self, tag):
        if self.skip:
            if tag not in ("br", "img", "input", "source", "meta", "link", "hr"):
                self.skip -= 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.nl()
        elif tag in ("ul", "ol"):
            self.list_depth = max(self.list_depth - 1, 0); self.nl(1)
        elif tag in ("b", "strong"):
            self.out.append("**")
        elif tag == "a" and self.href:
            i = len(self.out) - 1 - self.out[::-1].index("\x00")
            text = "".join(self.out[i + 1:]).strip()
            self.out[i:] = [f"[{text}]({self.href})" if text else ""]
            self.href = None
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()).replace("|", "/"))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if any(self.row):
                self.out.append("| " + " | ".join(self.row) + " |\n")
                if self.rows_seen == 0:
                    self.out.append("|" + " --- |" * len(self.row) + "\n")
                self.rows_seen += 1
            self.row = None
        elif tag in self.BLOCK:
            self.nl()

    def handle_data(self, data):
        if self.skip:
            return
        text = re.sub(r"\s+", " ", data)
        if self.cell is not None:
            self.cell.append(text)
        else:
            self.out.append(text)

    def markdown(self):
        md = "".join(self.out).replace("\x00", "")
        md = re.sub(r"\*\*\s*\*\*", "", md)
        md = re.sub(r"[ \t]+\n", "\n", md)
        md = re.sub(r"\n[ \t]+(?=[^-\s|])", "\n", md)
        md = re.sub(r"\n{3,}", "\n\n", md)
        return md.strip() + "\n"


def page_markdown(fname):
    text = open(page_path(fname), encoding="utf8").read()
    main = re.search(r"<main\b[^>]*>(.*)</main>", text, re.S)
    p = _MD()
    p.feed(main.group(1) if main else "")
    meta = PAGES[fname]
    head = (f"---\ntitle: {meta['title']}\ndescription: {meta['desc']}\nurl: {SITE_URL}{meta['path']}\n"
            f"last_updated: {LASTMOD.get(fname, TODAY)}\nsource: {BRAND} ({LEGAL})\n---\n\n")
    return head + p.markdown()


def write_markdown():
    """A Markdown twin of every page (/about/index.md) and the whole site in one file (llms-full.txt), so AI assistants
    and agents can read the content without the page chrome."""
    full = [f"# {LEGAL}: full site text\n\n> Every page of {SITE_URL} as Markdown, generated {TODAY}. "
            f"Page index: {SITE_URL}/llms.txt\n"]
    for fname, meta in PAGES.items():
        if not meta["path"]:
            continue
        md = page_markdown(fname)
        out = os.path.join(os.path.dirname(page_path(fname)), "index.md")
        open(out, "w", encoding="utf8").write(md)
        full.append(f"\n\n---\n\nSource: {SITE_URL}{meta['path']}\n\n" + md.split("---\n\n", 1)[-1])
    open(os.path.join(ROOT, "llms-full.txt"), "w", encoding="utf8").write("".join(full))


# ------------------------------------------------- lastmod, feed, IndexNow ----
LASTMOD = {}
LASTMOD_FILE = os.path.join(ROOT, "tools", "lastmod.json")


def compute_lastmod():
    """Each page's lastmod changes only when its visible content changes (a hash of <title>, description and <main>),
    so search engines can trust the dates in sitemap.xml."""
    try:
        store = json.load(open(LASTMOD_FILE, encoding="utf8"))
    except (OSError, ValueError):
        store = {}
    for fname, meta in PAGES.items():
        if not meta["path"]:
            continue
        t = open(page_path(fname), encoding="utf8").read()
        main = re.search(r"<main\b.*</main>", t, re.S)
        sig = meta["title"] + meta["desc"] + re.sub(r"\?v=[0-9a-f]+|\s+", "", main.group(0) if main else t)
        h = hashlib.sha1(sig.encode("utf8")).hexdigest()[:16]
        old = store.get(fname)
        if old and old[0] == h:
            day = old[1]
        elif old:
            day = TODAY
        else:  # first time: the date the page was last committed
            try:
                day = subprocess.run(["git", "log", "-1", "--format=%cs", "--", os.path.relpath(page_path(fname), ROOT)],
                                     cwd=ROOT, capture_output=True, text=True, timeout=20).stdout.strip() or TODAY
            except (OSError, subprocess.SubprocessError):
                day = TODAY
        if meta.get("kind") == "article" and meta.get("modified", "") > day:
            day = meta["modified"]
        store[fname] = [h, day]
        LASTMOD[fname] = day
    json.dump(dict(sorted(store.items())), open(LASTMOD_FILE, "w", encoding="utf8"), indent=1)


def write_feed():
    """RSS 2.0 feed of the solar guides, newest first."""
    from email.utils import format_datetime
    from datetime import datetime, timezone

    def rfc(d):
        return format_datetime(datetime.fromisoformat(d).replace(hour=9, tzinfo=timezone.utc))
    items = []
    for a in sorted(ARTICLES, key=lambda a: (a["updated"], a["date"]), reverse=True):
        m = PAGES[a["file"]]
        url = SITE_URL + m["path"]
        items.append(f"""  <item>
    <title>{esc(a['title'])}</title>
    <link>{url}</link>
    <guid isPermaLink="true">{url}</guid>
    <pubDate>{rfc(a['date'])}</pubDate>
    <category>{esc(a['tag'])}</category>
    <description>{esc(m['desc'])}</description>
  </item>""")
    last = rfc(max(a["updated"] for a in ARTICLES))
    open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf8").write(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{BRAND}: Solar Guides for India</title>
  <link>{SITE_URL}/insights/</link>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
  <description>Plain-English guides to solar in India: the PM Surya Ghar subsidy, net metering, GST, ALMM, batteries, CAPEX vs OPEX, installation and maintenance, from a veteran-led solar company.</description>
  <language>en-in</language>
  <lastBuildDate>{last}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
""")


INDEXNOW_KEY = "3f6b1d9e8c2a47f0b5e4d7c1a9f2e6b8"  # served at /<key>.txt; tools/indexnow.py pings Bing, Yandex & co.


def write_indexnow_key():
    open(os.path.join(ROOT, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf8").write(INDEXNOW_KEY)


# Response headers for Cloudflare Pages (written to _headers). Security headers on every response,
# long caching for versioned CSS/JS and fonts. Third-party hosts allowed by the CSP: FormSubmit (forms) and
# Cloudflare Web Analytics (cookieless; only active if it is switched on in the Cloudflare dashboard).
# Add any new third-party service here AND describe it in privacy-policy/index.html.
CSP = ("default-src 'self'; script-src 'self' https://static.cloudflareinsights.com; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: https:; font-src 'self'; media-src 'self'; connect-src 'self' https://formsubmit.co https://cloudflareinsights.com; "
       "frame-src 'none'; form-action 'self' https://formsubmit.co; base-uri 'self'; object-src 'none'; frame-ancestors 'self'; "
       "upgrade-insecure-requests")
HEADERS = [
    ("/*", {"Strict-Transport-Security": "max-age=63072000; includeSubDomains", "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN", "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
            "Cross-Origin-Opener-Policy": "same-origin", "Content-Security-Policy": CSP}),
    ("/assets/css/*", {"Cache-Control": "public, max-age=31536000, immutable"}),
    ("/assets/js/*", {"Cache-Control": "public, max-age=31536000, immutable"}),
    ("/assets/fonts/*", {"Cache-Control": "public, max-age=31536000, immutable", "Access-Control-Allow-Origin": "*"}),
    ("/assets/img/*", {"Cache-Control": "public, max-age=2592000"}),
    ("/assets/photos/*", {"Cache-Control": "public, max-age=2592000"}),
    ("/assets/opt/*", {"Cache-Control": "public, max-age=2592000"}),
    ("/*.md", {"Content-Type": "text/markdown; charset=utf-8", "X-Robots-Tag": "noindex", "Cache-Control": "public, max-age=3600"}),
    ("/llms.txt", {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "public, max-age=3600"}),
    ("/llms-full.txt", {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "public, max-age=3600"}),
    ("/feed.xml", {"Content-Type": "application/rss+xml; charset=utf-8", "Cache-Control": "public, max-age=3600"}),
    ("/sitemap.xml", {"Content-Type": "application/xml; charset=utf-8", "Cache-Control": "public, max-age=3600"}),
]


def write_headers():
    """_headers in Cloudflare Pages format (tools/serve.py reads the same file for local previews)."""
    out = ["# Generated by tools/build.py (HEADERS). Cloudflare Pages format. Edit HEADERS in tools/build.py, not this file."]
    for path, values in HEADERS:
        out.append(path)
        out += [f"  {k}: {v}" for k, v in values.items()]
    open(os.path.join(ROOT, "_headers"), "w", encoding="utf8").write("\n".join(out) + "\n")


def write_redirects():
    """Old .html and extensionless addresses 301 to the one clean URL, including the pages of the earlier
    one-page site (residential.html, subsidy.html, privacy.html). The .html files no longer exist, so these
    rules never shadow real content and cannot loop."""
    lines = ["# Generated by tools/build.py: every old address 301s to the page's one clean URL (/about/)."]
    for fname, meta in PAGES.items():
        if meta["path"] and fname != "index.html":
            lines.append(f"/{fname}  {meta['path']}  301")
    # Only plain 301 rules (Cloudflare Pages ignores 404/forced rules). Pages also drops .html itself, so these are a safety net.
    lines += ["/index.html  /  301", "/index  /  301",
              "/residential.html  /solar-for-homes/  301", "/residential  /solar-for-homes/  301",
              "/subsidy.html  /pm-surya-ghar-subsidy/  301", "/subsidy  /pm-surya-ghar-subsidy/  301",
              "/privacy.html  /privacy-policy/  301", "/privacy  /privacy-policy/  301", "/privacy/  /privacy-policy/  301",
              "/tools/*  /  301"]
    open(os.path.join(ROOT, "_redirects"), "w", encoding="utf8").write("\n".join(lines) + "\n")


# --------------------------------------------------------- link check ----
def check_links():
    ids, problems = {}, []
    for fname in PAGES:
        t = open(page_path(fname), encoding="utf8").read()
        ids[fname] = set(re.findall(r'\sid="([^"]+)"', open(page_path(fname), encoding="utf8").read()))
    for fname in PAGES:
        t = open(page_path(fname), encoding="utf8").read()
        t = re.sub(r"<script\b(?![^>]*\bsrc=)[^>]*>.*?</script>", "", t, flags=re.S)
        for attr, url in re.findall(r'\s(href|src|data-full)="([^"]*)"', t):
            if re.match(r"(https?:|mailto:|tel:|data:|javascript:)", url) or url == "":
                continue
            base, _, frag = url.partition("#")
            base = base.split("?")[0]
            if base.endswith(".html") or (base and not base.startswith("/")):
                problems.append(f"{fname}: link not in clean form {url}")
                continue
            if base in ("", "/") or base.endswith("/"):
                target = fname if url.startswith("#") else ("index.html" if base in ("", "/") else base.strip("/") + ".html")
                if target not in PAGES:
                    problems.append(f"{fname}: page not in PAGES {url}")
                elif frag and frag not in ids.get(target, set()):
                    problems.append(f"{fname}: missing anchor {url}")
            elif not os.path.isfile(os.path.join(ROOT, base.lstrip("/"))):
                problems.append(f"{fname}: missing file {url}")
    css = open(os.path.join(ROOT, "assets/css/style.css"), encoding="utf8").read()
    for url in re.findall(r"url\(['\"]?([^'\")]+)", css):
        if not url.startswith(("data:", "http")) and not os.path.isfile(os.path.join(ROOT, "assets/css", url)):
            problems.append(f"style.css: missing {url}")
    # stylesheet sanity: catch mangled colour values such as rgba(6, 78, 59.08)
    for m in re.finditer(r"rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\.\d+\s*\)", css):
        problems.append(f"style.css: malformed colour {m.group(0)}")
    for fname in PAGES:
        t = open(page_path(fname), encoding="utf8").read()
        for tag in re.findall(r"<img\b[^>]*>", t):
            if not re.search(r'\salt="[^"]+"', tag):
                problems.append(f"{fname}: <img> without alt: {tag[:90]}")
        if len(re.findall(r"<h1\b", t)) != 1:
            problems.append(f"{fname}: expected exactly one <h1>")
        title = html.unescape(re.search(r"<title>(.*?)</title>", t).group(1))
        desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', t).group(1))
        if not 50 <= len(title) <= 60:
            problems.append(f"{fname}: title is {len(title)} chars (want 50-60)")
        if not 135 <= len(desc) <= 155:
            problems.append(f"{fname}: description is {len(desc)} chars (want 135-155)")
        prev = 1
        for lvl in re.findall(r"<h([1-6])\b", t.split("</header>", 1)[-1]):
            if int(lvl) > prev + 1:
                problems.append(f"{fname}: heading jumps from h{prev} to h{lvl}")
            prev = int(lvl)
        if t.count('<link rel="canonical"') != (1 if PAGES[fname]["path"] else 0):
            problems.append(f"{fname}: canonical tag count")
        if "<main" not in t:
            problems.append(f"{fname}: no <main> landmark")
        body = re.sub(r'<script type="application/ld\+json".*?</script>', "", t.split("</head>", 1)[-1], flags=re.S)
        if KNOWN_HOSTS.search(re.sub(r"\s(?:href|src)=\"https?://[^\"]*\"", lambda m: m.group(0) if KNOWN_HOSTS.search(m.group(0)) else "", body)):
            problems.append(f"{fname}: a link or image uses the full domain; internal links must be root-relative (/about/)")
        for m in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', t, re.S):
            try:
                json.loads(m)
            except ValueError as err:
                problems.append(f"{fname}: invalid JSON-LD ({err})")
    return problems


def main():
    write_min_assets()
    write_generated_pages()
    for fname in PAGES:
        process_page(fname)
    compute_lastmod()
    write_sitemap()
    write_llms()
    write_markdown()
    write_feed()
    write_indexnow_key()
    write_robots()
    write_redirects()
    write_headers()
    problems = check_links()
    for p in problems:
        print("PROBLEM:", p)
    print(f"Built {len(PAGES)} pages for {SITE_URL}, {len(problems)} problem(s).")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
