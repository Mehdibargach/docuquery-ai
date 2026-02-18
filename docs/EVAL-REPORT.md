# Eval Report — DocuQuery AI

> From The Builder PM Method — EVALUATE phase

**Project:** DocuQuery AI
**Date:** 2026-02-18
**Evaluator:** Mehdi Bargach
**Build Version:** [commit hash — fill after commit]
**Golden Dataset Size:** 12 questions (+3 regression)

---

## Eval Gate Decision

**~~NO-GO~~ → CONDITIONAL GO** (after micro-loop BUILD)

- 1st eval: NO-GO — G2 BLOCKING fail (factual 75%, seuil 100%)
- Micro-loop: TOP_K 10→15 (1 line fix in store.py)
- 2nd eval: G2 = 4/4 = 100% → BLOCKING PASS. Zero regressions (E1, E2, E4 unchanged).

### Criteria Levels

> Each criterion is classified as BLOCKING, QUALITY, or SIGNAL.
> - **BLOCKING** : non-negotiable. FAIL = NO-GO, return to BUILD.
> - **QUALITY** : configurable threshold. FAIL = Builder decides (GO or CONDITIONAL GO).
> - **SIGNAL** : monitoring only. FAIL = document for V2, not blocking.

| # | Critere | Level | Seuil | Resultat | Status |
|---|---------|-------|-------|----------|--------|
| G1 | Overall accuracy | QUALITY | >= 80% | 87.5% (10.5/12) | **PASS** |
| G2 | Factual accuracy | **BLOCKING** | 100% | ~~75% (3/4)~~ → 100% (4/4) after micro-loop | **PASS** |
| G3 | Citation accuracy | QUALITY | >= 70% | 75% (9.0/12) | **PASS** |
| G4 | Latency | SIGNAL | < 5s (80%) | 8.5s median (17% < 5s) | **FAIL (signal)** |
| G5 | Zero hallucination | **BLOCKING** | 0 | 0/2 | **PASS** |
| G6 | Consistency | QUALITY | Facts match | Yes (E1=E12) | **PASS** |

### Decision Rules

| Decision | Condition | Action |
|----------|-----------|--------|
| **GO** | 0 BLOCKING fail + 0 QUALITY fail | → SHIP |
| **CONDITIONAL GO** | 0 BLOCKING fail + ≥1 QUALITY/SIGNAL fail | → SHIP with documented conditions |
| **NO-GO** | ≥1 BLOCKING fail | → Micro-loop BUILD (mandatory) |

**1st eval : 1 BLOCKING fail (G2) → NO-GO → micro-loop BUILD**
**2nd eval : 0 BLOCKING fail + 1 SIGNAL fail (G4) → CONDITIONAL GO**

---

## Test Files

| Fichier | Path | Utilisé pour |
|---------|------|-------------|
| NovaPay PRD (PDF, 59 pages) | `tests/test_sample.pdf` | R1, E1-E12 |
| Builder PM Method (TXT) | `tests/test_doc.txt` | R2 |
| Feature Satisfaction (CSV) | `tests/test_sample.csv` | R3 |

---

## Regression Check (DOR)

| # | Format | Question | Expected | Result | Status |
|---|--------|----------|----------|--------|--------|
| R1 | PDF | What is the total development budget? | $18.5 million | CORRECT | PASS |
| R2 | TXT | What are the four phases? | FRAME, BUILD, EVALUATE, SHIP | CORRECT | PASS |
| R3 | CSV | Which feature has the highest satisfaction score? | Advanced Analytics (4.9) | CORRECT | PASS |

**All PASS → proceed. Any FAIL → return to BUILD.**

---

## Golden Dataset

> Upload `tests/test_sample.pdf` une seule fois, puis pose les 12 questions dans l'ordre.

