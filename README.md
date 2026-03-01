# VC Diligence Automation Toolkit

AI-assisted portfolio intelligence for structured startup screening.

---

## Why This Exists

Early-stage diligence is noisy.

Portfolio pages are inconsistent.  
Company data is unstructured.  
Competitive overlap is often discovered manually.

This toolkit reduces that friction by transforming raw portfolio pages into structured, comparable outputs in minutes.

---

## What It Does

Given a publicly accessible portfolio page, the system:

1. Extracts company names using HTML parsing and optional NLP  
2. Normalizes organization entities  
3. Compares results against a configurable competitor set  
4. Outputs structured conflict summaries  

The result: faster signal extraction during venture screening workflows.

---

## Core Capabilities

### Portfolio Extraction
Parses static and JavaScript-rendered portfolio pages to extract structured company names.

### Entity Recognition
Uses spaCy’s `en_core_web_lg` model to detect and normalize organization entities from noisy text.

### Competitor Matching Engine
Compares extracted companies against user-defined direct and adjacent competitor lists.

### Modular Architecture
Clear separation between ingestion, parsing, and comparison layers for extensibility.

---

## Example Workflow

**Input:**  
A venture firm’s public portfolio URL  

**Output:**  
- Extracted company list  
- Direct overlaps  
- Adjacent overlaps  
- Clean classification summary  

This output can be exported or integrated into downstream memo workflows.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/vc-diligence-automation-toolkit.git
cd vc-diligence-automation-toolkit
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 3. Run the CLI

```bash
python -m src.main
```

Provide a publicly accessible portfolio URL when prompted.

---

## Architecture

```
src/
  main.py                # CLI entry point
  scraper.py             # Portfolio extraction engine
  scraper_spacy_only.py  # NLP-focused extraction variant
  comparer.py            # Competitor matching engine
data/
  sample_competitors.json
```

---

## Design Philosophy

- Automate repetitive research tasks  
- Keep inputs configurable  
- Avoid vendor lock-in  
- Maintain modular extensibility  
- Operate only on publicly accessible data  

This project demonstrates how lightweight AI + rule-based systems can structure venture workflows without requiring proprietary databases.

---

## Future Extensions

- Structured diligence memo generation  
- Risk flag extraction  
- Configurable scoring rubrics  
- CSV / PDF ingestion  
- Local web interface demo  

---

## Disclaimer

This toolkit operates on user-provided, publicly accessible data.  
Users are responsible for complying with applicable Terms of Service and licensing agreements.

This project is an independent technical demonstration and is not affiliated with any investment firm or data provider.

---

## Author

Abhishek Sriram  
GitHub: https://github.com/Milkshake10401