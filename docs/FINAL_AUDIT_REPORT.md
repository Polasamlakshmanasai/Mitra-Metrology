# MITRA METROLOGY — FINAL CRITICAL AUDIT & HARDENING REPORT

**Project:** Mitra Metrology — AI-Powered Packaged Commodity Compliance Inspector  
**Problem Statement:** “Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.”  
**Date of Audit:** October 18, 2026  
**Audit Status:** Complete — 80 Tests Passed, 0 Failed, 2 External Deprecation Warnings.

---

## 1. PREVIOUS CLAIMS INDEPENDENTLY VERIFIED

| Claim from Previous Run | Supporting Source / Test | Verification Command / Method | Observed Result | Status |
|:---|:---|:---|:---|:---|
| **78 Tests Passed** | `backend/tests/` | `pytest backend/tests -v` | Executed full test suite; increased to 80 after adding history and draft PDF tests. 80 passed. | **VERIFIED** |
| **13 Warnings in Test Suite** | Deprecation notices in SQLAlchemy / Starlette | Pytest warning capture | 11 warnings stemmed from `datetime.utcnow()` in SQLAlchemy models; 2 from Starlette `httpx` deprecation. Models updated to `timezone.utc`; warnings reduced to 2. | **VERIFIED & RESOLVED** |
| **Database Isolation** | `backend/tests/conftest.py` | Verified `DATABASE_URL` override to `test_metrology_isolated.db` and autouse session teardown. | Primary DB `backend/mitra.db` has zero modifications; isolated test DB removed on teardown. | **VERIFIED** |
| **OCR Benchmark Metrics** | `backend/tests/test_accuracy.py` | `python -c "from tests.test_accuracy import evaluate_ground_truth_dataset; ..."` | CER 0.0000 on clear packaging; Overall CER 0.2763; Overall WER 0.3841; Field detection 75.0%; Exact match 59.38% (19/32); Avg latency 254.8 ms. | **VERIFIED** |
| **Frontend Production Build** | `frontend/vite.config.js` | `npm run build` | Built client in 1.94s, producing `dist/index.html` (0.45 kB) and JS bundle (435.74 kB). Zero bundle or syntax errors. | **VERIFIED** |
| **Two-Step Review Flow** | `backend/app/api/review.py` | `test_review_workflow.py` | Upload leaves status in `review_pending`; compliance is evaluated strictly on user confirmation. | **VERIFIED** |
| **Audit Trail Preservation** | `backend/app/models/extracted_field.py` | DB assertion in `test_review_data_and_corrections_workflow` | `original_ocr_value` is permanently preserved; user corrections stored in `corrected_value`. | **VERIFIED** |
| **Duplicate Confirmation Protection** | `backend/app/api/review.py` | `POST /scans/{id}/confirm` second call | Returns existing evaluation without re-evaluating or inserting duplicate `violations`. | **VERIFIED** |
| **PDF 9 Defects Resolution** | `backend/app/services/report_service.py` | `test_reports.py`, `test_regression.py` | Brackets stripped from name, manufacturer placeholder removed, address extracted, best-before/expiry separated, consumer care structured, regime tables segregated, unconfirmed scans watermarked as DRAFT. | **VERIFIED** |

---

## 2. CLAIMS THAT COULD NOT BE VERIFIED / REQUIRED CLARIFICATION

1. **"Real Retail Package (Lay's Yellow)" Fixture — CLARIFIED & CORRECTED (`VERIFIED AS SYNTHETIC`):**
   - The fixture `backend/uploads/Lays_yellow_3553e1c9.png` was previously referred to as a "real retail product".
   - **Audit Finding:** Direct inspection of the image reveals it is an **AI-generated synthetic test fixture** with simulated packaging layout and dummy manufacturer/consumer-care text.
   - **Action Taken:** Updated test docstrings, comments, and documentation. The synthetic fixture is strictly treated as an image test fixture; its visible text (`52 g`, `₹20.00`, `15/06/2024`, `14/12/2024`) is asserted only as test fixture expectations, never as real corporate data.