| # | Type | Question (copier-coller dans Streamlit) | Expected Answer | Source Location |
|---|------|----------------------------------------|-----------------|-----------------|
| E1 | Factual | What is the customer acquisition cost at 200 customers? | $3,600 | Page 22 (Section 5.5 Marketing Budget) |
| E2 | Factual | What security certifications are planned? | PCI DSS v4.0 Level 1 and SOC 2 Type II | Pages 14, 43 (Sections 3.6, H) |
| E3 | Factual | What is the target number of transactions per second at launch? | 10,000 TPS | Page 13 (Section 3.5 REQ-NFR-003) |
| E4 | Factual | What is the total annual compensation for the Phase 1 team? | $5,760,000 | Page 25 (Section 6.2 Team Structure) |
| E5 | Multi-hop | Compare the regulatory requirements for EU (Phase 3) vs US (Phase 1) markets | Synthesizes both: EU = GDPR (Page 43), US = PCI, NACHA, state licenses (Pages 14, 31). Multiple citations. | Pages 14, 31, 43 |
| E6 | Multi-hop | What are the three go-to-market phases and their respective success metrics? | 3 phases with KPIs associes | Pages 21, 23 |
| E7 | Multi-hop | How does the pricing model differ across the three plans (Standard, Growth, Enterprise)? | Cross-reference des 3 tiers avec details | Page 21 + details scattered |
| E8 | Synthesis | Summarize NovaPay's competitive advantages in 3-4 points | 3-4 points inferes (pas de section "advantages" dans le doc) | Pages 4, 9, 21, 36-37 |
| E9 | Synthesis | What are the biggest risks for NovaPay and how are they mitigated? | Liste structuree de risques + mitigations | Pages 28-30 (Section 7) |
| E10 | Adversarial | What was NovaPay's revenue in Q4 2025? | **REFUSAL** : "I don't have enough information" (doc = PRD, pas de financials reels) | N/A |
| E11 | Adversarial | Who is the CEO and what is their background? | Nom = Michael Torres (Page 35). Background = **REFUSAL** (pas dans le doc). | Page 35 (approval only) |
| E12 | Consistency | What is the customer acquisition cost at 200 customers? | Meme reponse que E1 ($3,600). Les FAITS doivent etre identiques, le wording peut varier. | Same as E1 |

**Gates critiques :**
- **G2** : E1-E4 doivent etre 100% CORRECT (sinon le RAG est casse)
- **G5** : E10-E11 = 0 hallucination (sinon la confiance est perdue)
- **G6** : E12 = memes faits que E1 (sinon le systeme est inconsistant)

---

## Golden Dataset Results

| # | Type | Question | Expected | Actual | Answer | Citation | Latency | Pattern |
|---|------|----------|----------|--------|--------|----------|---------|---------|
| E1 | Factual | CAC at 200 customers? | $3,600 | $3,600 + LTV:CAC 8.7:1 context | CORRECT (1.0) | EXACT (1.0) — Page 22, P1 | 4.9s | — |
| E2 | Factual | Security certifications? | PCI DSS v4.0 L1 + SOC 2 Type II | PCI DSS v4.0 L1 + SOC 2 Type II + details couts/timeline | CORRECT (1.0) | EXACT (1.0) — Pages 13-14, 40-43 | 10.3s | — |
| E3 | Factual | TPS at launch? | 10,000 TPS | 1,000 TPS (load test Stage 2). Mentionne 10,000 TPS en secondaire. | PARTIAL (0.5) | APPROX (0.5) — Page 45, 16 (attendu: Page 13) | 6.2s | Retrieval Miss |
| E4 | Factual | Total annual comp Phase 1? | $5,760,000 | $5,760,000 + avg $320K/person + equity details | CORRECT (1.0) | EXACT (1.0) — Page 25, P1 | 5.8s | — |
| E5 | Multi-hop | EU vs US regulatory? | Synthesis EU + US | US detaille (PCI, NACHA, CCPA, SOX, licenses). EU = "GDPR readiness" seulement. | PARTIAL (0.5) | APPROX (0.5) — Pages 10, 14, 30 (manque Page 43 EU) | 91.8s | Partial Retrieval |
| E6 | Multi-hop | GTM phases + metrics? | 3 phases with KPIs | 3 stages + KPIs + broader Phase 1 metrics | CORRECT (1.0) | APPROX (0.5) — Page 21, 22 (attendu: 21, 23) | 13.2s | — |
| E7 | Multi-hop | Pricing across plans? | 3 tiers detailed | 3 tiers complets (fees, features, customer %) | CORRECT (1.0) | APPROX (0.5) — Page 53 (attendu: Page 21+) | 26.2s | — |
| E8 | Synthesis | Competitive advantages? | 3-4 inferred points | 4 points structures (analytics, dunning, onboarding, migration) | CORRECT (1.0) | APPROX (0.5) — Pages 5-7, 35-39 | 9.7s | — |
| E9 | Synthesis | Biggest risks + mitigation? | Structured risk list | 4 categories (legal, business model, migration, success criteria) + mitigations | CORRECT (1.0) | APPROX (0.5) — Pages 1, 38, 40, 58 | 13.2s | — |
| E10 | Adversarial | Q4 2025 revenue? | Refusal | Refus explicite : "PRD, not actual historical revenue data" | CORRECT (1.0) | N/A (refusal) (1.0) | 5.1s | — |
| E11 | Adversarial | CEO background? | Name yes, background refusal | Michael Torres (Page 35) + refus background | CORRECT (1.0) | EXACT (1.0) — Page 35, P1 | 3.6s | — |
| E12 | Consistency | Re-ask E1 (CAC) | Same as E1 | $3,600 + LTV:CAC 8.7:1 + $720K budget | CORRECT (1.0) | EXACT (1.0) — Pages 22-24 | 7.2s | — |

