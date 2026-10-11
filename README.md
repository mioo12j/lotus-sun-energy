# Lotus Sun Energy, company website

Source for https://lotussunenergy.com/, hosted on Cloudflare Pages.

Built and maintained by **Siddhant Kumar** for Lotus Sun Energy. Plain static HTML/CSS/JS: the files here are
what gets served. Colours follow the Lotus Sun Energy logo: navy, solar orange, leaf green, sun gold and lotus pink.

The site is written for households first (rooftop solar for homes, the PM Surya Ghar subsidy, EMIs), with
business, institutional and large ground-mount projects as a second line of services.

## What is (and is not) on the site
Lotus Sun Energy is a new company, so the site carries **no project case studies, client lists, work
experience, news coverage or photos**. Keep it that way until there is real work to show: never add a
project, client, capacity figure or testimonial that did not happen. The heroes and guide cards are drawn
in CSS/SVG; the only images are the logo (`assets/img/logo.png`) and the share image
(`assets/img/lotus-sun-energy-og.jpg`).

## Pages and URLs
Every page lives in its own folder and is served at a clean URL: `about/index.html` is `/about/`.
- Homes first: `/`, `solar-for-homes/`, `pm-surya-ghar-subsidy/`, `solar-in-bihar/`, `how-it-works/`
- Company: `about/`, `ex-servicemen-led-msme/`, `quality-safety/`, `how-it-works/`, `industries/`,
  `contact/`, `free-solar-quote/`, `privacy-policy/`, `terms/` and `404.html`
- Services: `service-rooftop/`, `service-ground-mount/`, `capex-solar-epc/`,
  `service-epc/`, `solar-installation-commissioning/`, `service-piling/`, `service-civil/`, `service-om/`
- Generated on every build (edit the data, not the HTML): the solar guides (`tools/articles.py`),
  `insights/`, `faq/` and `solar-glossary/` (`tools/content.py`) and `free-solar-quote/` (`tools/build.py`)
- `solar-schemes-india/` is hand-edited, with its scheme cards filled from `SCHEMES` in `tools/content.py`

Old addresses from the earlier one-page site (`/residential.html`, `/subsidy.html`, `/privacy.html`,
`/terms.html`, `/about.html`) 301 to their new pages through `_redirects`.

## After any edit: run the build
    pip install rcssmin rjsmin   # once; without them minification is lighter
    python3 tools/build.py

It needs only Python 3. It bakes the shared header and footer into every page (edit `NAV` and `FOOTER`
in `tools/build.py`), sets each page's title, description, canonical, Open Graph and structured data
(`PAGES` in `tools/build.py`), writes `sitemap.xml`, `robots.txt`, `llms.txt`, `llms-full.txt`,
`feed.xml`, `_redirects` and `_headers` (security and caching headers: edit `HEADERS` in `tools/build.py`), a Markdown twin of every page, and minified CSS/JS.
It fails if a link, anchor or image is broken, a page has more than one `<h1>`, a heading level is
skipped, a title is not 50 to 60 characters or a description not 135 to 155. Edit `style.css` and the
`.js` sources, never the `.min` files.

### Adding photos later
Save them under `assets/photos/` with a descriptive file name, use them in a page with a real `alt`
text, and run the build: it adds width/height, lazy loading and WebP copies (`assets/opt/`) automatically.

### Adding a guide
Add an entry to `ARTICLES` in `tools/articles.py` (title, summary, takeaways, sections, FAQ and sources
with links). Every number needs a source.

## Run locally
    python3 tools/serve.py          # then open http://localhost:8766/

## Forms
The contact and quote forms post to FormSubmit, which forwards them to info@lotussunenergy.com. The first
submission from the live site triggers a one-time activation email from FormSubmit to that inbox: click
the link in it, or enquiries will not arrive.

## Deploy (Cloudflare Pages)
1. Cloudflare dashboard > Workers & Pages > Create > Pages > Connect to Git, and pick this repository.
2. Framework preset: None. Build command: leave empty. Build output directory: `/` (the repository root).
3. Deploy, then add `lotussunenergy.com` (and `www.lotussunenergy.com`) under Custom domains. Add a
   redirect rule so `www` goes to `https://lotussunenergy.com` (the canonical address used everywhere).
4. Optional: Web Analytics in the Pages project (cookieless; already allowed by the CSP in `_headers`).

There is no build step on Cloudflare: run `python3 tools/build.py` locally and commit the result.
Cloudflare Pages reads `_headers` (security headers, caching) and `_redirects` (old addresses) from the root,
and serves `404.html` for unknown pages.

## Search engines
After the first deploy: verify the site in Google Search Console and Bing Webmaster Tools (paste the tokens
into `GSC_VERIFICATION` / `BING_VERIFICATION` in `tools/build.py`, or verify by DNS in Cloudflare), submit
`https://lotussunenergy.com/sitemap.xml`, and run `python3 tools/indexnow.py` after each publish.
Create a Google Business Profile for the Muzaffarpur office with the same name, address and hours as the site.