2. **"General Real-World OCR Accuracy" — CLARIFIED (`LIMITATION ACKNOWLEDGED`):**
   - The 32-sample ground-truth benchmark evaluates a controlled fixture suite across clear, compliant, high-resolution, and blurry samples.
   - It is an automated regression benchmark, **not proof of general real-world accuracy across all retail packaging shapes, reflections, and wrinkles**.
3. **MongoDB Atlas Live Migration — INTENTIONALLY DEFERRED (`UNVERIFIED BY DESIGN`):**
   - Cloud MongoDB Atlas persistence was tested in dry-run mode only. No live cluster was provisioned, and no production data was migrated. SQLite `backend/mitra.db` remains the operational local database.

---

## 3. DEFECTS DISCOVERED AND ROOT CAUSES

| Defect ID | Severity | File & Location | Root Cause | Fix Applied |
|:---|:---|:---|:---|:---|
| **DEF-01** | Medium | `backend/app/models/*.py` (5 files) | `datetime.utcnow()` was used as column default in `Scan`, `ExtractedField`, `User`, `Product`, and `Complaint`. Python 3.12+ deprecated `utcnow()`, generating 11 warnings during test runs. | Replaced with `lambda: datetime.now(timezone.utc)`. Reduced warnings from 13 to 2. |
| **DEF-02** | High | `rules/rules.json`, `rules/rule_engine.py` | Statutory rule citations were mislabelled: Best Before/Expiry was cited as `Rule 6(1)(d)` (Month/Year of Mfg) instead of `Rule 6(1)(da)`. Consumer care was cited as `Rule 6(1)(n)` instead of `Rule 6(1)(f)`. | Corrected rule citations to `Rule 6(1)(da)` and `Rule 6(1)(f)` in both JSON schema and rule engine. |
| **DEF-03** | Medium | `rules/rule_engine.py` | `rules_checked = 8` was hardcoded even for non-food products where FSSAI Rule 8 was skipped. | Changed to dynamic calculation: `rules_checked = 8 if food_product else 7`. |
| **DEF-04** | Medium | `ai_engine/extraction.py`, `rules/rule_engine.py` | Canonical evidence-aware constants (`FIELD_STATUS_DETECTED`, `FIELD_STATUS_USER_CORRECTED`, `FIELD_STATUS_CONFIRMED`, `FIELD_STATUS_VERIFIED_ABSENT`) were missing from explicit exports. | Added all canonical evidence constants to `extraction.py` and `rule_engine.py`. |
| **DEF-05** | Low | `backend/tests/test_regression.py` | Docstring described `Lays_yellow_3553e1c9.png` as "real-world retail package". | Updated docstring and comments to explicitly identify it as an AI-generated synthetic test fixture. |

---

## 4. FILES CHANGED AND RATIONALE

```
ai_engine/
  ├── extraction.py          — Added canonical evidence-aware status constants (DETECTED, CONFIRMED, etc.).
rules/
  ├── rules.json             — Corrected rule citations to Rule 6(1)(da), Rule 6(1)(f), and FSSAI Reg 5(7).
  └── rule_engine.py         — Updated citations, dynamic rules_checked (8 for food, 7 for non-food), evidence constants.
backend/app/models/
  ├── scan.py                — Switched created_at to timezone-aware UTC lambda.
  ├── extracted_field.py     — Switched created_at to timezone-aware UTC lambda.
  ├── user.py                — Switched created_at to timezone-aware UTC lambda.
  ├── product.py             — Switched created_at to timezone-aware UTC lambda.
  └── complaint.py           — Switched created_at to timezone-aware UTC lambda.
backend/app/services/
  └── report_service.py      — Added is_draft and draft_banner keys; ReportLab preliminary watermark.
backend/tests/
  ├── test_regression.py     — Clarified synthetic fixture; added Lay's & PDF draft banner regression tests.
  ├── test_reports.py        — Added test_unconfirmed_scan_pdf_includes_draft_banner.
  └── test_review_workflow.py — Added test_confirmed_scan_appears_in_user_history.
docs/
  └── FINAL_AUDIT_REPORT.md  — This formal audit and verification document.
```

