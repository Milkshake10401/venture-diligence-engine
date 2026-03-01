# VC Diligence Automation Toolkit — Roadmap

## Why This Exists

This project aims to create an open, transparent framework for analyzing venture portfolios using publicly accessible data.

Instead of relying solely on closed databases, this toolkit demonstrates how structured extraction, lightweight NLP, and rule-based matching can surface portfolio overlap and competitive conflicts in a reproducible way.

The long-term goal is to standardize early-stage diligence workflows through automation and modular design.

---

## Current State (MVP)

### What It Does Today

- Scrapes publicly accessible VC portfolio pages.
- Extracts likely company names using a card-aware + NLP approach.
- Displays detected companies in a structured table.
- Flags overlaps against a configurable competitor list.

---

## Key Outputs

1. Terminal table of detected company names with overlap flags.
2. Optional file output (CSV/JSON).
3. Debug mode that shows how names were selected or rejected.

---

## How It Works (High-Level)

1. Fetch HTML from a portfolio page.
2. Detect repeating “card” or “grid” structures.
3. Use spaCy to detect organization entities.
4. Fallback to capitalized phrase heuristics if NLP fails.
5. Clean and filter noisy tokens.
6. Compare extracted names against a user-defined competitor dataset.

In simple terms:
“Extract structured company names from visual card layouts, normalize them, and compare against a reference list.”

---

## Current Modules

- `src/scraper_spacy_only.py`  
  Card-aware scraper using spaCy per content block.

- `src/scraper.py`  
  Broader heuristic-based scraper (fallback logic).

- `src/main.py`  
  CLI entry point.

- `data/sample_competitors.json`  
  Example competitor dataset (user-configurable).

---

## Terminology

- **Card**: A repeating content block containing a company tile.
- **spaCy**: NLP library used for detecting organization entities.
- **Fallback**: Rule-based extraction when NLP fails.
- **Conflict**: A match against a reference competitor dataset.

---

## Development Phases

### Phase 1 — Web Scraper Stability
Goal: Improve reliability across common portfolio page structures.

Tasks:
- [ ] Keep card-aware + spaCy as default extractor.
- [ ] Add optional CSS selector hints for edge-case sites.
- [ ] Add manual normalization map for known name variants.
- [ ] Add `--debug` and `--no-debug` flags.
- [ ] Add optional CSV export to `output/`.

Success Criteria:
- Several common VC portfolio sites return mostly valid company names.
- Debug mode clearly explains inclusion/exclusion logic.

---

### Phase 2 — PDF Ingestion
Goal: Extract portfolio companies from downloaded fund PDFs.

Tasks:
- [ ] Build `pdf_ingest.py`.
- [ ] Implement text extraction (`pypdf` or `pdfplumber`).
- [ ] Apply same NLP + fallback logic as web scraper.
- [ ] Output standardized CSV format.

Success Criteria:
- PDF ingestion produces reasonably accurate company lists.
- False positives are minimized through rule-based filtering.

---

### Phase 3 — Conflict Engine v1
Goal: Improve overlap detection accuracy.

Tasks:
- [ ] Implement exact case-insensitive matching.
- [ ] Add fuzzy matching using `RapidFuzz`.
- [ ] Allow configurable similarity threshold.
- [ ] Output structured conflict reports.

Success Criteria:
- Detects direct overlaps reliably.
- Handles minor name variations (e.g., spacing, punctuation).

---

### Phase 4 — UX Improvements
Goal: Improve readability and usability.

Tasks:
- [ ] Add clean summary header (e.g., “Scraped: 56 | Conflicts: 2”).
- [ ] Hide debug output unless explicitly enabled.
- [ ] Add `--save` flag for CSV/JSON export.

Success Criteria:
- Output is readable at a glance.
- Non-technical users can run the tool without confusion.

---

## How to Run

```bash
source .venv/bin/activate
python -m src.main
```

Provide a publicly accessible portfolio URL when prompted.

---

## Future Directions (Optional Extensions)

- Structured diligence memo generation.
- Configurable scoring rubric.
- Local web interface demo.
- Batch processing mode.
- Plugin architecture for new data sources.

---

This roadmap reflects a modular, extensible approach to automating portfolio intelligence using publicly accessible data.