"""
Portfolio/companies name extraction from VC (or similar) websites.

Notes:
- Uses requests-html (optional JS rendering) + BeautifulSoup parsing.
- Applies multiple passes (JSON-LD, outbound links, section headings, optional spaCy ORG NER)
  plus lightweight heuristics to reduce noisy matches.
- This module is intended for user-provided, publicly accessible pages. Ensure you comply with
  the target site's Terms of Service and applicable data licenses.
"""


from urllib.parse import urljoin
from requests_html import HTMLSession
from bs4 import BeautifulSoup

def _fetch_html(url: str, render_js: bool = False) -> str | None:
    """Fetch HTML; optionally render JS so widget-based pages populate."""
    try:
        # Some environments have issues with the default headless flag; adjust if needed.
        import pyppeteer
        if "--headless" in pyppeteer.launcher.DEFAULT_ARGS:
            pyppeteer.launcher.DEFAULT_ARGS.remove("--headless")

        # Optional: allow callers to set PYPPETEER_EXECUTABLE_PATH externally if needed.
        # Do not hardcode machine-specific paths in public code.
        import os
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
    """Fetch portfolio or investment company names from a VC website."""
    html = _fetch_html(url, render_js=render_js)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    # -------------------------
    # Smart extraction pipeline
    # -------------------------
    from urllib.parse import urlparse

    def looks_like_company(s: str) -> bool:
        s = s.strip()
        if not s or len(s) > 50:
            return False
        # reject sentences / marketing copy
        if s.endswith(".") or "  " in s or any(p in s for p in ["\n", "…", "—"]):
            return False
        words = s.split()
        if not (1 <= len(words) <= 5):
            return False
        # must have at least one capitalized token
        caps = sum(1 for w in words if w and w[0].isalpha() and w[0].isupper())
        return caps >= max(1, len(words) // 2)

    def domain_to_name(href: str) -> str | None:
        try:
            netloc = urlparse(href).netloc.lower()
            if not netloc:
                return None
            # remove www.
            if netloc.startswith("www."):
                netloc = netloc[4:]
            # take the second-level label
            parts = netloc.split(".")
            if len(parts) >= 2:
                core = parts[-2]
            else:
                core = parts[0]
            core = core.replace("-", " ").strip()
            if not core:
                return None
            name = " ".join(w.capitalize() for w in core.split())
            # simple brand fixups
            if name.endswith(" Ai"):
                name = name[:-3] + "AI"
            return name
        except Exception:
            return None

    base_netloc = urlparse(url).netloc.lower()
    candidates: set[str] = set()

    # 1) JSON-LD pass (organizations often listed here)
    import json
    for script in soup.find_all("script", type=lambda t: t and "ld+json" in t):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue

        def walk(obj):
            if isinstance(obj, dict):
                t = obj.get("@type") or obj.get("type")
                n = obj.get("name")
                if n and isinstance(n, str) and looks_like_company(n):
                    candidates.add(n.strip())
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)

    # 2) External links pass (anchor text or domain → name)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # only consider absolute external links
        if href.startswith("http"):
            netloc = urlparse(href).netloc.lower()
            if netloc and netloc != base_netloc:
                text = a.get_text(strip=True)
                if text and looks_like_company(text):
                    candidates.add(text)
                else:
                    guess = domain_to_name(href)
                    if guess and looks_like_company(guess):
                        candidates.add(guess)

    # 3) Headings / anchors inside portfolio-like sections (fallback)
    keywords = ["portfolio", "companies", "investments", "our-companies", "startups", "company", "ventures"]
    sections = soup.find_all(
        lambda tag: tag.name in ["div", "section", "ul", "li"]
        and any(k in str(tag.get("class", [])).lower() or k in (tag.get("id") or "").lower() for k in keywords)
    )
    for sec in sections:
        for tag in sec.find_all(["h1", "h2", "h3", "h4", "a"]):
            text = tag.get_text(strip=True)
            if text and looks_like_company(text):
                candidates.add(text)

    # 3.5) Semantic entity extraction using spaCy (ORG detection)
    try:
        import spacy
        nlp = spacy.load("en_core_web_lg")

        # Combine all text sections into a big doc
        all_text = " ".join(tag.get_text(" ", strip=True) for tag in soup.find_all(["div", "section", "p"]))
        doc = nlp(all_text)

        for ent in doc.ents:
            if ent.label_ == "ORG" and len(ent.text) < 60:
                text = ent.text.strip()
                if looks_like_company(text):  # still apply your heuristic
                    candidates.add(text)

        print(f"[spaCy] Added {len([e for e in doc.ents if e.label_ == 'ORG'])} ORG candidates.")
    except Exception as e:
        print(f"[spaCy] Skipped semantic parsing: {e}")


    # 3.6) Context proximity filter (keep names near portfolio-related sections)
    import re
    portfolio_context = re.compile(r"(portfolio|companies|investments|startups|our work|ventures)", re.I)
    text_snippets = soup.get_text(" ", strip=True)
    filtered_candidates = set()

    for name in candidates:
        idx = text_snippets.find(name)
        if idx != -1:
            window = text_snippets[max(0, idx - 80): idx + 80]
            if portfolio_context.search(window):
                filtered_candidates.add(name)

    if filtered_candidates:
        print(f"[Context] Filtered to {len(filtered_candidates)} candidates near relevant sections.")
        candidates = filtered_candidates

    # 3.7) Frequency and pattern-based filtering (precision boost)
    from collections import Counter

    # Token-level frequency analysis
    all_text_lower = soup.get_text(" ", strip=True).lower()
    freq = Counter()

    for name in candidates:
        freq[name] = all_text_lower.count(name.lower())

    # Keep candidates that appear more than once OR are followed by a year (typical portfolio patterns)
    likely_real = set()
    for name in candidates:
        if freq[name] > 1 or re.search(fr"{name}.{{0,30}}(20\d{{2}})", all_text_lower, re.I):
            likely_real.add(name)

    if likely_real:
        print(f"[Frequency] Refined {len(candidates)} -> {len(likely_real)} likely candidates.")
        candidates = likely_real

    # 4) If still empty, try /portfolio/ automatically
    if not candidates and not url.rstrip("/").endswith("portfolio"):
        alt_url = urljoin(url, "portfolio/")
        print(f"[Retry] Retrying with {alt_url}")
        return scrape_portfolio(alt_url, render_js=render_js)

    # Final clean + sort
    # ---------------------------------------
    # Cleanup phase: segment & filter garbage
    # ---------------------------------------
    import re

    def clean_name(raw: str) -> str | None:
        raw = raw.strip()
        if not raw:
            return None

        # Insert spaces between camel-case transitions (e.g. EnergyMicro → Energy Micro)
        raw = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', raw)

        # Normalize double spaces and trim
        raw = re.sub(r'\s+', ' ', raw).strip()

        # Stopword-like suffixes that indicate descriptions, not company names
        context_words = [
            "Solutions", "Technologies", "Technology", "Systems", "Group", "Holdings",
            "Partners", "Ventures", "Capital", "Labs", "Studio", "Foundation",
            "Sustainable", "Global", "International", "Industries", "Company"
        ]

        # Tokenize
        tokens = raw.split()
        if not tokens:
            return None

        # Keep at most two consecutive capitalized tokens before context word
        name_tokens = []
        for t in tokens:
            # stop if we hit a lowercase or context word
            if t in context_words or not t[0].isupper():
                break
            name_tokens.append(t)
            if len(name_tokens) >= 2:
                break

        name = " ".join(name_tokens).strip()
        if len(name) < 2:
            return None

        return name

    candidates = {clean_name(n) for n in candidates if clean_name(n)}
    names = sorted(candidates)
    print(f"[OK] Parsed {len(names)} potential entries from {url}")
    return names