---

## Scores by Question Type

| Type | Count | Avg Answer Score | Avg Citation Score | Notes |
|------|-------|------------------|--------------------|-------|
| Factual | 4 | 0.875 (3C + 1P) | 0.875 | E3 PARTIAL — mauvaise priorisation du fait |
| Multi-hop | 3 | 0.833 (2C + 1P) | 0.5 | Citations approximatives (bonnes zones, pas les pages exactes) |
| Synthesis | 2 | 1.0 (2C) | 0.5 | Reponses excellentes, citations dispersees |
| Adversarial | 2 | 1.0 (2C) | 1.0 | Zero hallucination, refus propres |
| Consistency | 1 | 1.0 (1C) | 1.0 | Faits identiques E1=E12 |

---

## Failure Analysis

| # | Question | Pattern | Root Cause | Severity | Recommended Fix |
|---|----------|---------|-----------|----------|----------------|
| E3 | TPS at launch? | **Retrieval Miss** | Le chunk Page 13 (REQ-NFR-003 = 10,000 TPS) n'est pas priorise. Le chunk Page 45 (load testing = 1,000 TPS) est plus proche semantiquement de "at launch". Le systeme donne le bon chiffre en secondaire mais pas en reponse principale. | MEDIUM | Pas de fix code — la question est ambigue. Le systeme a trouve l'info. |
| E5 | EU vs US regulatory? | **Partial Retrieval** | L'info EU detaillee (GDPR, SCCs, budget compliance) est sur Page 43 (Appendix H). Ce chunk n'est pas dans le top 10. Le systeme ne trouve que la mention "GDPR readiness" sur Page 14. Info US complete. | MEDIUM | Augmenter TOP_K (10→15) ou ameliorer overlap pour capturer Appendix H |
| E2, E4, E7 | Montants en $ | **Rendering Bug** | Streamlit interprete $X comme LaTeX (ex: "$175,000,withannual..." au lieu de "$175,000, with annual..."). Pas un probleme RAG. | LOW | Echapper les $ dans la reponse ou desactiver LaTeX dans st.markdown |
| ALL | Latency > 5s | **API Latency** | 10/12 questions > 5s. Median 8.5s. Outlier E5 a 91.8s (probable retry API). Cause = temps de generation Claude Sonnet, pas le pipeline RAG (embed + search < 1s). | HIGH (gate) | Hors controle direct. Options : (1) accepter le seuil, (2) reduire max_tokens, (3) passer a Haiku pour factual |

---

## Recommendations

### CONDITIONAL GO — 0 BLOCKING fail + 1 SIGNAL fail (G4)

**Micro-loop BUILD (completed)**
- **Problem :** E3 answered 1,000 TPS (load test Stage 2) instead of 10,000 TPS (NFR Page 13)
- **Root cause :** Retrieval Miss — Page 45 chunk (load testing) was semantically closer to "at launch" than Page 13 chunk (NFR requirement). TOP_K=10 didn't retrieve the right chunk.
- **Fix :** TOP_K 10→15 in `store.py` (1 line change)
- **Result :** E3 now answers 10,000 TPS with citations Pages 13-14 and 49-50. Zero regressions on E1, E2, E4.

**G4 (Latency — SIGNAL) → Documented, not blocking**
- La latency est dominee par le temps de generation Claude Sonnet (pas le pipeline RAG)
- Le RAG pipeline (embed + cosine search) prend < 1s. C'est l'API LLM qui prend 3-90s
- Classe SIGNAL car c'est une dependance externe (ref: Google SRE Error Budget — causes externes = optional, pas mandatory)

**Conditions for SHIP :**
1. Latency documentee comme limitation connue (dependance Claude API)
2. Bug rendu LaTeX ($) dans Streamlit a fixer en Scope 3 (UI Lovable)

### Observations pour V2 (post-SHIP)
- Router factual → Haiku, synthesis → Sonnet pour optimiser latency
- Few-shot examples dans le prompt pour ameliorer la priorisation des faits
- Fix bug rendu LaTeX ($) dans Streamlit
- TOP_K=15 a resolu E3 mais pourrait aussi ameliorer E5 (EU retrieval) — a re-tester
