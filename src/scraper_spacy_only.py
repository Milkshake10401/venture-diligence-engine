"""
Card-aware + spaCy portfolio/company scraper.

Description:
Extracts structured company names from card/grid-style portfolio pages.

Pipeline:
1. Detect repeating card/grid sections.
2. Extract text per section.
3. Apply spaCy ORG entity detection.
4. Fallback to capitalized token heuristic if needed.
5. Deduplicate and clean names.

Note:
Intended for publicly accessible pages. Ensure compliance with site Terms of Service and applicable data licensing.
"""

from urllib.parse import urljoin
from requests_html import HTMLSession
from bs4 import BeautifulSoup


def _fetch_html(url: str, render_js: bool = False) -> str | None:
    """Fetch HTML, optionally render JS for widget-heavy pages."""
    try:
        import pyppeteer, os
        if "--headless" in pyppeteer.launcher.DEFAULT_ARGS:
            pyppeteer.launcher.DEFAULT_ARGS.remove("--headless")

        # Optional: allow environment variable override for Chromium path.
        os.environ.setdefault("PYPPETEER_EXECUTABLE_PATH", os.environ.get("PYPPETEER_EXECUTABLE_PATH", ""))
        if not os.environ["PYPPETEER_EXECUTABLE_PATH"]:
            os.environ.pop("PYPPETEER_EXECUTABLE_PATH", None)

        session = HTMLSession()
        r = session.get(url, timeout=15)
        if render_js:
            r.html.render(timeout=25, sleep=1)
        return r.html.html
    except Exception as e:
        print(f"[!] Fetch/render error for {url}: {e}")
        return None


def scrape_portfolio(url: str, render_js: bool = False):
    """Extract company names from grid/card layouts using spaCy."""
    html = _fetch_html(url, render_js=render_js)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    # --- Step 1: find repeating portfolio cards ---
    # We look for divs or articles with multiple children and relevant keywords
    possible_cards = soup.find_all(
        lambda tag: tag.name in ["div", "article"]
        and ("card" in str(tag.get("class", [])).lower()
             or "grid" in str(tag.get("class", [])).lower()
             or "portfolio" in str(tag.get("class", [])).lower())
    )

    # If no cards found, fall back to all divs under main content
    if not possible_cards:
        possible_cards = soup.find_all("div")

    # Heuristic: find divs with repeating structure (same class, similar length)
    from collections import Counter
    class_counter = Counter(" ".join(tag.get("class", [])) for tag in possible_cards if tag.get("class"))
    common_class = None
    if class_counter:
        common_class, _ = class_counter.most_common(1)[0]

    if common_class:
        cards = [tag for tag in possible_cards if " ".join(tag.get("class", [])) == common_class]
    else:
        cards = possible_cards[:50]  # fallback, take the top 50 divs max

    if not cards:
        print("[!] No card-like sections detected.")
        return []

    print(f"[+] Detected {len(cards)} potential portfolio cards.")

    # --- Step 2: run spaCy per-card ---
    import spacy, re
    nlp = spacy.load("en_core_web_lg")
    names = set()

    # Debug storage for analysis
    debug_rows = []

    for card in cards:
        text = card.get_text(" ", strip=True)
        if not text or len(text) < 3:
            continue

        # skip if it’s just generic category tags
        if text.lower() in {"enterprise", "business", "consumer", "biotech"}:
            continue

        # Try spaCy ORG detection
        doc = nlp(text)
        orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]

        if orgs:
            name = orgs[0]
        else:
            # fallback: first capitalized word(s)
            tokens = [t for t in text.split() if t[0].isupper()]
            name = " ".join(tokens[:2]) if tokens else None

        if not name:
            debug_rows.append({"stage": "skip", "raw": text[:50], "cleaned": "", "decision": "skipped"})
            continue

        # Clean up name
        raw_before = name
        name = re.sub(r"[^A-Za-z0-9&\-\s\.]", "", name)
        name = re.sub(r"\s+", " ", name).strip()

        # --- Context-aware cleaning ---
        # Strip category prefixes like "Business", "Enterprise", etc.
        CATEGORY_PREFIXES = {"business", "enterprise", "consumer", "company", "group", "holdings"}
        tokens = name.split()
        if tokens and tokens[0].lower() in CATEGORY_PREFIXES and len(tokens) > 1:
            cleaned_name = " ".join(tokens[1:])
        else:
            cleaned_name = name

        # Remove trailing periods or commas
        cleaned_name = cleaned_name.strip("., ")

        # Final filter: must have at least one capitalized token and not all uppercase acronyms
        if (len(cleaned_name) > 2 and
            len(cleaned_name.split()) <= 4 and
            any(t[0].isupper() for t in cleaned_name.split()) and
            not cleaned_name.isupper()):
            names.add(cleaned_name)
            debug_rows.append({"stage": "spaCy" if orgs else "fallback", "raw": raw_before, "cleaned": cleaned_name, "decision": "kept"})
        else:
            debug_rows.append({"stage": "filter", "raw": raw_before, "cleaned": cleaned_name, "decision": "rejected"})

        # Clean up name
        name = re.sub(r"[^A-Za-z0-9&\-\s\.]", "", name)
        name = re.sub(r"\s+", " ", name).strip()
        if len(name) > 2 and len(name.split()) <= 4:
            names.add(name)

    names = sorted(names)
    print(f"[OK] Parsed {len(names)} potential portfolio companies from {url}")

    # --- Debug summary and table ---
    print("\nNLP DEBUG TABLE")
    print(f"{'Stage':<10} | {'Raw Extract':<40} | {'Cleaned':<25} | {'Decision'}")
    print("-" * 100)
    for row in debug_rows[:20]:  # limit to first 20 entries for readability
        print(f"{row['stage']:<10} | {row['raw'][:40]:<40} | {row['cleaned']:<25} | {row['decision']}")
    print("-" * 100)
    print(f"[DEBUG SUMMARY] spaCy detections: {sum(1 for r in debug_rows if r['stage']=='spaCy')}, "
          f"fallbacks: {sum(1 for r in debug_rows if r['stage']=='fallback')}, "
          f"rejected/skipped: {sum(1 for r in debug_rows if r['decision']!='kept')}, "
          f"kept: {len(names)}")
    return names