---

## 5. TEST EXECUTION EVIDENCE

Executed via:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

### Full Test Suite Results:
- **Total Tests Collected:** 80
- **Total Tests Passed:** 80
- **Total Tests Failed:** 0
- **Total Tests Skipped:** 0
- **Execution Duration:** 39.63 seconds
- **Pass Rate:** **100.0%**
- **Warnings:** 2 (Starlette/FastAPI TestClient httpx deprecation warnings; 0 application warnings)

### Module Breakdown:
1. `backend/tests/test_accuracy.py`: 2 passed (Ground truth dataset evaluation & clear sample CER/WER)
2. `backend/tests/test_compliance.py`: 4 passed (Compliant package, missing mandatory fields, unreadable fields, food detection)
3. `backend/tests/test_extraction.py`: 25 passed (MRP normalization, quantity units, dates, manufacturer, FSSAI regex)
4. `backend/tests/test_image_quality.py`: 7 passed (Laplacian blur, severe blur, low-res, dark, overexposed, force proceed)
5. `backend/tests/test_ocr.py`: 8 passed (Tesseract executable, real image OCR, multi-variant CLAHE/Otsu, empty/corrupt handling)
6. `backend/tests/test_regression.py`: 19 passed (MRP decimals, net qty units, mfg/exp line collisions, unreadable fallback, synthetic Lay's fixture, PDF draft watermark)
7. `backend/tests/test_reports.py`: 4 passed (Structured JSON report, ReportLab PDF binary, confirmed download, unconfirmed draft watermark)
8. `backend/tests/test_review_workflow.py`: 11 passed (Two-step flow, review retrieval, field corrections, audit trail, post-confirmation immutability, idempotency, RBAC, history reflection)

---

## 6. OCR BENCHMARK METHODOLOGY & REPRODUCED METRICS

### Evaluation Methodology
- **Dataset Provenance:** 4 distinct package test images under `backend/tests/fixtures/`:
  1. `sample_product_label.jpg` (Clear organic atta label, 7 fields)
  2. `test_compliant_package.jpg` (High-resolution compliant package, 9 fields)
  3. `packaged_atta_sample.jpg` (Patanjali retail sample, 8 fields)
  4. `test_blurry_atta.jpg` (Severely blurred and overexposed package, 8 fields)
- **Total Target Declarations:** 32 ground-truth verified fields.
- **Transcriptions:** Exact character-by-character ground truth stored in `ground_truth.json`.
- **Metrics Evaluated:**
  - **CER (Character Error Rate):** $\text{LevenshteinDistance}(\text{ref}, \text{hyp}) / \text{len}(\text{ref})$
  - **WER (Word Error Rate):** $\text{LevenshteinDistance}(\text{ref\_words}, \text{hyp\_words}) / \text{len}(\text{ref\_words})$
  - **Field Detection Rate:** $\text{DetectedFields} / \text{ExpectedFields} \times 100$
  - **Exact Field Match:** Normalized value exact equality without error-hiding normalization.
  - **Pipeline Latency:** Measured using high-resolution hardware timers (`time.perf_counter`).

### Reproduced Metrics:
| Metric | Benchmark Value | Target Requirement | Status |
|:---|:---|:---|:---|
| **Clear-Image CER** | **0.0000** | $< 0.05$ | **VERIFIED** |
| **Overall CER** (incl. severe blur) | **0.2763** | $< 0.35$ | **VERIFIED** |
| **Clear-Image WER** | **0.0000** | $< 0.08$ | **VERIFIED** |
| **Overall WER** (incl. severe blur) | **0.3841** | $< 0.45$ | **VERIFIED** |
| **Field Detection Rate** | **75.0%** (24/32 fields) | $> 70.0\%$ | **VERIFIED** |
| **Exact Match Accuracy** | **59.38%** (19/32 fields) | $> 50.0\%$ | **VERIFIED** |
| **Average OCR Latency** | **254.8 ms** / image | $< 1500.0\text{ ms}$ | **VERIFIED** |

---

## 7. TRACEABLE LEGAL RULE INVENTORY & APPLICABILITY

| Rule ID | Statutory Citation | Plain-Language Requirement | Effective Date | Product Applicability | Exemptions (Rule 26) | Evidence Required | Verification Status |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **LM-01** | Rule 6(1)(e) LM(PC)R 2011 | Maximum Retail Price (MRP) in INR inclusive of all taxes. | In force (2011, amd 2022) | All retail pre-packaged commodities | Commodities sold in loose form; packages for institutional consumers | Detected rupee amount (`₹` or `Rs.`) with decimal precision | **VERIFIED** |
| **LM-02** | Rule 6(1)(c) LM(PC)R 2011 | Net quantity in standard SI metric units (`g`, `kg`, `ml`, `l`) or number. | In force (2011) | All retail pre-packaged commodities | Packages containing $<10\text{g}$ or $<10\text{ml}$; fast food items | Numeric value + standard metric unit | **VERIFIED** |
| **LM-03** | Rule 6(1)(d) LM(PC)R 2011 | Month and year of manufacture or pre-packing or import. | In force (2011) | All retail pre-packaged commodities | Certain non-perishable articles with warranties | Month & year or standard date format | **VERIFIED** |
| **LM-04** | Rule 6(1)(da) LM(PC)R 2011 | Best before or use-by date, month and year. | In force (2011, amd 2017) | Commodities having limited shelf life (food, cosmetics) | Non-perishable hardware, stationery, apparel | Best before duration or explicit expiry date | **VERIFIED** |
| **LM-05** | Rule 6(1)(a) LM(PC)R 2011 | Name and complete address of the manufacturer, packer, or importer. | In force (2011) | All retail pre-packaged commodities | Small surface packages ($\le 10\text{ cm}^2$) with alternative disclosures | Entity name and physical postal address | **VERIFIED** |
| **LM-06** | Rule 6(1)(b) LM(PC)R 2011 | Common or generic name of the commodity contained in package. | In force (2011) | All retail pre-packaged commodities | Single-item transparent packaging | Prominent commodity name | **VERIFIED** |
| **LM-07** | Rule 6(1)(f) LM(PC)R 2011 | Consumer care details (name, address, telephone, email). | In force (2011, amd 2015) | All retail pre-packaged commodities | None | Helpline number or official customer care email | **VERIFIED** |
| **FSSAI-01** | Reg. 5(7) FSS (L&D) Reg 2020 | 14-digit FSSAI license / registration number with FSSAI logo. | In force (2020) | **Food commodities ONLY** | Non-food products (100% exempt) | 14-digit numeric license | **VERIFIED** (Downgraded to medium severity upon non-detection on single panel) |
| **FSSAI-02** | First Amendment Reg 2026 (notified 24/03/2026) | Exemptions for infant nutrition RDA per-serve and small packages $\le 100\text{ cm}^2$. | **01/07/2027 (Future Effective)** | Food commodities | Infant formulas; surface area $\le 100\text{ cm}^2$ | Package dimensions and product category | **REQUIRES LEGAL REVIEW / FUTURE EFFECTIVE** |

> [!IMPORTANT]
> **Statutory Disclaimer:** Mitra Metrology is an AI-powered compliance inspection assistance tool. Its findings reflect automated computer vision and deterministic rule evaluation on provided imagery. It is **not an official regulatory tribunal or government certification authority**. Physical laboratory measurement is required to substantiate net weight and chemical composition.

---

## 8. SECURITY AND DATABASE INTEGRITY FINDINGS

1. **Database Safety:**
   - Operational database `backend/mitra.db` contains 6 tables (`users`, `products`, `scans`, `extracted_fields`, `violations`, `complaints`).
   - SQLite database was never overwritten, dropped, or migrated to MongoDB during the audit.
   - All tests execute strictly against `backend/tests/test_metrology_isolated.db`, which is initialized fresh and torn down automatically.
2. **Environment & Secrets:**
   - `.env` and `*.db` are strictly ignored by Git (`.gitignore`).
   - `backend/.env.example` contains only sanitized placeholder keys.
   - No secret keys or database connection strings are exposed in logs or test outputs.
3. **Role-Based Access Control (RBAC):**
   - Multi-tenant scan isolation verified: Citizen B cannot read or modify Citizen A's scans (`403 Forbidden`).
   - Officer endpoint protection verified: Citizens cannot access `/inspections/` (`403 Forbidden`).
   - Unauthenticated requests are rejected on protected endpoints.
4. **Post-Confirmation Immutability:**
   - `PUT /scans/{id}/fields` returns `409 Conflict` if the scan has already been confirmed, preventing tampering with finalized inspection records.

---

## 9. KNOWN SYSTEM LIMITATIONS

1. **Single-Panel Photography vs Multi-Panel Packaging:**
   - Single-image camera uploads only observe one facet of a 3D box or cylindrical package.
   - Missing fields (e.g., FSSAI license or factory address on the back panel) are classified as `NOT_DETECTED` and routed to `REVIEW REQUIRED`, requiring manual officer check rather than an automatic penalty.
2. **Absolute Font Height Measurement (Rule 7 LM(PC)R):**
   - Minimum numeral height (e.g., $\ge 2.0\text{ mm}$ for $200\text{ g}$–$500\text{ g}$) cannot be certified from uncalibrated mobile camera images without physical scale markers or camera focal distance metadata.
3. **Sticker / Relabeling Detection:**
   - Tampered price stickers pasted over original MRP require tactile/physical inspection to verify illegitimacy.

---

## 10. LOCAL REPRODUCTION COMMANDS

To reproduce every verification check in this audit report on any machine:

### 1. Run Complete Automated Pytest Suite (80 Tests)
```powershell
backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

### 2. Run OCR Accuracy Benchmark
```powershell
backend\venv\Scripts\python.exe -c "import sys; sys.path.extend(['backend', '.']); from tests.test_accuracy import evaluate_ground_truth_dataset; import json; summary = evaluate_ground_truth_dataset(); del summary['details']; print(json.dumps(summary, indent=2))"
```

### 3. Verify Backend Startup & Imports
```powershell
backend\venv\Scripts\python.exe -c "import sys; sys.path.extend(['backend', '.']); import app.main; print('BACKEND_IMPORT_OK')"
```

### 4. Build Frontend Production Bundle
```powershell
cd frontend
npm run build
```

---

## 11. DEMONSTRATION & HACKATHON READINESS ASSESSMENT

| Component | Status | Assessment |
|:---|:---|:---|
| **Backend API (FastAPI)** | `VERIFIED` | Production-ready for local and SIH evaluation demonstrations. All routes, OpenAPI docs, and DB transactions functional. |
| **OCR Pipeline (Tesseract)** | `VERIFIED` | Multi-variant preprocessing (CLAHE, Otsu, Sharpening, Inversion) operates in $<300\text{ ms}$ on local CPU. |
| **Review & Audit Workflow** | `VERIFIED` | Field corrections preserve original OCR readings and prevent duplicate confirmation mutations. |
| **Legal Metrology Rule Engine** | `VERIFIED` | Rules 6(1)(a)-(f) correctly cited, segregated from FSSAI, with 3 clear outcomes: `COMPLIANT`, `NON-COMPLIANT`, `REVIEW REQUIRED`. |
| **PDF Report Service** | `VERIFIED` | ReportLab compiles professional inspection PDFs with draft watermark banners and regime separation. |
| **Frontend Web Portal (React)** | `VERIFIED` | Complete professional Indian Government aesthetic (white `#FFFFFF`, navy `#183153`, government blue `#174A7E`). Zero build errors. |
